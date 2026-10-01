"""Step 8 PDF generation — stable façade over index / render / trace."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipeline_runtime.pipeline_log import PipelineLog, detail_callable
from pipeline_runtime.runner_step8_index import (
    _log_overlay_sample,
    _log_stem_sample_keys,
    index_step8_stem_maps,
    log_step8_index,
)
from pipeline_runtime.runner_step8_render import render_step8_pdfs
from pipeline_runtime.runner_step8_trace import write_step8_image_traces

__all__ = [
    "run_step8_pdf_generation_impl",
    "_log_stem_sample_keys",
    "_log_overlay_sample",
]


def run_step8_pdf_generation_impl(
    *,
    step6_csvs: list[Path],
    workbook_path: Path,
    apparel_dir: Optional[str | Path],
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    build_image_stem_map,
    render_one_pdf,
    csv_to_pdf,
    load_position_code_to_draw,
    format_missing_report,
    collect_image_match_details,
    format_image_match_log,
    sanitize_process_for_filename,
    date_dd_mm_yyyy: Optional[str] = None,
    log: Optional[PipelineLog] = None,
) -> Optional[str]:
    lc = detail_callable(log)
    if log:
        log.step(
            "Step 8/8: PDF — indexing image folders (parallel scan of apparel + logo directories). "
            "Very large folders can take 30–120s on first scan; later runs in this session reuse "
            "an in-memory (and on-disk) stem-map cache. Stem counts appear in the next block."
        )

    indexed = index_step8_stem_maps(
        apparel_dir=apparel_dir,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
        logo_normal_dir=logo_normal_dir,
        workbook_path=workbook_path,
        build_image_stem_map=build_image_stem_map,
        load_position_code_to_draw=load_position_code_to_draw,
        log=log,
    )
    log_step8_index(log, indexed)

    if log:
        log.step("Step 8/8: Generating PDFs...")

    step8_missing_logos_report = render_step8_pdfs(
        step6_csvs=step6_csvs,
        indexed=indexed,
        render_one_pdf=render_one_pdf,
        csv_to_pdf=csv_to_pdf,
        format_missing_report=format_missing_report,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        log=log,
        lc=lc,
    )

    write_step8_image_traces(
        step6_csvs=step6_csvs,
        indexed=indexed,
        workbook_path=workbook_path,
        collect_image_match_details=collect_image_match_details,
        format_image_match_log=format_image_match_log,
        sanitize_process_for_filename=sanitize_process_for_filename,
        log=log,
        lc=lc,
    )

    if log:
        log.step("Step 8/8: Done.")

    return step8_missing_logos_report
