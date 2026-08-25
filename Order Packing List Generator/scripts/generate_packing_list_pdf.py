"""
Backward-compatible wrapper for step 8 (packing list PDF generation).

Implementation lives under scripts/pipeline_generate_packing_list_pdf/.
This module re-exports the public API used by the pipeline runner and tests.
"""

from __future__ import annotations

from scripts.pipeline_generate_packing_list_pdf.cli import main_impl
from scripts.pipeline_generate_packing_list_pdf.runtime_api import (
    build_image_stem_map,
    build_order_counts,
    build_process_totals,
    collect_image_match_details,
    count_image_lookup_stats,
    csv_to_pdf,
    draw_page,
    format_image_match_log,
    format_missing_report,
    load_position_code_to_draw,
    render_one_pdf,
)
from scripts.pipeline_generate_packing_list_pdf.runtime_config import DEFAULT_WORKBOOK

_build_image_stem_map = build_image_stem_map
_render_one_pdf = render_one_pdf


def main() -> None:
    main_impl(
        default_workbook=DEFAULT_WORKBOOK,
        build_image_stem_map=build_image_stem_map,
        load_position_code_to_draw=load_position_code_to_draw,
        csv_to_pdf=csv_to_pdf,
        format_missing_report=format_missing_report,
    )


__all__ = [
    "DEFAULT_WORKBOOK",
    "_build_image_stem_map",
    "_render_one_pdf",
    "build_image_stem_map",
    "build_order_counts",
    "build_process_totals",
    "collect_image_match_details",
    "count_image_lookup_stats",
    "csv_to_pdf",
    "draw_page",
    "format_image_match_log",
    "format_missing_report",
    "load_position_code_to_draw",
    "main",
    "render_one_pdf",
]


if __name__ == "__main__":
    main()
