from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipeline_generate_packing_list_pdf.runtime_api import (
    build_image_stem_map,
    collect_image_match_details,
    csv_to_pdf,
    format_image_match_log,
    format_missing_report,
    load_position_code_to_draw,
    render_one_pdf,
)
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_step8_pdf import run_step8_pdf_generation_impl
from pipeline_runtime.runner_utils import (
    _copy_outputs_to_shift_dirs,
    _sanitize_process_for_filename,
)
from shared.demo_images import demo_image_lookup


def run_pdf_only_phase(
    *,
    output_root: Path,
    token: str,
    workbook_path: Path,
    apparel_dir,
    logo_custom_single_dir,
    logo_custom_double_dir,
    logo_normal_dir,
    pdf_copy_dir,
    shift_label: str,
    date_dd_mm_yyyy: str,
    use_demo: bool,
    log: Optional[PipelineLog],
    lc,
    discover_step6_csvs,
) -> tuple[Path, None, None, Optional[str]]:
    step6_csvs = discover_step6_csvs(output_root, token)
    if log:
        log.step(
            "Step 8/8: starting PDF phase (Excel files are complete). "
            "The next log block may pause briefly while image folders are indexed."
        )
        log.detail(f"  PDF phase: rediscovered {len(step6_csvs)} process CSV(s) in {output_root}")
    step8_missing_logos_report: Optional[str] = None
    with demo_image_lookup(use_demo):
        step8_missing_logos_report = run_step8_pdf_generation_impl(
            step6_csvs=step6_csvs,
            workbook_path=workbook_path,
            apparel_dir=apparel_dir,
            logo_custom_single_dir=logo_custom_single_dir,
            logo_custom_double_dir=logo_custom_double_dir,
            logo_normal_dir=logo_normal_dir,
            build_image_stem_map=build_image_stem_map,
            render_one_pdf=render_one_pdf,
            csv_to_pdf=csv_to_pdf,
            load_position_code_to_draw=load_position_code_to_draw,
            format_missing_report=format_missing_report,
            collect_image_match_details=collect_image_match_details,
            format_image_match_log=format_image_match_log,
            sanitize_process_for_filename=_sanitize_process_for_filename,
            date_dd_mm_yyyy=date_dd_mm_yyyy,
            log=log,
        )
    copy_warnings: list[str] = []
    if pdf_copy_dir:
        copy_warnings = _copy_outputs_to_shift_dirs(
            output_root, shift_label, pdf_copy_dir, None, lc
        )
        if copy_warnings:
            extra = "\n".join(copy_warnings)
            if step8_missing_logos_report:
                step8_missing_logos_report = f"{step8_missing_logos_report}\n\n{extra}"
            else:
                step8_missing_logos_report = extra
    if log:
        log.detail("----------")
        log.detail(f"PDF phase finished. Primary output: {output_root.resolve()}")
        if step8_missing_logos_report and not (
            copy_warnings and step8_missing_logos_report == "\n".join(copy_warnings)
        ):
            log.detail("Missing-logos report was produced (see Step 8 messages above).")
        if copy_warnings:
            log.detail("PDF copy had failures (also included in Finished report):")
            for w in copy_warnings:
                log.detail(f"  {w}")
        log.detail("----------")
    return output_root, None, None, step8_missing_logos_report
