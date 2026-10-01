"""Flatten ShipStation orders into a Step-1-compatible CSV."""

from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Any, Callable

from pipeline_runtime.runner_utils import (
    _sanitize_process_for_filename,
    _shift_subdir_name,
)

from .client import ShipStationClient, ShipStationError
from .credentials import load_shipstation_credentials

LogFn = Callable[[str], None]

# Orders carrying this ShipStation tag name are excluded from fetch/CSV.
EXCLUDE_TAG_NAME = "post-order-designs"
EXCLUDE_TAG_NAME_FOLD = EXCLUDE_TAG_NAME.casefold()

# Headers that fetch_input_csv aliases already accept.
CSV_FIELDNAMES = [
    "Order #",
    "Ship By",
    "Quantity",
    "Item - Image URL",
    "Gift - Message",
    "Notes - From Buyer",
    "Item SKU",
    "Item Name",
    "Item - Options",
    "Recipient",
    "Tags",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402
from pipeline_shipstation.orders_to_csv_impl import fetch_tag_orders_to_csv, input_csv_path_for_batch
DEFAULT_INPUT_ROOT = wh.packing_input_dir()


def _format_options(options: Any) -> str:
    if not isinstance(options, list):
        return ""
    parts: list[str] = []
    for opt in options:
        if not isinstance(opt, dict):
            continue
        name = str(opt.get("name") or "").strip()
        value = str(opt.get("value") or "").strip()
        if name and value:
            parts.append(f"{name}: {value}")
        elif value:
            parts.append(value)
        elif name:
            parts.append(name)
    return ", ".join(parts)


def _tags_string(tag_ids: Any, tag_id_to_name: dict[int, str]) -> str:
    if not isinstance(tag_ids, list):
        return ""
    names: list[str] = []
    for tid in tag_ids:
        try:
            key = int(tid)
        except (TypeError, ValueError):
            continue
        name = tag_id_to_name.get(key, "")
        if name:
            names.append(name)
    return ", ".join(names)


def _order_has_excluded_tag(tag_ids: Any, tag_id_to_name: dict[int, str]) -> bool:
    """True if any of the order's tags resolves to post-order-designs."""
    if not isinstance(tag_ids, list):
        return False
    for tid in tag_ids:
        try:
            key = int(tid)
        except (TypeError, ValueError):
            continue
        name = str(tag_id_to_name.get(key) or "").strip()
        if name.casefold() == EXCLUDE_TAG_NAME_FOLD:
            return True
    return False


def _ship_to_name(order: dict[str, Any]) -> str:
    ship_to = order.get("shipTo")
    if isinstance(ship_to, dict):
        return str(ship_to.get("name") or "").strip()
    return ""


def orders_to_rows(
    orders: list[dict[str, Any]],
    tag_id_to_name: dict[int, str],
) -> list[dict[str, str]]:
    """One CSV row per non-discount, non-adjustment line item.

    Orders tagged ``post-order-designs`` are skipped entirely.
    """
    rows: list[dict[str, str]] = []
    for order in orders:
        if _order_has_excluded_tag(order.get("tagIds"), tag_id_to_name):
            continue
        order_number = str(order.get("orderNumber") or "").strip()
        ship_by = str(order.get("shipByDate") or "").strip()
        gift = str(order.get("giftMessage") or "").strip()
        buyer_notes = str(order.get("customerNotes") or "").strip()
        recipient = _ship_to_name(order)
        tags = _tags_string(order.get("tagIds"), tag_id_to_name)
        items = order.get("items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            if item.get("adjustment") is True:
                continue
            item_name = str(item.get("name") or "").strip()
            if "discount" in item_name.casefold():
                continue
            qty = item.get("quantity")
            qty_str = "" if qty is None else str(qty).strip()
            rows.append(
                {
                    "Order #": order_number,
                    "Ship By": ship_by,
                    "Quantity": qty_str,
                    "Item - Image URL": str(item.get("imageUrl") or "").strip(),
                    "Gift - Message": gift,
                    "Notes - From Buyer": buyer_notes,
                    "Item SKU": str(item.get("sku") or "").strip(),
                    "Item Name": item_name,
                    "Item - Options": _format_options(item.get("options")),
                    "Recipient": recipient,
                    "Tags": tags,
                }
            )
    return rows


def write_orders_csv(rows: list[dict[str, str]], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return path


