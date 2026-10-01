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

def test_named_fawad_personalised_fotl_stays_on_run_shift() -> None:
    cat = _fotl_cats(**{"Customise": "Yes"})
    r = group_orders(
        [_order("F90", "1-M-T-WHT-M", store="MAS Clothing", catalogs=cat, tags=_ready())],
        RUN,
    )
    batch = [b for b in r.bins if b.floor_code == "B90"]
    assert len(batch) == 1
    assert batch[0].process_name.startswith("B90-S1-PRINTED-2-WAREHOUSE STOCK-P-")
    assert {o.number for o in batch[0].orders} == {"F90"}
    assert batch[0].shift_slot == "1st"
    assert r.held == []


def test_named_floor_mixes_today_future_when_small() -> None:
    cat = _fotl_cats()
    r = group_orders(
        [
            _order("N1", "1-M-T-WHT-M", catalogs=cat),
            _order("N2", "1-M-T-WHT-M", ship="2026-09-20", catalogs=cat),
        ],
        RUN,
    )
    assert r.mix_today_future is True
    batch = [b for b in r.bins if b.floor_code == "B100"]
    assert len(batch) == 1
    assert {o.number for o in batch[0].orders} == {"N1", "N2"}
    assert batch[0].shift_slot == "1st"


def test_glow_and_sku_contain_fixed_batches() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order(
                "G1",
                "77989LG-M-T-BLK-M",
                catalogs=cat,
                item_name="Kids Glow-in-the-Dark Tee",
            ),
            _order(
                "G2",
                "77989LG-M-T-BLK-M",
                catalogs=cat,
                item_name="Adult Glow In The Dark Shirt",
            ),
            _order("S1", "179975LG-M-T-BLK-M", catalogs=cat, item_name="Dancing Queen Tee"),
            _order("S2", "179975LG-M-T-BLK-M", catalogs=cat),
            _order("N1", "77989LG-M-T-BLK-M", catalogs=cat, item_name="Plain Black Tee"),
        ],
        RUN,
    )
    by = {o.number: b.floor_code for b in r.bins for o in b.orders}
    assert by["G1"] == "B3500"
    assert by["G2"] == "B3500"
    assert by["S1"] == "B5500"
    assert by["S2"] != "B5500"  # needs SKU AND Dancing Queen name
    assert by["N1"] not in {"B3500", "B5500"}






def test_plain_sequence_skips_reserved() -> None:
    from grouping import next_plain_batch_codes

    assert next_plain_batch_codes(6) == ["B2000", "B2100", "B2200", "B2500", "B2600", "B2700"]


