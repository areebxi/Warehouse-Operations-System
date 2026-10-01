from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import pandas as pd  # type: ignore[import]

from pipeline_generate_excel_outputs.service import run as run_generate_excel_outputs
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_utils import _update_all_orders_log, log_csv_preview
from pipeline_split_by_process_item.service import run as run_split_by_process_and_item_number


def run_steps_6_to_7(
    *,
    step5_path: Path,
    kept_step5,
    output_root: Path,
    workbook_path: Path,
    dispatch_date,
    use_fixed_process_number: bool,
    date_dd_mm_yyyy: str,
    shift_label: str,
    token: str,
    log: Optional[PipelineLog],
    lc,
    discover_step6_csvs,
) -> list[Path]:
    if log:
        log.step("Step 6/8: Splitting by process and item number...")
    t_step = time.perf_counter()
    if not kept_step5 or not step5_path.exists():
        step6_csvs = []
        if log:
            log.detail("  Step 6: skipped — no rows left after missing-logo filter.")
    else:
        run_split_by_process_and_item_number(
            step5_path,
            output_root,
            workbook_path,
            run_date=dispatch_date,
            use_simple_process_format=True,
            use_fixed_numeric_process=False,
            fixed_process_number=None,
            log=lc,
        )
        step6_csvs = discover_step6_csvs(output_root, token)

    for csv_path in step6_csvs:
        _update_all_orders_log(csv_path, date_dd_mm_yyyy, log=lc)
    if log:
        total_s6 = 0
        for p in sorted(step6_csvs, key=lambda x: x.name):
            try:
                nrows = len(pd.read_csv(p, encoding="utf-8"))
            except Exception as exc:
                log.detail(f"  Step 6: could not count rows in {p.name}: {exc}")
                continue
            total_s6 += nrows
            log.detail(f"  Step 6: {p.name} — {nrows} row(s)")
        log.detail(
            f"Step 6/8: Done — {len(step6_csvs)} process CSV file(s), "
            f"{total_s6} total row(s) across files  [{time.perf_counter() - t_step:.2f}s]"
        )
        if step6_csvs:
            first_proc = sorted(step6_csvs, key=lambda x: x.name)[0]
            log_csv_preview(lc, first_proc, "Step 6 CSV preview (first process file by name)")

    if log:
        log.step("Step 7/8: Generating Excel outputs...")
    t_step = time.perf_counter()
    for csv_path in step6_csvs:
        if log:
            log.detail(f"  Step 7/8: generating Excel from {csv_path.name} ...")
        run_generate_excel_outputs(
            csv_path,
            output_root,
            dispatch_date,
            use_fixed_process_number=use_fixed_process_number,
            use_fixed_numeric_process=False,
            log=lc,
            date_dd_mm_yyyy=date_dd_mm_yyyy,
            shift_label=shift_label,
        )
        if log:
            log.detail(f"  Step 7/8: completed Excel trio for {csv_path.name}")
    if log:
        xlsx_files = sorted(output_root.glob("*.xlsx"))
        log.detail(
            f"  Step 7/8: {len(xlsx_files)} Excel file(s) in output folder "
            f"{output_root.resolve()}"
        )
        for xf in xlsx_files[:80]:
            log.detail(f"    {xf.name}")
        if len(xlsx_files) > 80:
            log.detail(f"    ... and {len(xlsx_files) - 80} more .xlsx in this folder")
        log.detail(
            "  Step 7: each process CSV generates three Excel workbooks (Picking, Orders Details, DTF Des) "
            "in the same output folder as the CSV."
        )
        log.detail(f"Step 7/8: Done  [{time.perf_counter() - t_step:.2f}s]")
    return step6_csvs
