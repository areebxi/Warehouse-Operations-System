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

def test_inside_file_colour_groups_then_parts() -> None:
    cat = Catalogs(
        cl={
            "m-t-blk-m": _cl_row(**{"Colour": "Black"}),
            "m-t-nvy-m": _cl_row(**{"Custom_Label": "M-T-NVY-M", "Colour": "Navy"}),
            "m-t-wht-m": _cl_row(**{"Custom_Label": "M-T-WHT-M", "Colour": "White"}),
        }
    )
    # <30 per colour so they stay in one process file; ≥3 black/navy → inside -N groups
    blacks = [_order(f"B{i}", "1-M-T-BLK-M", qty=1, catalogs=cat) for i in range(6)]
    navies = [_order(f"N{i}", "1-M-T-NVY-M", qty=1, catalogs=cat) for i in range(4)]
    white = _order("W1", "1-M-T-WHT-M", qty=2, catalogs=cat)
    r = group_orders(blacks + navies + [white], RUN)
    assert len(r.bins) == 1
    parts = r.bins[0].parts
    assert [p.n for p in parts] == [1, 2, 3]
    assert sum(o.units for o in parts[0].orders) == 6
    assert all(o.number.startswith("B") for o in parts[0].orders)
    assert sum(o.units for o in parts[1].orders) == 4
    assert all(o.number.startswith("N") for o in parts[1].orders)
    assert [o.number for o in parts[2].orders] == ["W1"]

    # 60 units of one colour → file peels at 30; inside that file, 50-unit parts
    many = [_order(f"K{i:02d}", "1-M-T-BLK-M", qty=10, catalogs=cat) for i in range(6)]
    r2 = group_orders(many, RUN)
    assert len(r2.bins) == 1
    assert [sum(o.units for o in p.orders) for p in r2.bins[0].parts] == [50, 10]

    fat = _order("FAT60", "1-M-T-BLK-M", catalogs=cat)
    fat.lines = [attrs_for_sku("1-M-T-BLK-M", 60, cat)]
    r3 = group_orders([fat], RUN)
    assert len(r3.bins[0].parts) == 1
    assert r3.bins[0].parts[0].orders[0].units == 60

    pack_cat = Catalogs(packs={"set4741": _packs_row()})
    packs = [_order(f"P{i}", "SET4741", qty=10, catalogs=pack_cat) for i in range(8)]
    r4 = group_orders(packs, RUN)
    assert [sum(o.units for o in p.orders) for p in r4.bins[0].parts] == [50, 30]


