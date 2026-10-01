"""Grouping models, constants, parsers."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from shared.areeb_taxonomy import cell

EXCLUDE_TAG = "post-order-designs"
RESEND_TAG = "1014-ALL-RESEND"
RESEND_FILE = "RESEND"
UNMATCHED_FILE = "UNMATCHED"
PRIME_TAG = "amazon prime order"
# Exact ShipStation tag (Tags.xlsx). Designs ready on the floor.
PERSONALISED_READY_TAG = "1004- Personalised Design-Ready-"
FAWAD_STORE = "mas clothing"
EXCLUDE_STORES = frozenset({"dtfocean.co.uk wp"})
PLAIN_MARKERS = ("plainlg", "plain")

SHIFT1_SPLIT_ORDERS = 300
SHIFT_PER_RUN = False

COLOUR_GROUP_MIN = 3
PART_CAP = 50

WAREHOUSE_STOCK = "Warehouse Stock"
IN_HOUSE = "In House Manufacture"
ON_DEMAND = "Supplier On Demand"

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

# Graph 30-chain: peel a value only when that pile has >=30 units of it.
CHAIN_30: tuple[tuple[str, int], ...] = (
    ("category", 30),
    ("product-type", 30),
    ("product-style", 30),
    ("department", 30),
    ("brand", 30),
    ("size", 30),
    ("colour", 30),
)

ATTR_FIELD = {
    "category": "category",
    "product-type": "product_type",
    "product-style": "product_style",
    "department": "department",
    "brand": "brand",
    "size": "size",
    "colour": "colour",
}
def _fold(value: object) -> str:
    return cell(value).casefold()


def sku_is_plain_override(sku: object) -> bool:
    s = _fold(sku)
    return any(m in s for m in PLAIN_MARKERS)


def parse_qty(value: object) -> int:
    s = cell(value)
    if not s:
        return 0
    try:
        n = int(float(s))
    except ValueError:
        return 0
    return n if n > 0 else 0


def parse_ship_by(raw: object) -> Optional[date]:
    s = cell(raw)
    if not s:
        return None
    if len(s) >= 10 and s[4] == "-" and s[7] == "-":
        try:
            return date.fromisoformat(s[:10])
        except ValueError:
            return None
    return None


def slotify(value: object) -> str:
    s = _fold(value).replace(" ", "_")
    chars: list[str] = []
    for ch in s:
        if ch.isalnum() or ch in "-_":
            chars.append(ch)
        else:
            chars.append("_")
    out = "".join(chars).strip("_")
    while "__" in out:
        out = out.replace("__", "_")
    return out or "x"


def date_slot(ship: date, run: date) -> str:
    """Graph ship-by-date is binary: today (due/run date) or future."""
    return "today" if ship <= run else "future"


@dataclass
class LineAttrs:
    sku: str
    qty: int
    finish: Optional[str]
    source: Optional[str]
    supply_method: str = ""
    supplier: str = ""
    printing_type: str = ""
    customise: str = ""
    category: str = ""
    product_type: str = ""
    product_style: str = ""
    department: str = ""
    brand: str = ""
    size: str = ""
    colour: str = ""
    item_name: str = ""
    gender_apparel: str = ""


@dataclass
class Order:
    number: str
    ship_by_raw: str
    ship_by: Optional[date]
    tag_names: list[str]
    store_name: str
    lines: list[LineAttrs] = field(default_factory=list)
    ship_country: str = ""
    csv_rows: list[dict[str, str]] = field(default_factory=list)
    unmatched_reason: str = ""
    finish: str = ""
    left: list[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def units(self) -> int:
        return sum(ln.qty for ln in self.lines)


@dataclass
class ProcessPart:
    n: int
    orders: list[Order]


@dataclass
class ProcessBin:
    shift_slot: str
    shift_folder: str
    process_name: str
    orders: list[Order]
    parts: list[ProcessPart] = field(default_factory=list)
    floor_code: str = ""
    # Leftover Graph + 30-chain slots (fixed batches leave empty).
    group_slots: list[str] = field(default_factory=list)
    ship_by_slot: str = ""  # today | future | x (mixed / don't care)


@dataclass
class SortResult:
    run_date: date
    skipped_post: int
    empty_skipped: int
    resend: list[Order]
    unmatched: list[Order]
    held: list[Order]
    bins: list[ProcessBin]
    pool_orders: int
    shift_slot: str = "1st"
    shift_folder: str = "1st Shift"
    mix_today_future: bool = False
    today_orders: int = 0
    eligible_orders: int = 0
    skipped_already_written: int = 0
    skipped_excluded_store: int = 0
    # "B5500 over B10" → orders that also satisfied a lower fixed batch.
    overlaps: Counter = field(default_factory=Counter)


