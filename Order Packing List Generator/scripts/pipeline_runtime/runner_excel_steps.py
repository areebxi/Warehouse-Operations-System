from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_steps_1_5 import run_steps_1_to_5
from pipeline_runtime.runner_steps_6_7 import run_steps_6_to_7


def run_excel_steps(
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
    discover_step6_csvs,
    make_design_queues: bool = True,
) -> tuple[list[Path], Optional[Path], Optional[Path]]:
    step5_path, unmatched_path, missing_logo_path, kept_step5 = run_steps_1_to_5(
        input_csv_path=input_csv_path,
        output_root=output_root,
        token=token,
        workbook_path=workbook_path,
        cl_csv=cl_csv,
        shift=shift,
        shift_label=shift_label,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        dispatch_date=dispatch_date,
        use_fixed_process_number=use_fixed_process_number,
        fixed_process_number=fixed_process_number,
        separate_by_logo_id=separate_by_logo_id,
        logo_id_threshold=logo_id_threshold,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
        logo_normal_dir=logo_normal_dir,
        use_demo=use_demo,
        log=log,
        lc=lc,
        discover_step6_csvs=discover_step6_csvs,
    )
    step6_csvs = run_steps_6_to_7(
        step5_path=step5_path,
        kept_step5=kept_step5,
        output_root=output_root,
        workbook_path=workbook_path,
        dispatch_date=dispatch_date,
        use_fixed_process_number=use_fixed_process_number,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        shift_label=shift_label,
        token=token,
        log=log,
        lc=lc,
        discover_step6_csvs=discover_step6_csvs,
        make_design_queues=make_design_queues,
    )
    return step6_csvs, unmatched_path, missing_logo_path
