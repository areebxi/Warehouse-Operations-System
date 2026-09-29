"""Write per-date leftover batch criteria (B1 / B2 / …).

Same columns as fixed_batches.csv. Live folder:
database/order-grouping-sorter/leftover_batches/{YYYY-MM-DD}.csv
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TYPE_CHECKING

import shared.paths as wh

from fixed_batches import fixed_batch_codes

if TYPE_CHECKING:
    from grouping import ProcessBin, SortResult

# Keep in lockstep with database/order-grouping-sorter/fixed_batches.csv
LEFTOVER_HEADER = [
    "batch_code",
    "name",
    "order-status",
    "ship-by-date",
    "product-finish",
    "order-source",
    "design-grouping",
    "shipping-service",
    "printing-method",
    "customised",
    "customisation-type",
    "print-size",
    "print-position",
    "supply-method",
    "supplier",
    "package-type",
    "category",
    "product-type",
    "product-style",
    "department",
    "brand",
    "size",
    "color",
    "destination",
    "item-name-contains",
    "sku-contains",
    "item-name-not-contains",
    "sku-not-contains",
    "notes",
]

_SUPPLY_DISPLAY = {
    "warehouse_stock": "Warehouse Stock",
    "supplier_on_demand": "SUPPLY ON DEMAND",
    "in_house_manufacture": "In House Manufacture",
}

_CHAIN_COLS = (
    "category",
    "product-type",
    "product-style",
    "department",
    "brand",
    "size",
    "color",
)


def _slot(slots: list[str], i: int, default: str = "x") -> str:
    if i < len(slots) and slots[i]:
        return slots[i]
    return default


def _supply_cell(slot: str) -> str:
    if not slot or slot == "x":
        return "x"
    return _SUPPLY_DISPLAY.get(slot, slot.replace("_", " "))


def leftover_bins(bins: list) -> list:
    """Bins that received leftover B1/B2… (not fixed-batch codes)."""
    reserved = fixed_batch_codes()
    out = []
    for b in bins:
        if not b.orders or not b.floor_code:
            continue
        if b.floor_code in reserved:
            continue
        if not b.group_slots:
            continue
        out.append(b)
    return out


def row_for_bin(b) -> dict[str, str]:
    slots = list(b.group_slots)
    ship = b.ship_by_slot or "x"
    o = len(b.orders)
    li = sum(len(ord_.lines) for ord_ in b.orders)
    u = sum(ord_.units for ord_ in b.orders)
    chain_start = 12
    chain = {col: _slot(slots, chain_start + i) for i, col in enumerate(_CHAIN_COLS)}
    return {
        "batch_code": b.floor_code,
        "name": f"Leftover {b.floor_code}",
        "order-status": "awaiting_shipment",
        "ship-by-date": ship,
        "product-finish": _slot(slots, 0),
        "order-source": _slot(slots, 1),
        "design-grouping": _slot(slots, 2),
        "shipping-service": _slot(slots, 3),
        "printing-method": _slot(slots, 4),
        "customised": _slot(slots, 5),
        "customisation-type": _slot(slots, 6),
        "print-size": _slot(slots, 7),
        "print-position": _slot(slots, 8),
        "supply-method": _supply_cell(_slot(slots, 9)),
        "supplier": _slot(slots, 10),
        "package-type": _slot(slots, 11),
        **chain,
        "destination": "x",
        "item-name-contains": "x",
        "sku-contains": "x",
        "item-name-not-contains": "x",
        "sku-not-contains": "x",
        "notes": f"filename={b.process_name}; orders={o} lines={li} units={u}",
    }


def write_leftover_batches_csv(
    result,
    *,
    path: Path | None = None,
) -> Path:
    """Overwrite that run date's leftover CSV. Header-only when no leftovers."""
    dest = Path(path) if path else wh.sorter_leftover_batches_path(result.run_date)
    dest.parent.mkdir(parents=True, exist_ok=True)
    rows = [row_for_bin(b) for b in leftover_bins(result.bins)]
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LEFTOVER_HEADER)
        w.writeheader()
        w.writerows(rows)
    return dest
