"""Fixed-batch row matching against order left-slots."""
from __future__ import annotations

from datetime import date
from typing import Optional

from catalogs import SRC_PACKS
from fixed_batches import FixedBatchRow, cares, fixed_batch_table
from grouping_garments import (
    _all_chain,
    _destination_slot,
    _line_is_babysuit,
    _line_is_gildan_tee,
    _line_is_iron_on,
    _line_is_mug,
    _line_is_ss_fotl,
    _needles,
    _order_name_any,
    _order_sku_any,
    _order_status_slot,
)
from grouping_models import Order, _fold, date_slot, slotify


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


