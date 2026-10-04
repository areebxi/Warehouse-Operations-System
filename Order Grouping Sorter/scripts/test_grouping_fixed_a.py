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

def test_b50_on_demand_fotl_ready_made() -> None:
    """B50 = B100 twin with Supplier On Demand (locked 2026-09-30)."""
    cat = Catalogs(
        cl={
            "m-t-wht-m": _cl_row(
                **{
                    "Custom_Label": "M-T-WHT-M",
                    "Stock_Type": "Supplier On Demand",
                    "Supplier_Name": "BTC Activewear",
                    "Brand": "Fruit Of The Loom",
                    "Colour": "White",
                }
            )
        }
    )
    r = group_orders([_order("OD1", "1-M-T-WHT-M", catalogs=cat)], RUN)
    assert len(r.bins) == 1
    assert r.bins[0].floor_code == "B50"
    assert r.bins[0].process_name.startswith("B50-S1-PRINTED-2-SUPPLY ON DEMAND-R-")


def test_fixed_batch_codes_first_then_graph_leftover() -> None:
    fotl = _fotl_cats()
    other = _cats()
    r = group_orders(
        [
            _order("FOTL", "1-M-T-WHT-M", catalogs=fotl),
            _order("OTH", "77989LG-M-T-BLK-M", catalogs=other),
        ],
        RUN,
    )
    by_name = {b.process_name: {o.number for o in b.orders} for b in r.bins}
    batch = [n for n in by_name if n.startswith("B100-")]
    leftover = [n for n in by_name if not any(n.startswith(f"{c}-") for c in FIXED_BATCH_CODES)]
    assert len(batch) == 1
    assert by_name[batch[0]] == {"FOTL"}
    assert batch[0].startswith("B100-S1-PRINTED-2-WAREHOUSE STOCK-R-")
    assert len(leftover) == 1
    assert leftover[0] == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-2"
    assert by_name[leftover[0]] == {"OTH"}


def test_named_floor_splits_today_future_when_over_mix() -> None:
    cat = _fotl_cats()
    today = [_order(f"A{i:03d}", "77989LG-M-T-BLK-M", catalogs=_cats()) for i in range(300)]
    first = _order("N1", "1-M-T-WHT-M", catalogs=cat)
    future = _order("N2", "1-M-T-WHT-M", ship="2026-09-20", catalogs=cat)
    r = group_orders(today + [first, future], RUN)
    assert r.mix_today_future is False
    batch = [b for b in r.bins if b.floor_code == "B100"]
    assert len(batch) == 2
    by = {o.number: b for b in batch for o in b.orders}
    assert by["N1"].process_name != by["N2"].process_name
    assert all(b.shift_slot == "1st" for b in batch)
    assert int(by["N1"].process_name.rsplit("-", 1)[-1]) < int(
        by["N2"].process_name.rsplit("-", 1)[-1]
    )






def test_named_ironon_includes_prime_sticker_is_b1050() -> None:
    iron = _iron_cats()
    sticker = Catalogs(
        cl={
            "sticker-a4": _cl_row(
                **{
                    "Custom_Label": "STICKER-A4",
                    "Stock_Type": "In House Manufacture",
                    "Supplier_Name": "",
                    "Brand": "",
                    "Category (Areeb)": "Stickers",
                    "Product Type (Areeb)": "Sticker",
                }
            )
        }
    )
    r = group_orders(
        [
            _order("IP", "190867LG-DTF-IronOn-A4", tags=["Amazon Prime Order"], catalogs=iron),
            _order("S1", "802008LG-STICKER-A4", catalogs=sticker),
        ],
        RUN,
    )
    by_code = {b.floor_code: {o.number for o in b.orders} for b in r.bins}
    assert by_code["B1000"] == {"IP"}
    assert by_code["B1050"] == {"S1"}


