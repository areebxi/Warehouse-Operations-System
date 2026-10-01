"""Order-level stock validation (pack-aware, atomic per order)."""
from __future__ import annotations

from run_packs import _pack_key
from run_stock_issue_rows import is_discount_line_item
from run_stock_pack import validate_pack_line
from run_stock_single import validate_single_line


def validate_orders_stock(
    filtered_orders,
    tag_id: str,
    process_no,
    stock_levels: dict[str, int],
    packs_map: dict,
    pack_names_map: dict,
    custom_label_map: dict[str, str],
    log=print,
    labels_missing_stock_id: set[str] | None = None,
):
    """
    Build in-stock, out-of-stock, and not-found item lists (pack-aware, atomic per order).
    In-stock single-SKU rows: 8 fields ending with marketplace_sku.
    In-stock pack rows: 11 fields ending with marketplace_sku.
    """
    missing_label_ids = labels_missing_stock_id or set()
    in_stock_items = []
    out_of_stock_items = []
    not_found_items = []

    for order in filtered_orders:
        order_number = order.get("orderNumber", "")
        ship_to = order.get("shipTo") or {}
        recipient_name = ship_to.get("name", "")

        raw_items = order.get("items", []) or order.get("lineItems", [])
        items = []
        for item in raw_items:
            if is_discount_line_item(item):
                log(f"[SKIP] Ignoring Discount line on order {order_number}")
            else:
                items.append(item)

        if not items:
            log(f"[WARNING] Order {order_number} has no items")
            in_stock_items.append(
                [order_number, recipient_name, "", "", tag_id, "N/A", process_no, ""]
            )
            continue

        order_ok = True
        in_rows_for_order = []
        out_rows_for_order = []
        missing_rows_for_order = []
        for item in items:
            quantity = item.get("quantity", 1)
            original_sku = item.get("sku", "")
            pack_key = _pack_key(original_sku)
            component_candidates = packs_map.get(pack_key, [])
            if component_candidates:
                ok, in_r, out_r, miss_r = validate_pack_line(
                    order_number=order_number,
                    recipient_name=recipient_name,
                    quantity=quantity,
                    original_sku=original_sku,
                    pack_key=pack_key,
                    component_candidates=component_candidates,
                    tag_id=tag_id,
                    process_no=process_no,
                    stock_levels=stock_levels,
                    pack_names_map=pack_names_map,
                    custom_label_map=custom_label_map,
                    missing_label_ids=missing_label_ids,
                    log=log,
                )
            else:
                ok, in_r, out_r, miss_r = validate_single_line(
                    order_number=order_number,
                    recipient_name=recipient_name,
                    quantity=quantity,
                    original_sku=original_sku,
                    tag_id=tag_id,
                    process_no=process_no,
                    stock_levels=stock_levels,
                    custom_label_map=custom_label_map,
                    missing_label_ids=missing_label_ids,
                    log=log,
                )
            if not ok:
                order_ok = False
            in_rows_for_order.extend(in_r)
            out_rows_for_order.extend(out_r)
            missing_rows_for_order.extend(miss_r)

        if order_ok:
            in_stock_items.extend(in_rows_for_order)
            log(
                f"[FOUND] Order {order_number} fully in stock ({len(in_rows_for_order)} lines)"
            )
        else:
            out_of_stock_items.extend(out_rows_for_order)
            if missing_rows_for_order:
                not_found_items.extend(missing_rows_for_order)
            log(f"[WARNING] Order {order_number} moved to out-of-stock (atomic rule)")

    return in_stock_items, out_of_stock_items, not_found_items
