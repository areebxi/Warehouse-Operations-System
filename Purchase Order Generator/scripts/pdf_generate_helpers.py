"""Small helpers used while generating packing-slip PDFs."""
from __future__ import annotations


def _safe_add_single_page(pdf: 'PDF', item_data, product_data, item_count, total_items):
    """Render a single item page even if PDF.add_packing_slip doesn't exist."""
    add_single_fn = getattr(pdf, 'add_packing_slip', None)
    if callable(add_single_fn):
        add_single_fn(item_data, product_data, item_count, total_items)
        return
    # Manual render using internal helpers
    pdf.add_page(orientation='L')
    if hasattr(pdf, '_draw_header'):
        pdf._draw_header(item_data, product_data or {}, item_count, total_items)
    if hasattr(pdf, '_draw_product_details'):
        pdf._draw_product_details(item_data, product_data or {}, total_items)
