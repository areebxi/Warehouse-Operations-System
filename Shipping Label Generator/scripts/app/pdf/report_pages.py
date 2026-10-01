"""PDF report page builders — stable façade."""

from __future__ import annotations

from app.pdf.report_pages_missed import (
    make_combined_missed_orders_page_pdf,
    make_label_error_page_pdf,
    make_missed_orders_page_pdf,
)
from app.pdf.report_pages_summary import _create_summary_pdf, make_summary_page_pdf
from app.pdf.report_pages_text import (
    _error_reason_paragraph_text,
    _plain_cell_text,
    _summary_process_font_size,
    _truncate_text,
)

__all__ = [
    "_truncate_text",
    "_error_reason_paragraph_text",
    "_plain_cell_text",
    "_summary_process_font_size",
    "_create_summary_pdf",
    "make_summary_page_pdf",
    "make_missed_orders_page_pdf",
    "make_combined_missed_orders_page_pdf",
    "make_label_error_page_pdf",
]
