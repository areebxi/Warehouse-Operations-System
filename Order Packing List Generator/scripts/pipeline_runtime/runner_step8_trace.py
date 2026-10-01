from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from pipeline_generate_packing_list_pdf.runtime_api import count_image_lookup_stats
from pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_utils import (
    build_image_trace_log_file_body,
    log_image_trace_block,
)


def write_step8_image_traces(
    *,
    step6_csvs: list[Path],
    indexed: dict[str, Any],
    workbook_path: Path,
    collect_image_match_details,
    format_image_match_log,
    sanitize_process_for_filename,
    log: Optional[PipelineLog],
    lc,
) -> None:
    apparel_stem_map = indexed["apparel_stem_map"]
    logo_custom_stem_map = indexed["logo_custom_stem_map"]
    logo_normal_stem_map = indexed["logo_normal_stem_map"]
    apparel_dir_path = indexed["apparel_dir_path"]
    logo_custom_single_path = indexed["logo_custom_single_path"]
    logo_custom_double_path = indexed["logo_custom_double_path"]
    logo_normal_path = indexed["logo_normal_path"]
    run_timestamp = indexed["run_timestamp"]
    has_image_lookup_main = indexed["has_image_lookup_main"]
    if has_image_lookup_main:
        for csv_path in step6_csvs:
            process_name = sanitize_process_for_filename(csv_path.stem)
            df_csv = read_csv_with_order_numbers(csv_path)
            details = collect_image_match_details(
                df_csv,
                apparel_stem_map,
                logo_normal_stem_map,
                logo_custom_stem_map,
                apparel_image_dir=apparel_dir_path,
                logo_customise_dir=None,
                logo_normal_dir=logo_normal_path,
            )
            detail_text = format_image_match_log(details)
            stats = count_image_lookup_stats(
                df_csv,
                apparel_stem_map,
                logo_normal_stem_map,
                logo_custom_stem_map,
                apparel_image_dir=apparel_dir_path,
                logo_customise_dir=None,
                logo_normal_dir=logo_normal_path,
            )
            file_body = build_image_trace_log_file_body(
                step_label="Step 8/8 — image resolution after PDF generation",
                run_timestamp=run_timestamp,
                source_csv=csv_path,
                row_count=len(df_csv),
                workbook_path=workbook_path,
                output_pdf=csv_path.with_suffix(".pdf"),
                output_folder=csv_path.parent,
                apparel_dir=apparel_dir_path,
                logo_custom_single_dir=logo_custom_single_path,
                logo_custom_double_dir=logo_custom_double_path,
                logo_normal_dir=logo_normal_path,
                unique_apparel_stems=len(apparel_stem_map or {}),
                unique_logo_custom_stems=len(logo_custom_stem_map or {}),
                unique_logo_normal_stems=len(logo_normal_stem_map or {}),
                detail_text=detail_text,
                apparel_found=stats["apparel_found"],
                apparel_total=stats["apparel_total"],
                logo_found=stats["logo_found"],
                logo_total=stats["logo_total"],
            )
            if log:
                log.detail(
                    f"  Step 8: image trace for {csv_path.name} (process {process_name}) — "
                    f"apparel {stats['apparel_found']}/{stats['apparel_total']}, "
                    f"logo {stats['logo_found']}/{stats['logo_total']} (full block follows)"
                )
            log_image_trace_block(lc, file_body)
    elif log:
        log.detail(
            "  Step 8: no image-lookup trace block (no stem maps and no configured image directories)."
        )

