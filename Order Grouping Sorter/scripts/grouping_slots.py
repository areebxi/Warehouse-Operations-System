"""Left Graph slots after finish."""
from __future__ import annotations

from typing import Optional

from catalogs import SRC_PACKS
from grouping_intake import _has_tag
from grouping_models import (ATTR_FIELD, FAWAD_STORE, IN_HOUSE, ON_DEMAND, PRIME_TAG, LineAttrs, Order, _fold, slotify)

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


