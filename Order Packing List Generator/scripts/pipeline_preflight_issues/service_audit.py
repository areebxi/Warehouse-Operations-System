"""Preflight audit orchestration: image index → prep → flags → CSV."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from pipeline_cl_lookup.enrich_cl_lookup import DEFAULT_CL_CSV

from .config import NO_ISSUES, NO_UNMATCHED
from .service_flags import flag_and_write_issues
from .service_images import index_image_folders
from .service_prep import _load_workbook_cache, prepare_order_frames
from .service_types import PreflightResult, _fmt_secs


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

    image_checks_enabled, use_demo, maps = index_image_folders(
        log_callback,
        use_demo_images=use_demo_images,
        apparel_dir=apparel_dir,
        logo_normal_dir=logo_normal_dir,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
    )

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

    log_callback("3/4  Preparing orders (CL → fill → positions)…")
    t_prep = time.perf_counter()
    all_frames = prepare_order_frames(input_csv_paths, cache, log_callback)
    if all_frames is None:
        return None
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

    return flag_and_write_issues(
        df,
        output_dir=output_dir,
        image_checks_enabled=image_checks_enabled,
        use_demo=use_demo,
        maps=maps,
        log_callback=log_callback,
        t0=t0,
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
