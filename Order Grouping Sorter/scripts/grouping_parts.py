"""Inside-file colour groups and 50-unit parts."""
from __future__ import annotations

from collections import defaultdict

from grouping_models import COLOUR_GROUP_MIN, PART_CAP, Order, ProcessPart
from grouping_slots import _field_values, _unanimous, order_skips_colour

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
