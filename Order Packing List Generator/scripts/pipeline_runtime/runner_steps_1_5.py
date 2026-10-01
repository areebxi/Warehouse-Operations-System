from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import pandas as pd  # type: ignore[import]

from pipeline_assign_process_number.service import run as run_assign_process_number
from pipeline_cl_lookup.enrich_cl_lookup import NEW_COLUMNS, enrich_packing_data
from pipeline_cl_lookup.fetch_input_csv import (
    OUTPUT_COLUMNS,
    fetch_input_csv,
    write_fetched_csv,
)
from pipeline_fill_prime_images.service import fill_packing_columns
from pipeline_packing_rules.service import apply_packing_rules_to_csv
from pipeline_runtime.filter_missing_logos import filter_step6_csvs_for_missing_logos
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_utils import (
    _move_missing_logo_to_root,
    _move_unmatched_to_root,
    log_csv_preview,
)
from pipeline_split_position.service import run as run_split_and_assign_position_codes
from shared.demo_images import demo_image_lookup


def run_steps_1_to_5(
    *,
    input_csv_path: Path,
    output_root: Path,
    token: str,
    workbook_path: Path,
    cl_csv: Optional[Path],
    shift,
    shift_label: str,
    date_dd_mm_yyyy: str,
    dispatch_date,
    use_fixed_process_number: bool,
    fixed_process_number: Optional[str],
    separate_by_logo_id: bool,
    logo_id_threshold: int,
    logo_custom_single_dir,
    logo_custom_double_dir,
    logo_normal_dir,
    use_demo: bool,
    log: Optional[PipelineLog],
    lc,
    discover_step6_csvs=None,
) -> tuple[Path, Optional[Path], Optional[Path], object]:
    if log:
        log.step("Step 1/8: Fetching input CSV...")
    t_step = time.perf_counter()
    step1_path = output_root / f"1_fetch_input_csv_{token}.csv"
    rows = fetch_input_csv(input_csv_path)
    write_fetched_csv(rows, step1_path)
    if log:
        log.detail(
            f"Step 1/8: Done ({len(rows)} rows) -> {step1_path.name}  [{time.perf_counter() - t_step:.2f}s]"
        )
        log.detail(
            f"Step 1/8: output column order ({len(OUTPUT_COLUMNS)}): {', '.join(OUTPUT_COLUMNS)}"
        )
        if rows:
            r0 = rows[0]
            head_cols = OUTPUT_COLUMNS[:12]
            pairs = [
                f"{k}={(str(r0.get(k, '')).replace(chr(10), ' ').strip()[:72])}"
                for k in head_cols
                if k in r0
            ]
            if pairs:
                log.detail("Step 1/8: first input row (first columns, truncated): " + " | ".join(pairs))
        log_csv_preview(lc, step1_path, "Step 1 CSV preview (on disk)")

    apply_packing_rules_to_csv(step1_path, token=token, log=lc)

    if log:
        log.step("Step 2/8: Enriching CL lookup...")
    t_step = time.perf_counter()
    step2_path = output_root / f"2_enrich_cl_lookup_{token}.csv"
    df_step2 = enrich_packing_data(step1_path, workbook_path, log=lc, cl_csv_path=cl_csv)
    df_step2.to_csv(step2_path, index=False, encoding="utf-8")
    if log:
        log.detail(f"Step 2/8: Done ({len(df_step2)} rows) -> {step2_path.name}  [{time.perf_counter() - t_step:.2f}s]")
        present_new = [c for c in NEW_COLUMNS if c in df_step2.columns]
        log.detail(
            f"Step 2/8: total columns {len(df_step2.columns)}; CL-filled targets present: "
            f"{', '.join(present_new)}"
        )
        log_csv_preview(lc, step2_path, "Step 2 CSV preview (CL-enriched)")

    if log:
        log.step("Step 3/8: Filling Prime and images...")
    t_step = time.perf_counter()
    step3_path = output_root / f"3_fill_prime_and_images_{token}.csv"
    df_step3 = fill_packing_columns(step2_path, log=lc)
    df_step3.to_csv(step3_path, index=False, encoding="utf-8")
    if log:
        log.detail(f"Step 3/8: Done ({len(df_step3)} rows) -> {step3_path.name}  [{time.perf_counter() - t_step:.2f}s]")
        log_csv_preview(lc, step3_path, "Step 3 CSV preview (Prime / images filled)")

    if log:
        log.step("Step 4/8: Splitting and assigning position codes...")
    t_step = time.perf_counter()
    run_split_and_assign_position_codes(step3_path, workbook_path, output_root, log=lc)
    unmatched_csv_path = output_root / f"unmatched_orders_{token}.csv"
    unmatched_path: Optional[Path]
    unmatched_count = 0
    if unmatched_csv_path.exists():
        df_unmatched = pd.read_csv(unmatched_csv_path)
        unmatched_count = len(df_unmatched)
        if unmatched_count == 0:
            try:
                unmatched_csv_path.unlink()
            except OSError:
                pass
            unmatched_path = None
        else:
            unmatched_path = unmatched_csv_path
            moved = _move_unmatched_to_root(unmatched_path, date_dd_mm_yyyy, shift_label)
            if moved is not None:
                unmatched_path = moved
    else:
        unmatched_path = None
    matched_step4_path = output_root / f"4_matched_split_and_assign_position_codes_{token}.csv"
    if log:
        matched_count = len(pd.read_csv(matched_step4_path)) if matched_step4_path.exists() else 0
        log.detail(
            f"Step 4/8: Done (matched: {matched_count}, unmatched: {unmatched_count}) "
            f"-> {matched_step4_path.name}"
            + (f"; unmatched moved to {unmatched_path}" if unmatched_path else "")
            + f"  [{time.perf_counter() - t_step:.2f}s]"
        )
        log_csv_preview(lc, matched_step4_path, "Step 4 matched CSV preview (positions)")

    if log:
        log.step("Step 5/8: Assigning process numbers...")
    t_step = time.perf_counter()
    if not matched_step4_path.exists():
        raise FileNotFoundError(f"Step-4 matched CSV not found: {matched_step4_path}")
    fixed = (fixed_process_number or "").strip() if use_fixed_process_number else None
    run_assign_process_number(
        matched_step4_path,
        shift,
        workbook_path,
        output_root,
        dispatch_date=dispatch_date,
        separate_by_logo_id=separate_by_logo_id,
        logo_id_threshold=logo_id_threshold,
        fixed_process_number=fixed,
        log=lc,
    )
    step5_path = output_root / f"5_assign_process_number_{token}.csv"

    if not step5_path.exists():
        raise FileNotFoundError(f"Step-5 CSV not found after assign_process_number: {step5_path}")
    if log:
        n5 = len(pd.read_csv(step5_path))
        log.detail(f"Step 5/8: Done ({n5} rows) -> {step5_path.name}  [{time.perf_counter() - t_step:.2f}s]")
        log_csv_preview(lc, step5_path, "Step 5 CSV preview (process numbers)")

    if log:
        log.step("Filtering missing logos (before process/item naming)...")
    t_miss = time.perf_counter()
    with demo_image_lookup(use_demo):
        kept_step5, missing_logo_path, missing_logo_count = filter_step6_csvs_for_missing_logos(
            [step5_path],
            output_root=output_root,
            token=token,
            logo_custom_single_dir=logo_custom_single_dir,
            logo_custom_double_dir=logo_custom_double_dir,
            logo_normal_dir=logo_normal_dir,
            log=lc,
        )
    if missing_logo_path is not None:
        moved_missing = _move_missing_logo_to_root(missing_logo_path, date_dd_mm_yyyy, shift_label)
        if moved_missing is not None:
            missing_logo_path = moved_missing
    if log:
        log.detail(
            f"  Missing-logo filter done — excluded {missing_logo_count} row(s)"
            + (f"; file: {missing_logo_path}" if missing_logo_path else "")
            + f"  [{time.perf_counter() - t_miss:.2f}s]"
        )
    return step5_path, unmatched_path, missing_logo_path, kept_step5
