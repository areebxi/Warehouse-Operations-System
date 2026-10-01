"""Stock-issue row builders and discount detection."""
from __future__ import annotations


def is_discount_line_item(item) -> bool:
    """True for Etsy/marketplace discount / fee adjustment lines (no stock check)."""
    name = (item.get("name") or "").strip().casefold()
    sku = (item.get("sku") or "").strip()
    if "discount" in name:
        return True
    if item.get("adjustment") and not sku:
        return True
    return False


def build_issue_row(
    order_number,
    recipient_name,
    quantity,
    original_sku,
    tag_id,
    stock_level,
    process_no,
    *,
    item_sku="",
    stock_id="",
    status="",
) -> list:
    """Internal row for stock-issue exports (9 fields, or 10 when status set).

    Item SKU is blank when the before-dash prefix was not a real stock hit
    (custom-label / after-dash path, or not found). Complete SKU is always
    the full marketplace / ShipStation SKU. Status is set for not-found rows so
    the CSV can distinguish custom-label vs stock-levels misses.
    """
    row = [
        order_number,
        recipient_name,
        quantity,
        item_sku or "",
        (original_sku or "").strip(),
        stock_id or "",
        tag_id,
        stock_level,
        process_no,
    ]
    if status:
        row.append(status)
    return row


def _issue_item_sku(effective: str, used_fallback: bool) -> str:
    """Display Item SKU only for a real primary stock-id hit."""
    if used_fallback:
        return ""
    return effective or ""
