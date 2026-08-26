"""Flatten ShipStation orders into a Step-1-compatible CSV."""

from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import Any, Callable

from scripts.pipeline_runtime.runner_utils import (
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
DEFAULT_INPUT_ROOT = wh.packing_input_dir()


def input_csv_path_for_batch(
    date_dd_mm_yyyy: str,
    shift_label: str,
    process_number: str,
    *,
    input_root: str | Path | None = None,
) -> Path:
    """Return Input/{date}/{shift} Shift/{process}.csv."""
    root = Path(input_root) if input_root else DEFAULT_INPUT_ROOT
    process = _sanitize_process_for_filename((process_number or "").strip())
    shift_part = _shift_subdir_name((shift_label or "").strip())
    return root / date_dd_mm_yyyy.strip() / shift_part / f"{process}.csv"


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


def fetch_tag_orders_to_csv(
    *,
    tag_id: int,
    tag_name: str,
    date_dd_mm_yyyy: str,
    shift_label: str,
    process_number: str,
    input_root: str | Path | None = None,
    client: ShipStationClient | None = None,
    log: LogFn | None = None,
) -> Path:
    """
    Fetch awaiting_shipment orders for tag, write Input/{date}/{shift} Shift/{process}.csv.

    Orders with the ``post-order-designs`` tag are excluded.

    Raises ShipStationError / ValueError / FileNotFoundError on failure.
    Raises ShipStationError if zero line-item rows are produced.
    """
    log_fn = log or (lambda _m: None)
    ss = client or ShipStationClient(load_shipstation_credentials(), log=log_fn)

    # Prefer a full tag map so Tags column includes all order tags (e.g. Prime).
    tag_id_to_name: dict[int, str] = {}
    try:
        for t in ss.list_tags():
            tag_id_to_name[int(t["tagId"])] = str(t.get("name") or "")
    except ShipStationError:
        tag_id_to_name[int(tag_id)] = (tag_name or "").strip()

    if int(tag_id) not in tag_id_to_name and (tag_name or "").strip():
        tag_id_to_name[int(tag_id)] = tag_name.strip()

    display = (tag_name or tag_id_to_name.get(int(tag_id)) or str(tag_id)).strip()
    log_fn(f"Fetching ShipStation orders for tag '{display}' (awaiting_shipment)…")
    orders = ss.list_orders_by_tag(int(tag_id), order_status="awaiting_shipment")
    skipped = sum(
        1 for o in orders if _order_has_excluded_tag(o.get("tagIds"), tag_id_to_name)
    )
    if skipped:
        log_fn(
            f"Skipping {skipped} order(s) tagged '{EXCLUDE_TAG_NAME}'."
        )
    rows = orders_to_rows(orders, tag_id_to_name)
    if not rows:
        raise ShipStationError(
            f"No awaiting-shipment line items found for tag '{display}' "
            f"(after excluding '{EXCLUDE_TAG_NAME}')."
        )

    out_path = input_csv_path_for_batch(
        date_dd_mm_yyyy, shift_label, process_number, input_root=input_root
    )
    write_orders_csv(rows, out_path)
    kept_orders = len(orders) - skipped
    log_fn(
        f"Wrote {len(rows)} row(s) from {kept_orders} order(s) "
        f"({skipped} excluded) to {out_path}"
    )
    return out_path
