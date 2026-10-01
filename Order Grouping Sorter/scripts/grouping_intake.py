"""ShipStation raw orders → Order + CSV rows."""
from __future__ import annotations

from typing import Any, Iterable

from shared.areeb_taxonomy import cell

from catalogs import Catalogs
from grouping_finish import attrs_for_sku
from grouping_models import (EXCLUDE_STORES, EXCLUDE_TAG, LineAttrs, Order, _fold, parse_qty, parse_ship_by)

def _item_is_skipped(item: dict[str, Any]) -> bool:
    if item.get("adjustment") is True:
        return True
    name = _fold(item.get("name"))
    return "discount" in name


def _format_options(options: Any) -> str:
    """Packing current-view Item - Options. Do not import Packing internals."""
    if not isinstance(options, list):
        return ""
    parts: list[str] = []
    for opt in options:
        if not isinstance(opt, dict):
            continue
        name = cell(opt.get("name"))
        value = cell(opt.get("value"))
        if name and value:
            parts.append(f"{name}: {value}")
        elif value:
            parts.append(value)
        elif name:
            parts.append(name)
    return ", ".join(parts)


def _ship_to_name(raw: dict[str, Any]) -> str:
    ship_to = raw.get("shipTo")
    if isinstance(ship_to, dict):
        return cell(ship_to.get("name"))
    return ""


def _item_csv_row(raw: dict[str, Any], item: dict[str, Any], tags: str) -> dict[str, str]:
    qty = item.get("quantity")
    qty_str = "" if qty is None else str(qty).strip()
    return {
        "Order #": cell(raw.get("orderNumber")),
        "Ship By": cell(raw.get("shipByDate")),
        "Quantity": qty_str,
        "Item - Image URL": cell(item.get("imageUrl")),
        "Gift - Message": cell(raw.get("giftMessage")),
        "Notes - From Buyer": cell(raw.get("customerNotes")),
        "Item SKU": cell(item.get("sku")),
        "Item Name": cell(item.get("name")),
        "Item - Options": _format_options(item.get("options")),
        "Recipient": _ship_to_name(raw),
        "Tags": tags,
    }


def _tag_names(tag_ids: Any, tag_id_to_name: dict[int, str]) -> list[str]:
    if not isinstance(tag_ids, list):
        return []
    names: list[str] = []
    for tid in tag_ids:
        try:
            key = int(tid)
        except (TypeError, ValueError):
            continue
        name = cell(tag_id_to_name.get(key))
        if name:
            names.append(name)
    return names


def _has_tag(names: Iterable[str], want: str) -> bool:
    w = want.strip().casefold()
    return any(n.strip().casefold() == w for n in names)


def _order_is_customised(order: Order) -> bool:
    """Printed majority-Customise pile (six-field slot), not plain `x`."""
    return len(order.left) > 5 and order.left[5] == "customised"


def _store_name(order: dict[str, Any], store_id_to_name: dict[int, str]) -> str:
    adv = order.get("advancedOptions")
    sid = None
    if isinstance(adv, dict):
        sid = adv.get("storeId")
    if sid is None:
        sid = order.get("storeId")
    try:
        return cell(store_id_to_name.get(int(sid)))
    except (TypeError, ValueError):
        return ""


def orders_from_ss(
    raw_orders: list[dict[str, Any]],
    tag_id_to_name: dict[int, str],
    store_id_to_name: dict[int, str],
    catalogs: Catalogs,
) -> tuple[list[Order], int, int, int]:
    """Skip post-order-designs, excluded stores, and discount/adjustment lines."""
    out: list[Order] = []
    skipped_post = 0
    skipped_excluded_store = 0
    empty_skipped = 0
    for raw in raw_orders:
        names = _tag_names(raw.get("tagIds"), tag_id_to_name)
        if _has_tag(names, EXCLUDE_TAG):
            skipped_post += 1
            continue
        store_name = _store_name(raw, store_id_to_name)
        if _fold(store_name) in EXCLUDE_STORES:
            skipped_excluded_store += 1
            continue
        items = raw.get("items")
        if not isinstance(items, list):
            empty_skipped += 1
            continue
        lines: list[LineAttrs] = []
        csv_rows: list[dict[str, str]] = []
        tags_str = ", ".join(names)
        for item in items:
            if not isinstance(item, dict) or _item_is_skipped(item):
                continue
            sku = cell(item.get("sku"))
            qty = parse_qty(item.get("quantity"))
            item_name = cell(item.get("name"))
            lines.append(attrs_for_sku(sku, qty, catalogs, item_name=item_name))
            csv_rows.append(_item_csv_row(raw, item, tags_str))
        if not lines:
            empty_skipped += 1
            continue
        out.append(
            Order(
                number=cell(raw.get("orderNumber")),
                ship_by_raw=cell(raw.get("shipByDate")),
                ship_by=parse_ship_by(raw.get("shipByDate")),
                tag_names=names,
                store_name=store_name,
                lines=lines,
                csv_rows=csv_rows,
                ship_country=cell((raw.get("shipTo") or {}).get("country")),
            )
        )
    return out, skipped_post, empty_skipped, skipped_excluded_store


