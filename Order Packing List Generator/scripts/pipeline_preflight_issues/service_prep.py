"""Preflight CSV prep: workbook cache + per-file steps 2–4."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from pipeline_cl_lookup.enrich_cl_lookup import (
    apply_cl_enrichment,
    build_cl_lookup,
    load_cl_database,
)
from pipeline_cl_lookup.fetch_input_csv import fetch_input_csv
from pipeline_fill_prime_images.service import fill_packing_columns_df
from pipeline_runtime.order_number_csv import coerce_order_number_columns
from pipeline_split_by_process_item.common import pin_batch_shift
from pipeline_split_by_process_item.duplicate_order_suffixes import (
    assign_merge_order_number_suffixes,
)
from pipeline_split_by_process_item.grouping_quantity import (
    _expand_df_by_quantity,
)
from pipeline_split_position.io_process_info import (
    load_logo_ids_to_positions,
    load_multiple_positions,
    load_process_info_pq,
)
from pipeline_split_position.service import transform_step4_df
from pipeline_split_position.transform_position_codes import build_position_lookup

from .service_types import WorkbookCache

# Parallel CSV prep — workbook cache is read-only shared state.
_CSV_MAX_WORKERS = 4


def _load_workbook_cache(workbook_path: Path, cl_csv_path: Path | None = None) -> WorkbookCache:
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
    return WorkbookCache(
        cl_lookup=cl_lookup,
        logo_id_to_position=logo_id_to_position,
        default_code=default_code,
        position_to_code=position_to_code,
        multiple_positions_df=multiple_positions_df,
    )


def _process_one_csv(
    csv_path: Path,
    cache: WorkbookCache,
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
    # Input CSV stem → B1-S1 (batch+shift); RESEND / numeric stay whole.
    combined["Process Number"] = pin_batch_shift(csv_path.stem)
    cols = ["Process Number"] + [c for c in combined.columns if c != "Process Number"]
    return combined[cols]


def prepare_order_frames(
    input_csv_paths: list[Path],
    cache: WorkbookCache,
    log_callback: Callable[[str], None],
) -> list[pd.DataFrame] | None:
    """Stage 3: run steps 2–4 per CSV. Returns frames, or None on hard error."""
    n_files = len(input_csv_paths)
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
        return all_frames

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_job, p): p for p in input_csv_paths}
        for fut in as_completed(futures):
            path, combined, err = fut.result()
            done += 1
            if err:
                log_callback(f"      · [{done}/{n_files}] {path.name} — ERROR: {err}")
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
    return all_frames


__all__ = [
    "_CSV_MAX_WORKERS",
    "_load_workbook_cache",
    "_process_one_csv",
    "prepare_order_frames",
]
