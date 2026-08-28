"""Preflight audit: unmatched SKUs + missing logo/apparel dry-run."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_cl_lookup.enrich_cl_lookup import (
    DEFAULT_CL_CSV,
    apply_cl_enrichment,
    build_cl_lookup,
    load_cl_database,
)
from scripts.pipeline_cl_lookup.fetch_input_csv import fetch_input_csv
from scripts.pipeline_fill_prime_images.service import fill_packing_columns_df
from scripts.pipeline_runtime.order_number_csv import coerce_order_number_columns
from scripts.pipeline_split_by_process_item.duplicate_order_suffixes import (
    assign_merge_order_number_suffixes,
)
from scripts.pipeline_split_by_process_item.grouping_quantity import (
    _expand_df_by_quantity,
)
from scripts.pipeline_split_by_process_item.merge_group_mask import (
    expand_issue_mask_to_merge_groups,
)
from scripts.pipeline_split_position.io_process_info import (
    load_logo_ids_to_positions,
    load_multiple_positions,
    load_process_info_pq,
)
from scripts.pipeline_split_position.service import transform_step4_df
from scripts.pipeline_split_position.transform_position_codes import build_position_lookup

from .config import NO_ISSUES, NO_UNMATCHED
from .image_dry_run import build_preflight_stem_maps, flag_missing_images

import sys

_WAREHOUSE = Path(__file__).resolve().parent.parent.parent.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared.demo_images import demo_image_lookup, effective_image_dirs  # noqa: E402

# Parallel CSV prep — workbook cache is read-only shared state.
_CSV_MAX_WORKERS = 4


@dataclass
class PreflightResult:
    path: Path
    unmatched_count: int
    missing_logo_count: int
    missing_apparel_count: int
    issue_row_count: int


@dataclass(frozen=True)
class _WorkbookCache:
    cl_lookup: dict
    logo_id_to_position: Optional[dict[str, str]]
    default_code: str
    position_to_code: dict[str, str]
    multiple_positions_df: Optional[pd.DataFrame]


def _is_blank(val) -> bool:
    """True if value is missing, empty string, or whitespace-only."""
    if pd.isna(val):
        return True
    if not isinstance(val, str):
        val = str(val)
    return val.strip() == ""


def _yes_no(flag: bool) -> str:
    return "Yes" if flag else "No"


def _fmt_secs(seconds: float) -> str:
    if seconds < 10:
        return f"{seconds:.1f}s"
    return f"{seconds:.0f}s"


def _load_workbook_cache(workbook_path: Path, cl_csv_path: Path | None = None) -> _WorkbookCache:
    """Load CL CSV + Step-4 workbook sheets once."""
    cl_df = load_cl_database(cl_csv_path)
    cl_lookup = build_cl_lookup(cl_df)
    logo_id_to_position = load_logo_ids_to_positions(workbook_path)
    pq_df = load_process_info_pq(workbook_path)
    default_code, position_to_code = build_position_lookup(pq_df)
    if default_code == "":
        raise ValueError(
            "Workbook Process Info sheet must define a Default Position code."
        )
    multiple_positions_df = load_multiple_positions(workbook_path)
    return _WorkbookCache(
        cl_lookup=cl_lookup,
        logo_id_to_position=logo_id_to_position,
        default_code=default_code,
        position_to_code=position_to_code,
        multiple_positions_df=multiple_positions_df,
    )


def _process_one_csv(
    csv_path: Path,
    cache: _WorkbookCache,
) -> Optional[pd.DataFrame]:
    """Fetch → enrich → fill → step 4 in memory; return recombined rows or None."""
    rows = fetch_input_csv(csv_path, warn_missing_columns=False)
    if not rows:
        return None

    df = coerce_order_number_columns(pd.DataFrame(rows))
    enriched = apply_cl_enrichment(df, cache.cl_lookup, log=None)
    if "Gender Apparel" not in enriched.columns:
        raise ValueError("Enriched data missing 'Gender Apparel' column.")

    filled = fill_packing_columns_df(enriched, log=None)
    matched, unmatched = transform_step4_df(
        filled,
        logo_id_to_position=cache.logo_id_to_position,
        default_code=cache.default_code,
        position_to_code=cache.position_to_code,
        multiple_positions_df=cache.multiple_positions_df,
        log=None,
    )

    parts: list[pd.DataFrame] = []
    if matched is not None and not matched.empty:
        parts.append(matched)
    if unmatched is not None and not unmatched.empty:
        parts.append(unmatched)
    if not parts:
        return None
    combined = pd.concat(parts, ignore_index=True, sort=False)
    # Match Step 6: expand Item Quantity to one row per unit, then assign
    # base / base-1 / base-2 Logo/Design stems so custom file lookup aligns.
    combined = _expand_df_by_quantity(combined)
    combined = assign_merge_order_number_suffixes(combined)
    # Input CSV stem is the process batch the order came from (e.g. 8050.csv → 8050).
    combined["Process Number"] = csv_path.stem
    cols = ["Process Number"] + [c for c in combined.columns if c != "Process Number"]
    return combined[cols]


def run_preflight_audit(
    input_csv_paths: list[Path],
    workbook_path: Path,
    output_dir: Path,
    log_callback: Callable[[str], None],
    *,
    cl_csv_path: Optional[Path] = None,
    apparel_dir: Optional[Path] = None,
    logo_normal_dir: Optional[Path] = None,
    logo_custom_single_dir: Optional[Path] = None,
    logo_custom_double_dir: Optional[Path] = None,
    use_demo_images: bool = False,
) -> PreflightResult | None | object:
    """
    Process each input CSV through steps 2–4, flag unmatched SKU + missing logo/apparel,
    write Preflight Issues CSV for rows with at least one Yes.
    Returns PreflightResult, NO_ISSUES, or None on error.

    Workbook = process/position sheets. Custom Label enrich uses ``cl_csv_path``
    (default live Custom_Label_Database.csv), not the Workbook CL sheet.
    """
    t0 = time.perf_counter()

    if not input_csv_paths:
        log_callback("Error: No input files selected.")
        return None
    if not workbook_path.is_file():
        log_callback(f"Error: Workbook not found: {workbook_path}")
        return None
    resolved_cl = Path(cl_csv_path) if cl_csv_path is not None else Path(DEFAULT_CL_CSV)
    if not resolved_cl.is_file():
        log_callback(f"Error: Custom Label Database CSV not found: {resolved_cl}")
        return None

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_files = len(input_csv_paths)
    log_callback(f"Preflight started — {n_files} file(s)")
    log_callback("")

    # --- Stage 1: image index ---
    log_callback("1/4  Indexing image folders…")
    t_img = time.perf_counter()
    use_demo = bool(use_demo_images)
    (
        resolved_apparel,
        resolved_normal,
        resolved_custom_single,
        resolved_custom_double,
    ) = effective_image_dirs(
        use_demo,
        apparel_dir,
        logo_normal_dir,
        logo_custom_single_dir,
        logo_custom_double_dir,
    )
    if use_demo:
        log_callback("      Demo images enabled (Demo Images Database/)")
    with demo_image_lookup(use_demo):
        apparel_map, logo_normal_map, logo_custom_map, apparel_path, logo_normal_path, logo_custom_single_path, logo_custom_double_path = (
            build_preflight_stem_maps(
                resolved_apparel,
                resolved_normal,
                resolved_custom_single,
                resolved_custom_double,
            )
        )
    image_checks_enabled = (
        use_demo
        or apparel_map is not None
        or logo_normal_map is not None
        or logo_custom_map is not None
        or apparel_path is not None
        or logo_normal_path is not None
        or logo_custom_single_path is not None
        or logo_custom_double_path is not None
    )
    if not image_checks_enabled:
        log_callback(
            f"      Skipped (no folders set) — Unmatched SKU only  [{_fmt_secs(time.perf_counter() - t_img)}]"
        )
    else:
        la = len(apparel_map) if apparel_map else 0
        ln = len(logo_normal_map) if logo_normal_map else 0
        lc = len(logo_custom_map) if logo_custom_map else 0
        log_callback(
            f"      Done — apparel {la:,} · normal logos {ln:,} · custom logos {lc:,}"
            f"  [{_fmt_secs(time.perf_counter() - t_img)}]"
        )

    # --- Stage 2: CL CSV + workbook process sheets ---
    log_callback("2/4  Loading CL CSV + workbook lookups…")
    log_callback(f"      CL CSV: {resolved_cl.resolve()}")
    t_wb = time.perf_counter()
    try:
        cache = _load_workbook_cache(workbook_path, cl_csv_path=resolved_cl)
    except Exception as e:
        log_callback(f"Error loading CL CSV / workbook: {e}")
        return None
    log_callback(
        f"      Done — CL labels {len(cache.cl_lookup):,}"
        f"  [{_fmt_secs(time.perf_counter() - t_wb)}]"
    )

    # --- Stage 3: prepare orders (steps 2–4) ---
    log_callback("3/4  Preparing orders (CL → fill → positions)…")
    t_prep = time.perf_counter()
    all_frames: list[pd.DataFrame] = []

    def _job(path: Path) -> tuple[Path, Optional[pd.DataFrame], Optional[str]]:
        try:
            return path, _process_one_csv(path, cache), None
        except Exception as exc:
            return path, None, str(exc)

    workers = min(_CSV_MAX_WORKERS, max(1, n_files))
    if n_files == 1:
        path, combined, err = _job(input_csv_paths[0])
        if err:
            log_callback(f"      Error — {path.name}: {err}")
            return None
        if combined is None:
            log_callback(f"      · {path.name} — no rows (skipped)")
        else:
            log_callback(f"      · {path.name} — {len(combined):,} row(s)")
            all_frames.append(combined)
    else:
        done = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_job, p): p for p in input_csv_paths}
            for fut in as_completed(futures):
                path, combined, err = fut.result()
                done += 1
                if err:
                    log_callback(f"      · [{done}/{n_files}] {path.name} — ERROR: {err}")
                    # Cancel remaining work; fail fast like the previous behaviour.
                    for pending in futures:
                        pending.cancel()
                    return None
                if combined is None:
                    log_callback(f"      · [{done}/{n_files}] {path.name} — no rows (skipped)")
                    continue
                log_callback(
                    f"      · [{done}/{n_files}] {path.name} — {len(combined):,} row(s)"
                )
                all_frames.append(combined)

    if not all_frames:
        log_callback("      No rows to audit.")
        log_callback("")
        log_callback("No preflight issues found.")
        return NO_ISSUES

    df = pd.concat(all_frames, ignore_index=True, sort=False)
    log_callback(
        f"      Prepared {len(df):,} row(s) from {len(all_frames)} file(s)"
        f"  [{_fmt_secs(time.perf_counter() - t_prep)}]"
    )

    # --- Stage 4: flags ---
    log_callback("4/4  Checking issues…")
    t_chk = time.perf_counter()
    unmatched_flags = expand_issue_mask_to_merge_groups(
        df, df["Gender Apparel"].map(_is_blank)
    )

    if image_checks_enabled:
        with demo_image_lookup(use_demo):
            missing_logo_flags, missing_apparel_flags = flag_missing_images(
                df,
                apparel_stem_map=apparel_map,
                logo_normal_stem_map=logo_normal_map,
                logo_custom_stem_map=logo_custom_map,
                apparel_image_dir=apparel_path,
                logo_normal_dir=logo_normal_path,
                logo_custom_single_dir=logo_custom_single_path,
                logo_custom_double_dir=logo_custom_double_path,
            )
        missing_logo_flags = expand_issue_mask_to_merge_groups(df, missing_logo_flags)
    else:
        missing_logo_flags = pd.Series(False, index=df.index, dtype=bool)
        missing_apparel_flags = pd.Series(False, index=df.index, dtype=bool)

    df = df.copy()
    df["Unmatched SKU"] = unmatched_flags.map(_yes_no)
    df["Missing Logo"] = missing_logo_flags.map(_yes_no)
    df["Missing Apparel"] = missing_apparel_flags.map(_yes_no)

    issue_mask = unmatched_flags | missing_logo_flags | missing_apparel_flags
    issues = df.loc[issue_mask].copy()

    unmatched_count = int(unmatched_flags.sum())
    missing_logo_count = int(missing_logo_flags.sum())
    missing_apparel_count = int(missing_apparel_flags.sum())
    log_callback(f"      Done  [{_fmt_secs(time.perf_counter() - t_chk)}]")
    log_callback("")

    log_callback("Summary")
    log_callback(f"  Unmatched SKU     {unmatched_count:,}")
    log_callback(f"  Missing Logo      {missing_logo_count:,}")
    log_callback(f"  Missing Apparel   {missing_apparel_count:,}")
    log_callback(f"  Issue rows        {len(issues):,} / {len(df):,}")
    log_callback("")

    if issues.empty:
        log_callback(f"No preflight issues found.  (total {_fmt_secs(time.perf_counter() - t0)})")
        return NO_ISSUES

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    out_path = output_dir / f"Preflight Issues_{timestamp}.csv"
    issues.to_csv(out_path, index=False, encoding="utf-8")
    log_callback(f"Wrote {len(issues):,} issue row(s) →")
    log_callback(f"  {out_path}")
    log_callback(f"Finished in {_fmt_secs(time.perf_counter() - t0)}")
    return PreflightResult(
        path=out_path,
        unmatched_count=unmatched_count,
        missing_logo_count=missing_logo_count,
        missing_apparel_count=missing_apparel_count,
        issue_row_count=len(issues),
    )


def run_unmatched_extraction(
    input_csv_paths: list[Path],
    workbook_path: Path,
    output_dir: Path,
    log_callback: Callable[[str], None],
) -> Path | None | object:
    """
    Compatibility wrapper: run preflight without image folders (Unmatched SKU flags only).
    Returns Path, NO_UNMATCHED/NO_ISSUES, or None on error.
    """
    result = run_preflight_audit(
        input_csv_paths,
        workbook_path,
        output_dir,
        log_callback,
    )
    if result is NO_ISSUES:
        return NO_UNMATCHED
    if isinstance(result, PreflightResult):
        return result.path
    return result
