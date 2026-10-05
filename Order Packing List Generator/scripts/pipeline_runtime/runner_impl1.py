"""run_pipeline orchestrator — setup / excel / queues / pdf finish live in sibling modules."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Tuple

from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.run_design_queues_step import run_design_queues_for_outputs
from pipeline_runtime.runner_excel_steps import run_excel_steps
from pipeline_runtime.runner_finish import finish_excel_phase, finish_full_pipeline
from pipeline_runtime.runner_impl2 import discover_step6_csvs
from pipeline_runtime.runner_pdf_phase import run_pdf_only_phase
from pipeline_runtime.runner_setup import prepare_pipeline_run

PipelinePhase = Literal["all", "excel", "pdf"]


def run_pipeline(
    input_csv: str | Path,
    date_dd_mm_yyyy: str,
    shift: str,
    output_dir: str | Path,
    workbook_path: str | Path,
    apparel_dir: Optional[str | Path],
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    separate_by_logo_id: bool = False,
    logo_id_threshold: int = 5,
    use_fixed_process_number: bool = False,
    fixed_process_number: Optional[str] = None,
    pdf_copy_dir: Optional[str | Path] = None,
    excel_copy_dir: Optional[str | Path] = None,
    log: Optional[PipelineLog] = None,
    phases: PipelinePhase = "all",
    cl_csv_path: Optional[str | Path] = None,
    use_demo_images: bool = False,
    make_design_queues: bool = True,
) -> Tuple[Path, Optional[Path], Optional[Path], Optional[str]]:
    """Run the packing pipeline for a single input CSV."""
    if phases not in ("all", "excel", "pdf"):
        raise ValueError(f"phases must be 'all', 'excel', or 'pdf', got {phases!r}")

    ctx = prepare_pipeline_run(
        input_csv=input_csv,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        shift=shift,
        output_dir=output_dir,
        workbook_path=workbook_path,
        apparel_dir=apparel_dir,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
        logo_normal_dir=logo_normal_dir,
        use_demo_images=use_demo_images,
        phases=phases,
        cl_csv_path=cl_csv_path,
        use_fixed_process_number=use_fixed_process_number,
        fixed_process_number=fixed_process_number,
        separate_by_logo_id=separate_by_logo_id,
        logo_id_threshold=logo_id_threshold,
        pdf_copy_dir=pdf_copy_dir,
        excel_copy_dir=excel_copy_dir,
        log=log,
    )

    if phases == "pdf":
        return run_pdf_only_phase(
            output_root=ctx["output_root"],
            token=ctx["token"],
            workbook_path=ctx["workbook_path"],
            apparel_dir=ctx["apparel_dir"],
            logo_custom_single_dir=ctx["logo_custom_single_dir"],
            logo_custom_double_dir=ctx["logo_custom_double_dir"],
            logo_normal_dir=ctx["logo_normal_dir"],
            pdf_copy_dir=pdf_copy_dir,
            shift_label=ctx["shift_label"],
            date_dd_mm_yyyy=ctx["date_dd_mm_yyyy"],
            use_demo=ctx["use_demo"],
            log=log,
            lc=ctx["lc"],
            discover_step6_csvs=discover_step6_csvs,
        )

    step6_csvs, unmatched_path, missing_logo_path = run_excel_steps(
        input_csv_path=ctx["input_csv_path"],
        output_root=ctx["output_root"],
        token=ctx["token"],
        workbook_path=ctx["workbook_path"],
        cl_csv=ctx["cl_csv"],
        shift=shift,
        shift_label=ctx["shift_label"],
        date_dd_mm_yyyy=ctx["date_dd_mm_yyyy"],
        dispatch_date=ctx["dispatch_date"],
        use_fixed_process_number=use_fixed_process_number,
        fixed_process_number=fixed_process_number,
        separate_by_logo_id=separate_by_logo_id,
        logo_id_threshold=logo_id_threshold,
        logo_custom_single_dir=ctx["logo_custom_single_dir"],
        logo_custom_double_dir=ctx["logo_custom_double_dir"],
        logo_normal_dir=ctx["logo_normal_dir"],
        use_demo=ctx["use_demo"],
        log=log,
        lc=ctx["lc"],
        discover_step6_csvs=discover_step6_csvs,
        make_design_queues=make_design_queues,
    )

    if phases == "excel":
        return finish_excel_phase(
            output_root=ctx["output_root"],
            unmatched_path=unmatched_path,
            missing_logo_path=missing_logo_path,
            excel_copy_dir=excel_copy_dir,
            shift_label=ctx["shift_label"],
            log=log,
            lc=ctx["lc"],
        )

    # Excel done; sync Design Queues (wait) before packing list PDFs.
    run_design_queues_for_outputs(
        [ctx["output_root"]],
        make_design_queues=make_design_queues,
        log=ctx["lc"],
        date_dd_mm_yyyy=ctx["date_dd_mm_yyyy"],
        shift_label=ctx["shift_label"],
    )

    return finish_full_pipeline(
        output_root=ctx["output_root"],
        unmatched_path=unmatched_path,
        missing_logo_path=missing_logo_path,
        step6_csvs=step6_csvs,
        workbook_path=ctx["workbook_path"],
        apparel_dir=ctx["apparel_dir"],
        logo_custom_single_dir=ctx["logo_custom_single_dir"],
        logo_custom_double_dir=ctx["logo_custom_double_dir"],
        logo_normal_dir=ctx["logo_normal_dir"],
        pdf_copy_dir=pdf_copy_dir,
        excel_copy_dir=excel_copy_dir,
        shift_label=ctx["shift_label"],
        date_dd_mm_yyyy=ctx["date_dd_mm_yyyy"],
        use_demo=ctx["use_demo"],
        log=log,
        lc=ctx["lc"],
    )
