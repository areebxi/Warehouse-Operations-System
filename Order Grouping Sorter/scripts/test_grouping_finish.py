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

def test_finish_gate_and_attribute_source() -> None:
    cat = _cats()
    assert finish_for_sku("77989LG-M-T-BLK-M", cat) == "printed"
    assert finish_for_sku("1243-1", cat) == "plain"
    assert finish_for_sku("SET4741", cat) == "plain"
    assert finish_for_sku("M99-plain-1243", cat) == "plain"
    assert finish_for_sku("NOPE", cat) is None
    # Dashed SKU: after-first only (M-T-BLK-M → T-BLK-M, not the Custom Label)
    assert finish_for_sku("M-T-BLK-M", cat) is None
    packs = attrs_for_sku("SET4741", 1, cat)
    assert packs.source == "packs"
    assert packs.brand == "Fruit Of The Loom"
    assert packs.size == "5"
    assert packs.colour == ""


def test_plain_in_house_unmatched() -> None:
    cat = Catalogs(
        plain={
            "1243": _plain_row(**{"Supply Method": "In House Manufacture"}),
        }
    )
    r = group_orders([_order("P1", "1243-1", catalogs=cat)], RUN)
    assert r.bins == []
    assert r.unmatched[0].unmatched_reason == "plain in-house"


def test_printed_wins_and_mixed_flag1_unmatched() -> None:
    cat = _cats()
    mixed_finish = _order(
        "M1",
        "77989LG-M-T-BLK-M",
        catalogs=cat,
        extra_lines=[("1243-1", 1)],
    )
    r = group_orders([mixed_finish], RUN)
    # supply-method mixed (on-demand printed vs on-demand plain — same value, should group printed)
    # both fixtures are Supplier On Demand + BTC, so printed-wins should succeed
    assert r.unmatched == []
    assert r.bins[0].orders[0].finish == "printed"

    cat2 = Catalogs(
        cl={"m-t-blk-m": _cl_row()},
        plain={"1243": _plain_row(**{"Supply Method": "Warehouse Stock"})},
    )
    mixed_supply = _order(
        "M2",
        "77989LG-M-T-BLK-M",
        catalogs=cat2,
        extra_lines=[("1243-1", 1)],
    )
    r2 = group_orders([mixed_supply], RUN)
    assert r2.unmatched == []
    assert r2.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"


def test_no_dash_sku_matches_cl_whole() -> None:
    cat = Catalogs(
        cl={"a515": _cl_row(**{"Custom Label": "A515", "Customise": "Yes"})},
        packs={"set4741": _packs_row()},
    )
    assert finish_for_sku("A515", cat) == "printed"
    ln = attrs_for_sku("A515", 1, cat)
    assert ln.customise == "Yes"
    assert finish_for_sku("SET4741", cat) == "plain"
    r = group_orders([_order("A1", "A515", tags=_ready(), catalogs=cat)], RUN)
    assert r.unmatched == []
    assert r.held == []
    assert r.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-P-1"


def test_slotify() -> None:
    assert slotify("BTC Activewear") == "btc_activewear"
    assert slotify("T-SHIRTS") == "t-shirts"


