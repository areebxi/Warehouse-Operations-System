"""Packing PDF image-match reporting — stable façade."""

from __future__ import annotations

from pipeline_generate_packing_list_pdf.reporting_counts import (
    build_order_counts_impl,
    build_process_totals_impl,
)
from pipeline_generate_packing_list_pdf.reporting_format import (
    _format_missing_items_section,
    format_image_match_log_impl,
    format_missing_report_impl,
)
from pipeline_generate_packing_list_pdf.reporting_lookup_source import (
    _custom_pdf_slot_token_label,
    _lookup_source_apparel,
    _lookup_source_custom_logo,
    _lookup_source_normal_logo,
)
from pipeline_generate_packing_list_pdf.reporting_match_details import (
    collect_image_match_details_impl,
)
from pipeline_generate_packing_list_pdf.reporting_stats import (
    count_image_lookup_stats_impl,
)

__all__ = [
    "build_order_counts_impl",
    "build_process_totals_impl",
    "count_image_lookup_stats_impl",
    "collect_image_match_details_impl",
    "format_image_match_log_impl",
    "format_missing_report_impl",
]
