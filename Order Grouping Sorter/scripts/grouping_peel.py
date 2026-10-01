"""30-chain peel into process piles."""
from __future__ import annotations

from collections import defaultdict

from grouping_models import Order, slotify
from grouping_slots import (_field_values, _mark_unmatched, _unanimous, order_skips_colour)

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


