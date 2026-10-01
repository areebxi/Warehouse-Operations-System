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


def finish_excel_phase(
    *,
    output_root: Path,
    unmatched_path: Optional[Path],
    missing_logo_path: Optional[Path],
    excel_copy_dir,
    shift_label: str,
    log: Optional[PipelineLog],
    lc,
) -> tuple[Path, Optional[Path], Optional[Path], Optional[str]]:
    step8_missing_logos_report: Optional[str] = None
    if log:
        log.detail("Excel phase complete — skipping PDF (Step 8) for this pass.")
    copy_warnings = []
    if excel_copy_dir:
        copy_warnings = _copy_outputs_to_shift_dirs(
            output_root, shift_label, None, excel_copy_dir, lc
        )
        if copy_warnings:
            step8_missing_logos_report = "\n".join(copy_warnings)
    if log:
        log.detail("----------")
        log.detail(f"Excel phase finished. Primary output: {output_root.resolve()}")
        if unmatched_path:
            try:
                log.detail(f"Unmatched orders file: {unmatched_path.resolve()}")
            except OSError:
                log.detail(f"Unmatched orders file: {unmatched_path}")
        if missing_logo_path:
            try:
                log.detail(f"Missing logo orders file: {missing_logo_path.resolve()}")
            except OSError:
                log.detail(f"Missing logo orders file: {missing_logo_path}")
        if copy_warnings:
            log.detail("Excel copy had failures (also included in Finished report):")
            for w in copy_warnings:
                log.detail(f"  {w}")
        log.detail("----------")
    return output_root, unmatched_path, missing_logo_path, step8_missing_logos_report


def finish_full_pipeline(
    *,
    output_root: Path,
    unmatched_path: Optional[Path],
    missing_logo_path: Optional[Path],
    step6_csvs: list[Path],
    workbook_path: Path,
    apparel_dir,
    logo_custom_single_dir,
    logo_custom_double_dir,
    logo_normal_dir,
    pdf_copy_dir,
    excel_copy_dir,
    shift_label: str,
    date_dd_mm_yyyy: str,
    use_demo: bool,
    log: Optional[PipelineLog],
    lc,
) -> tuple[Path, Optional[Path], Optional[Path], Optional[str]]:
    if log:
        log.step(
            "Step 8/8: starting PDF phase (Excel files are complete). "
            "The next log block may pause briefly while image folders are indexed."
        )

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

    if pdf_copy_dir or excel_copy_dir:
        copy_warnings = _copy_outputs_to_shift_dirs(
            output_root, shift_label, pdf_copy_dir, excel_copy_dir, lc
        )
        if copy_warnings:
            extra = "\n".join(copy_warnings)
            if step8_missing_logos_report:
                step8_missing_logos_report = f"{step8_missing_logos_report}\n\n{extra}"
            else:
                step8_missing_logos_report = extra
    else:
        copy_warnings = []
    if log:
        log.detail("----------")
        log.detail(f"Pipeline finished. Primary output: {output_root.resolve()}")
        if unmatched_path:
            try:
                log.detail(f"Unmatched orders file: {unmatched_path.resolve()}")
            except OSError:
                log.detail(f"Unmatched orders file: {unmatched_path}")
        if missing_logo_path:
            try:
                log.detail(f"Missing logo orders file: {missing_logo_path.resolve()}")
            except OSError:
                log.detail(f"Missing logo orders file: {missing_logo_path}")
        if step8_missing_logos_report and not (
            copy_warnings and step8_missing_logos_report == "\n".join(copy_warnings)
        ):
            log.detail("Missing-logos report was produced (see Step 8 messages above).")
        if copy_warnings:
            log.detail("PDF/Excel copy had failures (also included in Finished report):")
            for w in copy_warnings:
                log.detail(f"  {w}")
        log.detail("----------")
    return output_root, unmatched_path, missing_logo_path, step8_missing_logos_report
