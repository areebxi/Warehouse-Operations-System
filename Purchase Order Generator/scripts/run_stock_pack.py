"""Pack-aware stock validation for one order line."""
from __future__ import annotations

from stock_resolver import STATUS_NOT_FOUND, not_found_status, resolve_stock_level
from run_stock_issue_rows import build_issue_row


def validate_pack_line(
    *,
    order_number,
    recipient_name,
    quantity,
    original_sku,
    pack_key,
    component_candidates,
    tag_id,
    process_no,
    stock_levels,
    pack_names_map,
    custom_label_map,
    missing_label_ids,
    log,
):
    """Return (ok, in_rows, out_rows, missing_rows) for one pack line."""
    component_levels = {}
    effective_components = []
    any_missing = False
    insufficient = False
    pack_nf_status = STATUS_NOT_FOUND
    pack_nf_stock_id = ""
    for comp_entry in component_candidates:
        comp_original = comp_entry.get("sku") or ""
        level, effective, _marketplace, used_fallback = resolve_stock_level(
            comp_original, stock_levels, custom_label_map
        )
        component_levels[effective] = level
        effective_components.append(effective)
        if used_fallback:
            log(f"[CUSTOM LABEL] Component {comp_original} -> stock ID {effective}")
        if level == -1:
            if not any_missing:
                pack_nf_status = not_found_status(
                    comp_original,
                    custom_label_map,
                    missing_label_ids,
                    used_fallback=used_fallback,
                )
                pack_nf_stock_id = effective if used_fallback else ""
            any_missing = True
        elif level < quantity:
            insufficient = True

    if any_missing:
        log(
            f"[ERROR] Pack components missing in stock file: Order {order_number}, "
            f"Pack {pack_key} -> {component_candidates} ({pack_nf_status})"
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
                    item_sku=pack_key,
                    stock_id=pack_nf_stock_id,
                    status=pack_nf_status,
                )
            ],
        )
    if insufficient:
        log(
            f"[WARNING] Pack insufficient stock: Order {order_number}, Pack {pack_key} "
            f"(Need {quantity} each) -> {component_levels}"
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
                    0,
                    process_no,
                    item_sku=pack_key,
                )
            ],
            [],
        )
    components_joined = ",".join(effective_components)
    colours_joined = ",".join([c.get("colour", "") for c in component_candidates])
    pack_name_value = pack_names_map.get(pack_key, "")
    return (
        True,
        [
            [
                order_number,
                recipient_name,
                quantity,
                pack_key,
                pack_name_value,
                tag_id,
                1,
                components_joined,
                colours_joined,
                process_no,
                "",
            ]
        ],
        [],
        [],
    )
