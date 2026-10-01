"""group_orders / sort_raw_orders orchestration."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any, Optional

from catalogs import Catalogs
from grouping_fixed import fixed_batch_matches
from grouping_intake import _has_tag, _order_is_customised, orders_from_ss
from grouping_models import (
    CHAIN_30,
    PERSONALISED_READY_TAG,
    RESEND_TAG,
    SHIFT1_SPLIT_ORDERS,
    Order,
    ProcessBin,
    SortResult,
    date_slot,
)
from grouping_names import _apply_six_field_names
from grouping_parts import assign_inside_file
from grouping_peel import _process_name, peel_chain
from grouping_slots import _mark_unmatched, _order_finish, left_slots


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


