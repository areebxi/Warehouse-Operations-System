from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# Path bootstrap + fixtures + grouping API live in test_grouping_fixtures.
from test_grouping_fixtures import (  # noqa: F401
    FIXED_BATCH_CODES,
    PERSONALISED_READY_TAG,
    RUN,
    Catalogs,
    Order,
    _cats,
    _cl_row,
    _fotl_cats,
    _gildan_tee_cats,
    _iron_cats,
    _order,
    _packs_row,
    _plain_row,
    _ready,
    _sweatshirt_cats,
    attrs_for_sku,
    finish_for_sku,
    group_orders,
    next_open_shift,
    next_plain_batch_codes,
    order_numbers_in_date_folder,
    six_field_core,
    slotify,
    write_process_csvs,
)

def test_today_orders_never_held() -> None:
    cat = _cats()
    today = [_order(f"A{i:03d}", "77989LG-M-T-BLK-M", catalogs=cat) for i in range(250)]
    fat = _order("B-FAT", "77989LG-M-T-BLK-M", catalogs=cat)
    fat.lines = [attrs_for_sku("77989LG-M-T-BLK-M", 1, cat) for _ in range(80)]
    tiny = _order("C-TINY", "77989LG-M-T-BLK-M", catalogs=cat)
    huge = _order("D-HUGE", "77989LG-M-T-BLK-M", catalogs=cat)
    huge.lines = [attrs_for_sku("77989LG-M-T-BLK-M", 1, cat) for _ in range(400)]
    r = group_orders(today + [fat, tiny, huge], RUN)
    assert r.held == []
    assert all(b.shift_slot == "1st" for b in r.bins)
    numbers = {o.number for b in r.bins for o in b.orders}
    assert {"B-FAT", "C-TINY", "D-HUGE"} <= numbers
    assert sum(o.line_count for b in r.bins for o in b.orders) == 250 + 80 + 1 + 400


def test_future_fill_uses_future_slot_not_iso_date() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order("FUT", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat),
            _order("FUT2", "77989LG-M-T-BLK-M", ship="2026-09-25", catalogs=cat),
        ],
        RUN,
    )
    assert len(r.bins) == 1
    assert r.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"
    assert {o.number for o in r.bins[0].orders} == {"FUT", "FUT2"}


def test_small_pool_mixes_today_and_future() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order("T1", "77989LG-M-T-BLK-M", catalogs=cat),
            _order("F1", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat),
        ],
        RUN,
    )
    assert r.mix_today_future is True
    leftover = [b for b in r.bins if b.floor_code not in FIXED_BATCH_CODES]
    assert len(leftover) == 1
    assert {o.number for o in leftover[0].orders} == {"T1", "F1"}
    assert leftover[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"


def test_today_300_plus_future_splits_by_date() -> None:
    cat = _cats()
    today = [_order(f"A{i:03d}", "77989LG-M-T-BLK-M", catalogs=cat) for i in range(300)]
    r = group_orders(
        today + [_order("F1", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat)],
        RUN,
    )
    assert r.eligible_orders == 301
    assert r.mix_today_future is False
    by = {o.number: b.process_name for b in r.bins for o in b.orders}
    assert by["A000"] != by["F1"]
    assert int(by["A000"].rsplit("-", 1)[-1]) < int(by["F1"].rsplit("-", 1)[-1])


def test_volume_300_mixes_today_and_later() -> None:
    cat = _cats()
    today = [_order(f"T{i:03d}", "77989LG-M-T-BLK-M", catalogs=cat) for i in range(200)]
    future = [
        _order(f"F{i:03d}", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat)
        for i in range(100)
    ]
    r = group_orders(today + future, RUN)
    assert r.eligible_orders == 300
    assert r.mix_today_future is True
    by = {o.number: b.process_name for b in r.bins for o in b.orders}
    assert by["T000"] == by["F000"]


def test_volume_over_300_splits_even_if_today_is_small() -> None:
    cat = _cats()
    today = [_order(f"T{i:03d}", "77989LG-M-T-BLK-M", catalogs=cat) for i in range(50)]
    future = [
        _order(f"F{i:03d}", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat)
        for i in range(251)
    ]
    r = group_orders(today + future, RUN)
    assert r.today_orders == 50
    assert r.eligible_orders == 301
    assert r.mix_today_future is False
    by = {o.number: b.process_name for b in r.bins for o in b.orders}
    assert by["T000"] != by["F000"]


