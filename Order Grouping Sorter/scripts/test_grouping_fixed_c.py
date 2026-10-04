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

def test_named_floor_fawad_prime_customised_ironon() -> None:
    fotl = _fotl_cats()
    fotl_yes = _fotl_cats(**{"Customise": "Yes"})
    iron = _iron_cats()
    iron_yes = _iron_cats(customise="Yes")
    r = group_orders(
        [
            _order("F80", "1-M-T-WHT-M", store="MAS Clothing", catalogs=fotl),
            _order(
                "F90",
                "1-M-T-WHT-M",
                store="MAS Clothing",
                catalogs=fotl_yes,
                tags=_ready(),
            ),
            _order("P8", "1-M-T-WHT-M", tags=["Amazon Prime Order"], catalogs=fotl),
            _order("C4", "1-M-T-WHT-M", catalogs=fotl_yes, tags=_ready()),
            _order(
                "CP",
                "1-M-T-WHT-M",
                tags=_ready("Amazon Prime Order"),
                catalogs=fotl_yes,
            ),
            _order("I1", "190867LG-DTF-IronOn-A4", catalogs=iron),
            _order("I5", "190867LG-DTF-IronOn-A4", catalogs=iron_yes, tags=_ready()),
            _order("IF", "190867LG-DTF-IronOn-A4", store="MAS Clothing", catalogs=iron),
            _order(
                "IP",
                "190867LG-DTF-IronOn-A4",
                store="MAS Clothing",
                catalogs=iron_yes,
                tags=_ready(),
            ),
        ],
        RUN,
    )
    by_code = {b.floor_code: {o.number for o in b.orders} for b in r.bins if b.floor_code}
    assert by_code["B80"] == {"F80"}
    assert by_code["B90"] == {"F90"}
    assert by_code["B8000"] == {"P8"}
    assert by_code["B4000"] == {"C4"}
    assert by_code["B8050"] == {"CP"}
    assert by_code["B1000"] == {"I1"}
    assert by_code["B5000"] == {"I5"}
    assert by_code["B1080"] == {"IF"}
    assert by_code["B5080"] == {"IP"}
    for b in r.bins:
        if b.floor_code == "B80":
            assert b.process_name.startswith("B80-S1-PRINTED-2-WAREHOUSE STOCK-R-")
        if b.floor_code == "B90":
            assert b.process_name.startswith("B90-S1-PRINTED-2-WAREHOUSE STOCK-P-")
        if b.floor_code == "B8000":
            assert b.process_name.startswith("B8000-S1-PRINTED-1-WAREHOUSE STOCK-R-")
        if b.floor_code == "B4000":
            assert b.process_name.startswith("B4000-S1-PRINTED-2-WAREHOUSE STOCK-P-")
    pri = {b.floor_code: int(b.process_name.rsplit("-", 1)[-1]) for b in r.bins if b.floor_code}
    assert pri["B8000"] < pri["B80"]
    assert pri["B8050"] < pri["B80"]
    assert pri["B80"] < pri["B90"] < pri["B1000"]

def test_named_floor_skips_30chain_and_keeps_inside_file() -> None:
    cat = Catalogs(
        cl={
            "m-t-blk-m": _cl_row(
                **{
                    "Stock_Type": "Warehouse Stock",
                    "Brand": "Fruit Of The Loom",
                    "Colour": "Black",
                    "Department (Areeb)": "Mens",
                }
            ),
            "k-t-blk-s": _cl_row(
                **{
                    "Custom_Label": "K-T-BLK-S",
                    "Stock_Type": "Warehouse Stock",
                    "Brand": "Fruit Of The Loom",
                    "Colour": "Navy",
                    "Department (Areeb)": "Kids",
                    "Product Type (Areeb)": "Childrens T-Shirt",
                }
            ),
        }
    )
    mens = [_order(f"M{i:02d}", "1-M-T-BLK-M", qty=1, catalogs=cat) for i in range(40)]
    kids = [_order(f"K{i}", "1-K-T-BLK-S", qty=3, catalogs=cat) for i in range(2)]
    r = group_orders(mens + kids, RUN)
    assert len(r.bins) == 1
    assert r.bins[0].floor_code == "B100"
    assert r.bins[0].process_name.startswith("B100-S1-PRINTED-2-WAREHOUSE STOCK-R-")
    assert "mens" not in r.bins[0].process_name
    parts = r.bins[0].parts
    assert [p.n for p in parts] == [1, 2]
    assert sum(o.units for o in parts[0].orders) == 40
    assert sum(o.units for o in parts[1].orders) == 6

