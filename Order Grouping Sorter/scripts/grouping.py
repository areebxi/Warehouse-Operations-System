"""Order Grouping Sorter — grouping + Packing Input CSV write.

Locks: order-grouping-locks.md. SKU keys are not universal resolve_label.
"""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from shared import paths as wh
from shared.areeb_taxonomy import cell

from catalogs import SRC_PACKS, Catalogs
from fixed_batches import (
    FixedBatchRow,
    cares,
    fixed_batch_codes,
    fixed_batch_table,
    reserved_batch_nums,
)

EXCLUDE_TAG = "post-order-designs"
RESEND_TAG = "1014-ALL-RESEND"
RESEND_FILE = "RESEND"
UNMATCHED_FILE = "UNMATCHED"
PRIME_TAG = "amazon prime order"
# Exact ShipStation tag name (Tags.xlsx / list_tags). Designs ready on the floor.
PERSONALISED_READY_TAG = "1004- Personalised Design-Ready-"
FAWAD_STORE = "mas clothing"
# Not processed in this warehouse system (supervisor 2026-09-24).
EXCLUDE_STORES = frozenset({"dtfocean.co.uk wp"})
PLAIN_MARKERS = ("plainlg", "plain")

# Hashim 2026-09-14 (#037): Shift 1 volume above this (orders) → split today vs later dates.
# Do not dump overflow into Shift 2/3 as caps.
SHIFT1_SPLIT_ORDERS = 300
# ponytail: testing rewrites 1st Shift each --run. Production later: nth --run of the day = nth shift.
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

# Graph 30-chain, same for plain and printed. Peel a value into a new
# process file only when that pile has >=30 units of it. Under 30, stay
# on the parent (e.g. 29 short-sleeve t-shirts = all departments together).
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


def finish_for_sku(sku: object, catalogs: Catalogs) -> Optional[str]:
    if sku_is_plain_override(sku):
        return "plain"
    if catalogs.lookup_cl(sku) is not None:
        return "printed"
    if catalogs.lookup_plain(sku) is not None:
        return "plain"
    if catalogs.lookup_packs(sku) is not None:
        return "plain"
    return None


def _row_brand_size_colour(source: str, row: Mapping[str, str]) -> tuple[str, str, str]:
    if source == SRC_PACKS:
        return cell(row.get("Brand Name")), cell(row.get("Pack Size")), ""
    return cell(row.get("Brand")), cell(row.get("Size")), cell(row.get("Colour"))


def attrs_for_sku(
    sku: object, qty: int, catalogs: Catalogs, *, item_name: str = ""
) -> LineAttrs:
    finish = finish_for_sku(sku, catalogs)
    source, row = catalogs.attribute_row(sku)
    if row is None:
        return LineAttrs(
            sku=cell(sku), qty=qty, finish=finish, source=None, item_name=item_name
        )
    brand, size, colour = _row_brand_size_colour(source or "", row)
    return LineAttrs(
        sku=cell(sku),
        qty=qty,
        finish=finish,
        source=source,
        supply_method=cell(row.get("Supply Method")),
        supplier=cell(row.get("Supplier Name")),
        printing_type=cell(row.get("Printing Type")),
        customise=cell(row.get("Customise")),
        category=cell(row.get("Category (Areeb)")),
        product_type=cell(row.get("Product Type (Areeb)")),
        product_style=cell(row.get("Product Style (Areeb)")),
        department=cell(row.get("Department (Areeb)")),
        brand=brand,
        size=size,
        colour=colour,
        item_name=item_name,
        gender_apparel=cell(row.get("Gender Apparel")),
    )


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


def order_source_slot(store_name: str) -> str:
    if _fold(store_name) == FAWAD_STORE:
        return "fawad"
    return "own"


def prime_slot(tag_names: list[str]) -> str:
    return "prime" if _has_tag(tag_names, PRIME_TAG) else "non-prime"


PERSONALISED_NAME_NEEDLES = ("personali", "custom")


def _line_is_personalised(ln: LineAttrs) -> bool:
    """Supervisor 2026-09-28: CL Customise = Yes OR Item Name contains Personali / Custom."""
    if _fold(ln.customise) == "yes":
        return True
    name = _fold(ln.item_name)
    return any(n in name for n in PERSONALISED_NAME_NEEDLES)


def mixed_customised_slot(printed: list[LineAttrs]) -> str:
    """Supervisor 2026-09-17: mixed P/R → majority printed units; tie → readymade."""
    p = 0
    r = 0
    for ln in printed:
        if _line_is_personalised(ln):
            p += ln.qty
        else:
            r += ln.qty
    if p > r:
        return "customised"
    return "readymade"


def _unanimous(values: list[str]) -> Optional[str]:
    nonempty = [v for v in values if v]
    if not nonempty:
        return None
    first = nonempty[0]
    if all(v == first for v in nonempty):
        return first
    return None


def _chain_lines(order: Order) -> list[LineAttrs]:
    """After printed-wins, 30-chain follows printed lines so mixed finish can stay printed."""
    if order.finish == "printed":
        printed = _printed_lines(order)
        if printed:
            return printed
    return list(order.lines)


def _field_values(order: Order, field: str) -> list[str]:
    attr = ATTR_FIELD[field]
    vals: list[str] = []
    for ln in _chain_lines(order):
        if field == "colour" and ln.source == SRC_PACKS:
            continue
        vals.append(getattr(ln, attr))
    return vals


def order_skips_colour(order: Order) -> bool:
    lines = _chain_lines(order)
    return bool(lines) and all(ln.source == SRC_PACKS for ln in lines)


def _printed_lines(order: Order) -> list[LineAttrs]:
    return [ln for ln in order.lines if ln.finish == "printed"]


def _order_finish(order: Order) -> Optional[str]:
    finishes = [ln.finish for ln in order.lines]
    if any(f is None for f in finishes):
        return None
    if "printed" in finishes:
        return "printed"
    return "plain"


def _printed_tail(supply: str) -> str:
    """warehouse-stock / in-house share supplier slot x; on-demand splits supplier."""
    if supply == ON_DEMAND:
        return "on-demand"
    return "warehouse-stock"


def left_slots(order: Order, finish: str) -> Optional[list[str]]:
    """Graph slots after date + shift. None → unmatched (reason set)."""
    supply_vals = [ln.supply_method for ln in order.lines]
    if any(not v for v in supply_vals):
        order.unmatched_reason = "blank supply-method"
        return None
    supply = _unanimous(supply_vals)
    if supply is None:
        # Supervisor 2026-09-22: mixed supply → on-demand (that item arrives later).
        supply = ON_DEMAND
    if finish == "plain" and supply == IN_HOUSE:
        order.unmatched_reason = "plain in-house"
        return None

    supplier_flag_value = True
    if finish == "printed" and _printed_tail(supply) == "warehouse-stock":
        supplier_flag_value = False

    if supplier_flag_value:
        sup_vals = [ln.supplier for ln in order.lines]
        if any(not v for v in sup_vals):
            order.unmatched_reason = "blank supplier"
            return None
        supplier = _unanimous(sup_vals)
        if supplier is None:
            order.unmatched_reason = "mixed supplier"
            return None
        supplier_slot = slotify(supplier)
    else:
        supplier_slot = "x"

    if finish == "printed":
        printed = _printed_lines(order)
        if not printed:
            order.unmatched_reason = "printed-wins with no printed lines"
            return None
        pt_vals = [ln.printing_type for ln in printed]
        if any(not v for v in pt_vals):
            order.unmatched_reason = "blank printing-method"
            return None
        printing = _unanimous(pt_vals)
        if printing is None:
            order.unmatched_reason = "mixed printing-method"
            return None
        print_slot = slotify(printing)
        cust_slot = mixed_customised_slot(printed)
    else:
        print_slot = "x"
        cust_slot = "x"

    return [
        finish,
        order_source_slot(order.store_name),
        "x",  # design-grouping
        prime_slot(order.tag_names),
        print_slot,
        cust_slot,
        "x",  # customisation-type
        "x",  # print-size
        "x",  # print-position
        slotify(supply),
        supplier_slot,
        "x",  # package-type
    ]


def _mark_unmatched(order: Order, reason: str) -> None:
    if not order.unmatched_reason:
        order.unmatched_reason = reason


def _split_flag1(orders: list[Order], field: str) -> tuple[list[Order], dict[str, list[Order]]]:
    unmatched: list[Order] = []
    groups: dict[str, list[Order]] = defaultdict(list)
    for order in orders:
        vals = _field_values(order, field)
        if not vals or any(not v for v in vals):
            _mark_unmatched(order, f"blank {field}")
            unmatched.append(order)
            continue
        u = _unanimous(vals)
        if u is None:
            _mark_unmatched(order, f"mixed {field}")
            unmatched.append(order)
            continue
        groups[u].append(order)
    return unmatched, groups


def _split_flag30(orders: list[Order], field: str) -> tuple[list[Order], dict[str, list[Order]], list[Order]]:
    # ponytail: flag 30 blank stays in leftover (parent), same as mixed.
    # Peel only at >=30 of a named value. In-house Brand is intentionally empty;
    # unmatched here dumped every iron-on/sticker. Flag 1 still unmatcheds blank.
    unmatched: list[Order] = []
    unanimous: dict[str, list[Order]] = defaultdict(list)
    mixed: list[Order] = []
    for order in orders:
        vals = _field_values(order, field)
        if any(not v for v in vals):
            mixed.append(order)
            continue
        u = _unanimous(vals) if vals else None
        if u is None:
            mixed.append(order)
            continue
        unanimous[u].append(order)
    return unmatched, unanimous, mixed


def peel_chain(
    orders: list[Order],
    chain: tuple[tuple[str, int], ...],
    prefix: list[str],
    unmatched: list[Order],
) -> list[tuple[list[str], list[Order]]]:
    if not orders:
        return []
    if not chain:
        return [(prefix, orders)]
    field, flag = chain[0]
    rest = chain[1:]

    if field == "colour":
        skip = [o for o in orders if order_skips_colour(o)]
        need = [o for o in orders if not order_skips_colour(o)]
        out: list[tuple[list[str], list[Order]]] = []
        if skip:
            out.extend(peel_chain(skip, rest, prefix, unmatched))
        if need:
            out.extend(_peel_one(need, field, flag, rest, prefix, unmatched))
        return out
    return _peel_one(orders, field, flag, rest, prefix, unmatched)


def _peel_one(
    orders: list[Order],
    field: str,
    flag: int,
    rest: tuple[tuple[str, int], ...],
    prefix: list[str],
    unmatched: list[Order],
) -> list[tuple[list[str], list[Order]]]:
    if flag == 0:
        return peel_chain(orders, rest, prefix + ["x"], unmatched)
    if flag == 1:
        bad, groups = _split_flag1(orders, field)
        unmatched.extend(bad)
        out: list[tuple[list[str], list[Order]]] = []
        for val, group in groups.items():
            out.extend(peel_chain(group, rest, prefix + [slotify(val)], unmatched))
        return out
    # flag 30
    bad, unanimous, mixed = _split_flag30(orders, field)
    unmatched.extend(bad)
    leftover: list[Order] = list(mixed)
    out: list[tuple[list[str], list[Order]]] = []
    for val, group in unanimous.items():
        units = sum(o.units for o in group)
        if units >= 30:
            out.extend(peel_chain(group, rest, prefix + [slotify(val)], unmatched))
        else:
            leftover.extend(group)
    if leftover:
        out.extend(peel_chain(leftover, rest, prefix, unmatched))
    return out


def _process_name(date_s: str, shift_s: str, slots: list[str]) -> str:
    """Internal leftover sort key. Not the on-disk filename."""
    return "-".join([date_s, shift_s, *slots])


FILENAME_SUPPLY = {
    slotify(WAREHOUSE_STOCK): "WAREHOUSE STOCK",
    slotify(ON_DEMAND): "SUPPLY ON DEMAND",
    slotify(IN_HOUSE): "IN HOUSE MANUFACTURE",
}

# Fixed-batch codes + criteria: database/order-grouping-sorter/fixed_batches.csv
# (loaded via fixed_batches.py). Shift is only S1/S2/S3 — never remap B100→B200.
FIXED_BATCH_CODES: frozenset[str] = fixed_batch_codes()
NAMED_CODES = FIXED_BATCH_CODES  # back-compat alias
RESERVED_BATCH_NUMS: frozenset[int] = reserved_batch_nums()


def next_leftover_batch_codes(count: int) -> list[str]:
    """B1, B2, … skipping fixed-batch numbers (B80, B100, B1000, …)."""
    out: list[str] = []
    n = 1
    while len(out) < count:
        if n not in RESERVED_BATCH_NUMS:
            out.append(f"B{n}")
        n += 1
    return out


def next_plain_batch_codes(count: int) -> list[str]:
    """Plain batches 1, 2, …: B2000, B2100, B2200, B2500, B2600, B2700, … (skip reserved)."""
    out: list[str] = []
    n = 2000
    while len(out) < count:
        if n not in RESERVED_BATCH_NUMS:
            out.append(f"B{n}")
        n += 100
    return out


def _sku_parts(sku: str) -> set[str]:
    return {p.strip().casefold() for p in (sku or "").split("-")}


def _needles(spec: str) -> list[str]:
    return [n.strip() for n in spec.split(";") if n.strip()]


def _sku_hit(sku: str, needle: str) -> bool:
    """`=M61` = whole dash-separated SKU part; else case-insensitive substring."""
    if needle.startswith("="):
        return needle[1:].casefold() in _sku_parts(sku)
    return needle.casefold() in _fold(sku)


def _order_sku_any(order: Order, spec: str) -> bool:
    needles = _needles(spec)
    return any(_sku_hit(ln.sku, n) for ln in order.lines for n in needles)


def _order_name_any(order: Order, spec: str) -> bool:
    return any(_order_has_item_name_contains(order, n) for n in _needles(spec))


def _destination_slot(order: Order) -> str:
    """Blank country is not guessed international."""
    c = cell(order.ship_country).upper()
    return "international" if c and c != "GB" else "uk"


BABYSUIT_STYLES = frozenset({"c800t", "c8020t", "c8030t"})


def _line_is_mug(ln: LineAttrs) -> bool:
    return (
        "mug" in _fold(ln.sku)
        or "m61" in _sku_parts(ln.sku)
        or _fold(ln.printing_type) == "sublimation"
    )


def _line_is_babysuit(ln: LineAttrs) -> bool:
    return bool(BABYSUIT_STYLES & _sku_parts(ln.sku)) or _fold(ln.product_type) == "body suit"


def _line_is_ss_fotl(ln: LineAttrs) -> bool:
    if _fold(ln.supply_method) != _fold(WAREHOUSE_STOCK):
        return False
    if _fold(ln.category) != "t-shirts":
        return False
    pt = _fold(ln.product_type)
    if not pt:
        return False
    if "long sleeve" in pt or "longsleeve" in pt:
        return False
    return "short sleeve" in pt or "t-shirt" in pt


def _line_is_iron_on(ln: LineAttrs) -> bool:
    """Catalog iron-on OR Item SKU contains IronOn (supervisor 2026-09-28). Never sticker."""
    cat = _fold(ln.category)
    pt = _fold(ln.product_type)
    if "sticker" in cat or "sticker" in pt or "sticker" in _fold(ln.sku):
        return False
    if "ironon" in _fold(ln.sku):
        return True
    if _fold(ln.supply_method) != _fold(IN_HOUSE):
        return False
    return cat == "iron-on" or "iron-on" in pt or "iron on" in pt


def _has_gildan_5000_token(text: str) -> bool:
    """Style 5000 / G5000 as a token — not substring of 15000 (FOTL UID false hit)."""
    for part in re.split(r"[^A-Za-z0-9]+", text or ""):
        p = part.casefold()
        if p in {"5000", "g5000"}:
            return True
    return False


def _line_is_gildan_tee(ln: LineAttrs) -> bool:
    """B40: Brand Gildan T-Shirts, or style 5000/G5000 in SKU / Gender Apparel."""
    if _fold(ln.category) != "t-shirts":
        return False
    if _fold(ln.brand) == "gildan":
        return True
    return _has_gildan_5000_token(ln.sku) or _has_gildan_5000_token(ln.gender_apparel)


def _all_chain(order: Order, pred) -> bool:
    lines = _chain_lines(order)
    return bool(lines) and all(pred(ln) for ln in lines)


def _order_status_slot(order: Order) -> str:
    """Graph order-status: resend tag wins; else awaiting_shipment (pool)."""
    if _has_tag(order.tag_names, RESEND_TAG):
        return "resend"
    return "awaiting_shipment"


def _norm_item_text(s: str) -> str:
    """Casefold; treat hyphens as spaces so Glow-in-the-Dark ≈ Glow In The Dark."""
    return " ".join(_fold(s).replace("-", " ").split())


def _order_has_item_name_contains(order: Order, needle: str) -> bool:
    n = _norm_item_text(needle)
    if not n:
        return False
    for ln in order.lines:
        if n in _norm_item_text(ln.item_name):
            return True
    for row in order.csv_rows:
        if n in _norm_item_text(row.get("Item Name", "")):
            return True
    return False


def _order_matches_fixed_row(
    order: Order, row: FixedBatchRow, *, run: date | None = None
) -> bool:
    """Match order to one fixed_batches.csv row. `any` / `x` / blank = ignore."""
    left = order.left
    if len(left) < 12:
        return False
    # left: finish, source, design-grouping, prime, printing, cust,
    #       cust-type, print-size, print-position, supply, supplier, package
    finish, source, design, prime, printing, cust = left[:6]
    cust_type, print_size, print_pos, supply, supplier, package = left[6:12]

    if cares(row.item_name_contains) and not _order_name_any(order, row.item_name_contains):
        return False
    if cares(row.sku_contains) and not _order_sku_any(order, row.sku_contains):
        return False
    if cares(row.item_name_not_contains) and _order_name_any(order, row.item_name_not_contains):
        return False
    if cares(row.sku_not_contains) and _order_sku_any(order, row.sku_not_contains):
        return False
    if cares(row.destination) and _destination_slot(order) != row.destination:
        return False

    if cares(row.order_status) and _order_status_slot(order) != row.order_status:
        return False
    if cares(row.ship_by_date):
        if run is None or order.ship_by is None:
            return False
        if date_slot(order.ship_by, run) != row.ship_by_date:
            return False
    if cares(row.product_finish) and finish != row.product_finish:
        return False
    if cares(row.order_source) and source != row.order_source:
        return False
    if cares(row.design_grouping) and _fold(design) != row.design_grouping:
        return False
    if cares(row.shipping_service) and prime != row.shipping_service:
        return False
    if cares(row.printing_method) and printing != row.printing_method:
        return False
    if cares(row.customised) and cust != row.customised:
        return False
    if cares(row.customisation_type) and _fold(cust_type) != row.customisation_type:
        return False
    if cares(row.print_size) and _fold(print_size) != row.print_size:
        return False
    if cares(row.print_position) and _fold(print_pos) != row.print_position:
        return False
    if cares(row.supply_method) and supply != slotify(row.supply_method):
        return False
    if cares(row.supplier) and _fold(supplier) != row.supplier and supplier != slotify(row.supplier):
        return False
    if cares(row.package_type) and _fold(package) != row.package_type:
        return False

    # Garment tokens (short-sleeve FOTL / iron-on / Gildan tee) — same predicates as before.
    if row.product_type == "ss_fotl":
        if not _all_chain(order, _line_is_ss_fotl):
            return False
    elif row.product_type == "iron_on":
        if not _all_chain(order, _line_is_iron_on):
            return False
    elif row.product_type == "gildan_tee":
        if not _all_chain(order, _line_is_gildan_tee):
            return False
    elif row.product_type == "mug":
        if not _all_chain(order, _line_is_mug):
            return False
    elif row.product_type == "babysuit":
        if not _all_chain(order, _line_is_babysuit):
            return False
    elif row.product_type == "packs":
        if not any(ln.source == SRC_PACKS for ln in order.lines):
            return False
    elif cares(row.product_type):
        want = {_fold(v) for v in _needles(row.product_type)}
        if not _all_chain(order, lambda ln: _fold(ln.product_type) in want):
            return False
    elif cares(row.category):
        want = _fold(row.category)
        if not _all_chain(order, lambda ln: _fold(ln.category) == want):
            return False

    if cares(row.product_style):
        want = row.product_style
        if not _all_chain(order, lambda ln: _fold(ln.product_style) == want):
            return False
    if cares(row.department):
        want = row.department
        if not _all_chain(order, lambda ln: _fold(ln.department) == want):
            return False
    if cares(row.brand):
        want = row.brand
        if not _all_chain(order, lambda ln: _fold(ln.brand) == want):
            return False
    if cares(row.size):
        want = row.size
        if not _all_chain(order, lambda ln: _fold(ln.size) == want):
            return False
    if cares(row.color):
        want = row.color
        if not _all_chain(order, lambda ln: _fold(ln.colour) == want):
            return False
    return True


def named_process_code(
    order: Order, shift_slot: str = "", *, run: date | None = None
) -> Optional[str]:
    """batch_code from fixed_batches.csv, or None → leftover B1/B2… + 30-chain."""
    for row in fixed_batch_table():
        if _order_matches_fixed_row(order, row, run=run):
            return row.batch_code
    return None


def fixed_batch_matches(order: Order, *, run: date | None = None) -> list[str]:
    """Every fixed batch this order satisfies, in priority order (first one wins)."""
    return [r.batch_code for r in fixed_batch_table() if _order_matches_fixed_row(order, r, run=run)]


def six_field_core(left: list[str], shift_slot: str) -> str:
    """Filename fields 1–5: shift-finish-prime-supply-R/P. Priority is appended later.

    Supervisor 2026-09-22/23: shift first after optional fixed-batch prefix, e.g.
    B100-S1-PRINTED-2-WAREHOUSE STOCK-R-5.
    """
    finish = "PRINTED" if (left[0] if left else "") == "printed" else "PLAIN"
    prime = "1" if (len(left) > 3 and left[3] == "prime") else "2"
    supply_slot = left[9] if len(left) > 9 else "x"
    supply = FILENAME_SUPPLY.get(supply_slot, supply_slot.replace("_", " ").upper())
    cust = "P" if (len(left) > 5 and left[5] == "customised") else "R"
    shift = shift_file_token(shift_slot)
    return f"{shift}-{finish}-{prime}-{supply}-{cust}"


def _bin_is_today(b: ProcessBin, run: date) -> bool:
    """Any due/overdue line makes the pile today (mixed today+future counts as today)."""
    return any(o.ship_by is not None and o.ship_by <= run for o in b.orders)


def _bin_is_prime(b: ProcessBin) -> bool:
    if not b.orders:
        return False
    left = b.orders[0].left
    return len(left) > 3 and left[3] == "prime"


def _apply_six_field_names(bins: list[ProcessBin], run: date) -> None:
    """On-disk name only. Grouping keys are unchanged.

    Field 6 is packing-list order in that shift: today first, then prime first,
    then as files are made (fixed batches, then leftover). More ranking later.

    Leftover piles get B1, B2, … (skipping reserved fixed-batch numbers).
    Supervisor 2026-09-23.
    """
    bins.sort(key=lambda b: _bin_sort_key(b, run))
    leftover = [b for b in bins if b.orders and not b.floor_code]
    plain = [b for b in leftover if b.orders[0].finish == "plain"]
    other = [b for b in leftover if b.orders[0].finish != "plain"]
    for b, code in zip(plain, next_plain_batch_codes(len(plain))):
        b.floor_code = code
    for b, code in zip(other, next_leftover_batch_codes(len(other))):
        b.floor_code = code
    next_pri: dict[str, int] = {}
    for b in bins:
        if not b.orders:
            continue
        core = six_field_core(b.orders[0].left, b.shift_slot)
        stem = f"{b.floor_code}-{core}" if b.floor_code else core
        n = next_pri.get(b.shift_slot, 0) + 1
        next_pri[b.shift_slot] = n
        b.process_name = f"{stem}-{n}"


def _batch_sort_num(code: str) -> int:
    """B100 → 100 for priority sort. Digits only; unknown → 0."""
    digits = "".join(c for c in code if c.isdigit())
    return int(digits) if digits else 0


def _bin_sort_key(b: ProcessBin, run: date) -> tuple:
    shift_i = shift_number(b.shift_slot) - 1
    date_i = 0 if _bin_is_today(b, run) else 1
    prime_i = 0 if _bin_is_prime(b) else 1
    if b.floor_code:
        return (shift_i, date_i, prime_i, 0, _batch_sort_num(b.floor_code), "")
    return (shift_i, date_i, prime_i, 1, 0, b.process_name)


def _order_colour(order: Order) -> str:
    """Unanimous colour, or '' if packs / mixed / blank (leftover, not a colour group)."""
    if order_skips_colour(order):
        return ""
    vals = _field_values(order, "colour")
    if not vals or any(not v for v in vals):
        return ""
    return _unanimous(vals) or ""


def _pack_parts(orders: list[Order], cap: int = PART_CAP) -> list[list[Order]]:
    """Fill parts to cap units. No skip-around. An order larger than cap keeps one -N."""
    if not orders:
        return []
    chunks: list[list[Order]] = [[]]
    used = 0
    for order in orders:
        if chunks[-1] and used + order.units > cap:
            chunks.append([])
            used = 0
        chunks[-1].append(order)
        used += order.units
    return chunks


def assign_inside_file(orders: list[Order]) -> list[ProcessPart]:
    """Colour 3+ groups first (not packs), then 50-unit parts. -N is inside the file."""
    if not orders:
        return []
    packs_only = all(order_skips_colour(o) for o in orders)
    groups: list[list[Order]] = []
    if packs_only:
        groups = [list(orders)]
    else:
        by_colour: dict[str, list[Order]] = defaultdict(list)
        leftover: list[Order] = []
        for order in orders:
            colour = _order_colour(order)
            if colour:
                by_colour[colour].append(order)
            else:
                leftover.append(order)
        for colour in sorted(by_colour, key=str.casefold):
            group = by_colour[colour]
            if sum(o.units for o in group) >= COLOUR_GROUP_MIN:
                groups.append(group)
            else:
                leftover.extend(group)
        if leftover:
            groups.append(leftover)
    parts: list[ProcessPart] = []
    n = 1
    for group in groups:
        for chunk in _pack_parts(group):
            parts.append(ProcessPart(n=n, orders=chunk))
            n += 1
    return parts


def shift_number(shift_slot: str) -> int:
    digits = "".join(c for c in shift_slot if c.isdigit())
    return int(digits) if digits else 1


def shift_file_token(shift_slot: str) -> str:
    return f"S{shift_number(shift_slot)}"


def shift_pair(n: int) -> tuple[str, str]:
    if n == 1:
        slot = "1st"
    elif n == 2:
        slot = "2nd"
    elif n == 3:
        slot = "3rd"
    else:
        slot = f"{n}th"
    return slot, f"{slot} Shift"


def _eligible_stats(orders: list[Order], run: date) -> tuple[int, int]:
    today = sum(1 for o in orders if o.ship_by is not None and o.ship_by <= run)
    return today, len(orders)


def _should_mix_today_future(eligible_orders: int) -> bool:
    """Mix today+later in one process when Shift 1 volume is not above 300 orders."""
    return eligible_orders <= SHIFT1_SPLIT_ORDERS


def _classify_or_unmatch(order: Order, unmatched: list[Order]) -> bool:
    finish = _order_finish(order)
    if finish is None:
        _mark_unmatched(order, "no catalog match")
        unmatched.append(order)
        return False
    slots = left_slots(order, finish)
    if slots is None:
        unmatched.append(order)
        return False
    order.finish = finish
    order.left = slots
    return True


def group_orders(
    orders: list[Order],
    run: date,
    *,
    shift_slot: str = "1st",
    shift_folder: str | None = None,
) -> SortResult:
    if shift_folder is None:
        shift_folder = f"{shift_slot} Shift"
    resend: list[Order] = []
    unmatched: list[Order] = []
    held: list[Order] = []
    eligible: list[Order] = []
    for order in orders:
        if _has_tag(order.tag_names, RESEND_TAG):
            resend.append(order)
            continue
        if order.ship_by is None:
            if order.ship_by_raw:
                # Unparseable non-blank date — still unmatched (not inventing a day).
                _mark_unmatched(order, "unparseable ship-by")
                unmatched.append(order)
                continue
            # Blank ship-by: in awaiting_shipment → pull today (supervisor 2026-09-24).
            order.ship_by = run
            eligible.append(order)
            continue
        eligible.append(order)

    today_orders, eligible_orders = _eligible_stats(eligible, run)
    mix = _should_mix_today_future(eligible_orders)
    bins: list[ProcessBin] = []
    named_groups: dict[tuple[str, str], list[Order]] = defaultdict(list)
    by_key: dict[tuple[str, tuple[str, ...]], list[Order]] = defaultdict(list)
    overlaps: Counter[str] = Counter()
    for order in eligible:
        if not _classify_or_unmatch(order, unmatched):
            continue
        # Personalised pile only when SS tag says design is ready on the floor.
        if _order_is_customised(order) and not _has_tag(
            order.tag_names, PERSONALISED_READY_TAG
        ):
            order.unmatched_reason = "personalised design not ready"
            held.append(order)
            continue
        dslot = "" if mix else date_slot(order.ship_by, run)
        hits = fixed_batch_matches(order, run=run)
        code = hits[0] if hits else None
        for lost in hits[1:]:
            overlaps[f"{code} over {lost}"] += 1
        if code:
            named_groups[(code, dslot)].append(order)
            continue
        by_key[(dslot, tuple(order.left))].append(order)
    for (code, _dslot), group in named_groups.items():
        inside = assign_inside_file(group)
        flat = [o for p in inside for o in p.orders]
        bins.append(
            ProcessBin(
                shift_slot=shift_slot,
                shift_folder=shift_folder,
                process_name=code,
                orders=flat,
                parts=inside,
                floor_code=code,
            )
        )
    for (dslot, left), group in by_key.items():
        peeled_unmatched: list[Order] = []
        peeled = peel_chain(group, CHAIN_30, list(left), peeled_unmatched)
        unmatched.extend(peeled_unmatched)
        for slots, part_orders in peeled:
            inside = assign_inside_file(part_orders)
            flat = [o for p in inside for o in p.orders]
            bins.append(
                ProcessBin(
                    shift_slot=shift_slot,
                    shift_folder=shift_folder,
                    process_name=_process_name(dslot, shift_slot, slots),
                    orders=flat,
                    parts=inside,
                    group_slots=list(slots),
                    ship_by_slot=dslot or "x",
                )
            )
    _apply_six_field_names(bins, run)
    return SortResult(
        run_date=run,
        skipped_post=0,
        empty_skipped=0,
        resend=resend,
        unmatched=unmatched,
        held=held,
        bins=bins,
        pool_orders=len(orders),
        shift_slot=shift_slot,
        shift_folder=shift_folder,
        mix_today_future=mix,
        today_orders=today_orders,
        eligible_orders=eligible_orders,
        overlaps=overlaps,
    )


def sort_raw_orders(
    raw_orders: list[dict[str, Any]],
    *,
    catalogs: Catalogs,
    tag_id_to_name: dict[int, str],
    store_id_to_name: dict[int, str],
    run_date: date,
    shift_slot: str = "1st",
    shift_folder: str = "1st Shift",
    exclude_order_numbers: Optional[set[str]] = None,
) -> SortResult:
    parsed, skipped_post, empty_skipped, skipped_store = orders_from_ss(
        raw_orders, tag_id_to_name, store_id_to_name, catalogs
    )
    already = exclude_order_numbers or set()
    skipped_written = 0
    kept: list[Order] = []
    for order in parsed:
        if order.number in already:
            skipped_written += 1
        else:
            kept.append(order)
    result = group_orders(
        kept, run_date, shift_slot=shift_slot, shift_folder=shift_folder
    )
    result.skipped_post = skipped_post
    result.empty_skipped = empty_skipped
    result.skipped_excluded_store = skipped_store
    result.skipped_already_written = skipped_written
    result.pool_orders = (
        len(parsed) + skipped_post + empty_skipped + skipped_store
    )
    return result


def _counts(orders: list[Order]) -> tuple[int, int, int]:
    return len(orders), sum(o.line_count for o in orders), sum(o.units for o in orders)


def input_date_folder(run: date) -> str:
    return run.strftime("%d-%m-%Y")


def next_open_shift(input_root: Path, run: date) -> tuple[str, str]:
    """Nth --run this calendar day (production later when SHIFT_PER_RUN is True)."""
    day = Path(input_root) / input_date_folder(run)
    n = 1
    while n < 20:
        slot, folder = shift_pair(n)
        if not any((day / folder).glob("*.csv")):
            return slot, folder
        n += 1
    return shift_pair(n)


def order_numbers_in_date_folder(input_root: Path, run: date) -> set[str]:
    """Order # already in any shift CSV for this run date (skip on a later run)."""
    day = Path(input_root) / input_date_folder(run)
    found: set[str] = set()
    if not day.is_dir():
        return found
    for csv_path in day.glob("*/*.csv"):
        try:
            with csv_path.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    number = (row.get("Order #") or "").strip()
                    if number:
                        found.add(number)
        except (OSError, csv.Error, UnicodeDecodeError):
            continue
    return found


def _csv_rows_for(order: Order) -> list[dict[str, str]]:
    if order.csv_rows:
        return list(order.csv_rows)
    tags = ", ".join(order.tag_names)
    return [
        {
            "Order #": order.number,
            "Ship By": order.ship_by_raw,
            "Quantity": str(ln.qty),
            "Item - Image URL": "",
            "Gift - Message": "",
            "Notes - From Buyer": "",
            "Item SKU": ln.sku,
            "Item Name": "",
            "Item - Options": "",
            "Recipient": "",
            "Tags": tags,
        }
        for ln in order.lines
    ]


def _orders_in_part_order(orders: list[Order]) -> list[Order]:
    parts = assign_inside_file(orders)
    return [o for p in parts for o in p.orders] if parts else list(orders)


def write_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        return path
    except PermissionError:
        # ponytail: Excel/Cursor lock — same fallback as CL csv-writes.
        fallback = path.with_name(path.stem + "_write_fallback" + path.suffix)
        with fallback.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            writer.writerows(rows)
        return fallback


def write_process_csvs(
    result: SortResult,
    *,
    input_root: Path | None = None,
) -> list[Path]:
    """One CSV per process into this run's shift folder only. Other shifts stay put."""
    root = Path(input_root) if input_root else wh.packing_input_dir()
    date_folder = input_date_folder(result.run_date)
    folder = result.shift_folder
    (root / date_folder / folder).mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def dump(name: str, orders: list[Order]) -> None:
        ordered = _orders_in_part_order(orders)
        if not ordered:
            return
        path = root / date_folder / folder / f"{name}.csv"
        written.append(
            write_csv(path, [row for order in ordered for row in _csv_rows_for(order)])
        )

    dump(RESEND_FILE, result.resend)
    dump(UNMATCHED_FILE, result.unmatched)
    for bin_ in result.bins:
        dump(bin_.process_name, bin_.orders)

    keep = {p.resolve() for p in written}
    shift_dir = root / date_folder / folder
    for old in shift_dir.glob("*.csv"):
        if old.resolve() in keep:
            continue
        try:
            old.unlink()
        except PermissionError:
            pass
    return written


def format_report(result: SortResult, written: list[Path] | None = None) -> str:
    lines: list[str] = []
    o, li, u = _counts(
        [
            *result.resend,
            *result.unmatched,
            *result.held,
            *(o for b in result.bins for o in b.orders),
        ]
    )
    wrote = written is not None
    mode = "run" if wrote else "dry-run"
    lines.append(f"Order Grouping Sorter {mode}  run-date={result.run_date.isoformat()}")
    if wrote:
        lines.append(f"Input WAS written ({len(written)} CSV).")
        for path in written or []:
            lines.append(f"  {path}")
    else:
        lines.append("Input was NOT written.")
    lines.append(
        f"awaiting_shipment fetched={result.pool_orders}  "
        f"skipped post-order-designs={result.skipped_post}  "
        f"skipped DTFOcean.co.uk WP={result.skipped_excluded_store}  "
        f"empty/discount-only={result.empty_skipped}"
    )
    ro, rl, ru = _counts(result.resend)
    lines.append(f"{RESEND_FILE}  orders={ro}  lines={rl}  units={ru}")
    for p in assign_inside_file(result.resend):
        po, pl, pu = _counts(p.orders)
        lines.append(f"  -{p.n}  orders={po}  lines={pl}  units={pu}")
    uo, ul, uu = _counts(result.unmatched)
    lines.append(f"{UNMATCHED_FILE}  orders={uo}  lines={ul}  units={uu}")
    reasons = Counter(o.unmatched_reason or "(no reason)" for o in result.unmatched)
    for reason, n in reasons.most_common():
        lines.append(f"  {reason}: {n}")
    for p in assign_inside_file(result.unmatched):
        po, pl, pu = _counts(p.orders)
        lines.append(f"  -{p.n}  orders={po}  lines={pl}  units={pu}")
    ho, hl, hu = _counts(result.held)
    lines.append(
        f"HELD personalised (no {PERSONALISED_READY_TAG!r})  "
        f"orders={ho}  lines={hl}  units={hu}"
    )
    for p in assign_inside_file(result.held):
        po, pl, pu = _counts(p.orders)
        lines.append(f"  -{p.n}  orders={po}  lines={pl}  units={pu}")
    lines.append(
        f"shift={result.shift_slot}  folder={result.shift_folder}  "
        f"{shift_file_token(result.shift_slot)}"
    )
    mix_word = "yes" if result.mix_today_future else "no"
    lines.append(
        f"today+future mix={mix_word}  today_orders={result.today_orders}  "
        f"eligible_orders={result.eligible_orders}  "
        f"(mix when eligible orders<={SHIFT1_SPLIT_ORDERS}; else split today vs later dates)"
    )
    if result.skipped_already_written:
        lines.append(
            f"skipped already in today's earlier shift CSVs: "
            f"{result.skipped_already_written} orders"
        )
    if result.overlaps:
        lines.append("fixed-batch overlaps (first wins; orders):")
        for pair, n in result.overlaps.most_common():
            lines.append(f"  {pair}: {n}")
    used = sum(o.line_count for b in result.bins for o in b.orders)
    lines.append(f"{result.shift_folder}  lines={used}")
    if not result.bins:
        lines.append("  (empty)")
    else:
        for b in result.bins:
            _append_process_block(lines, b.process_name, b.orders, b.parts, indent="  ")
    lines.append(
        f"grouped orders={o}  lines={li}  units={u}  (resend+unmatched+held+bins)"
    )
    return "\n".join(lines) + "\n"


def _append_process_block(
    lines: list[str],
    name: str,
    orders: list[Order],
    parts: list[ProcessPart] | None = None,
    *,
    indent: str,
) -> None:
    bo, bl, bu = _counts(orders)
    lines.append(f"{indent}{name}  orders={bo}  lines={bl}  units={bu}")
    inside = parts if parts is not None else assign_inside_file(orders)
    for p in inside:
        po, pl, pu = _counts(p.orders)
        lines.append(f"{indent}  -{p.n}  orders={po}  lines={pl}  units={pu}")
