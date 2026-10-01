"""Single-SKU stock validation for one order line."""
from __future__ import annotations

from stock_resolver import not_found_status, resolve_stock_level
from run_stock_issue_rows import _issue_item_sku, build_issue_row


def validate_single_line(
    *,
    order_number,
    recipient_name,
    quantity,
    original_sku,
    tag_id,
    process_no,
    stock_levels,
    custom_label_map,
    missing_label_ids,
    log,
):
    """Return (ok, in_rows, out_rows, missing_rows) for one non-pack line."""
    stock_level, effective, marketplace, used_fallback = resolve_stock_level(
        original_sku, stock_levels, custom_label_map
    )
    if used_fallback:
        log(
            f"[CUSTOM LABEL] {original_sku} -> stock ID {effective} "
            f"(label {original_sku.split('-', 1)[1].strip()})"
        )
    packing_sku = effective if effective else ""
    item_data = [
        order_number,
        recipient_name,
        quantity,
        packing_sku,
        tag_id,
        stock_level,
        process_no,
        marketplace or (original_sku or "").strip(),
    ]
    if stock_level == -1:
        status = not_found_status(
            original_sku,
            custom_label_map,
            missing_label_ids,
            used_fallback=used_fallback,
        )
        log(
            f"[ERROR] {status}: Order {order_number}, "
            f"SKU {(original_sku or '').strip() or effective}"
        )
        return (
            False,
            [],
            [],
            [
                build_issue_row(
                    order_number,
                    recipient_name,
                    quantity,
                    original_sku,
                    tag_id,
                    -1,
                    process_no,
                    item_sku="",
                    stock_id=effective if used_fallback else "",
                    status=status,
                )
            ],
        )
    if stock_level < quantity:
        log(
            f"[WARNING] Insufficient stock: Order {order_number}, SKU {effective} "
            f"(Have {stock_level}, Need {quantity})"
        )
        return (
            False,
            [],
            [
                build_issue_row(
                    order_number,
                    recipient_name,
                    quantity,
                    original_sku,
                    tag_id,
                    stock_level,
                    process_no,
                    item_sku=_issue_item_sku(effective, used_fallback),
                    stock_id=effective,
                )
            ],
            [],
        )
    return True, [item_data], [], []
