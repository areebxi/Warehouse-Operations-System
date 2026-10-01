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

def test_flag30_peels_and_packs_skip_colour() -> None:
    cat = Catalogs(
        plain={
            "1243": _plain_row(**{"Colour": "White"}),
            "555": _plain_row(**{"SKU": "555", "Colour": "Navy"}),
        },
        packs={"set4741": _packs_row()},
    )
    whites = [
        _order(f"W{i}", "1243-1", qty=5, catalogs=cat) for i in range(6)
    ]  # 30 units white
    navy = _order("N1", "555-1", qty=2, catalogs=cat)
    pack = _order("PK", "SET4741", qty=4, catalogs=cat)
    r = group_orders(whites + [navy, pack], RUN)
    white_bin = next(b for b in r.bins if any(o.number.startswith("W") for o in b.orders))
    navy_bin = next(b for b in r.bins if any(o.number == "N1" for o in b.orders))
    pack_bins = [b for b in r.bins if any(o.number == "PK" for o in b.orders)]
    assert any(o.number.startswith("W") for o in white_bin.orders)
    assert navy_bin is not white_bin
    assert pack_bins
    assert "colour" not in pack_bins[0].process_name.lower()
    assert all("navy" not in b.process_name.lower() for b in r.bins)
    assert all(re.match(r"B\d+-S1-PLAIN-", b.process_name) for b in r.bins)


def test_printed_under_30_keeps_all_departments_in_one_process() -> None:
    """Graph 30-chain: 29 short-sleeve t-shirts stay one file (all departments/sizes)."""
    cat = Catalogs(
        cl={
            "m-t-blk-m": _cl_row(**{"Department (Areeb)": "Mens", "Size": "M"}),
            "k-t-blk-s": _cl_row(
                **{
                    "Custom Label": "K-T-BLK-S",
                    "Department (Areeb)": "Kids",
                    "Size": "5-6 Years",
                }
            ),
        }
    )
    mens = [_order(f"M{i}", "1-M-T-BLK-M", qty=1, catalogs=cat) for i in range(20)]
    kids = [_order(f"K{i}", "1-K-T-BLK-S", qty=1, catalogs=cat) for i in range(9)]
    r = group_orders(mens + kids, RUN)
    assert r.unmatched == []
    assert len(r.bins) == 1
    name = r.bins[0].process_name
    assert "mens" not in name
    assert "kids" not in name
    assert "5-6_years" not in name
    assert {o.number for o in r.bins[0].orders} == {*[f"M{i}" for i in range(20)], *[f"K{i}" for i in range(9)]}


def test_flag30_blank_brand_stays_in_parent_not_unmatched() -> None:
    """In-house Brand is blank by design. Under 30 it stays on the parent file."""
    cat = Catalogs(
        cl={
            "dtf-ironon-a4": _cl_row(
                **{
                    "Custom Label": "DTF-IronOn-A4",
                    "Supply Method": "In House Manufacture",
                    "Supplier Name": "",
                    "Brand": "",
                    "Size": "A4",
                    "Colour": "Iron On Sticker",
                    "Category (Areeb)": "Iron-On",
                    "Product Type (Areeb)": "Iron-On Transfer",
                    "Product Style (Areeb)": "A4",
                    "Department (Areeb)": "General",
                }
            ),
            "sticker-a4": _cl_row(
                **{
                    "Custom Label": "STICKER-A4",
                    "Supply Method": "In House Manufacture",
                    "Supplier Name": "",
                    "Brand": "",
                    "Size": "A4",
                    "Colour": "",
                    "Category (Areeb)": "Stickers",
                    "Product Type (Areeb)": "Sticker",
                    "Product Style (Areeb)": "A4",
                    "Department (Areeb)": "General",
                }
            ),
        }
    )
    r = group_orders(
        [
            _order("I1", "190867LG-DTF-IronOn-A4", catalogs=cat),
            _order("S1", "802008LG-STICKER-A4", catalogs=cat),
        ],
        RUN,
    )
    assert r.unmatched == []
    assert {o.number for b in r.bins for o in b.orders} == {"I1", "S1"}
    by_name = {b.process_name: {o.number for o in b.orders} for b in r.bins}
    assert by_name["B1000-S1-PRINTED-2-IN HOUSE MANUFACTURE-R-1"] == {"I1"}
    assert by_name["B1050-S1-PRINTED-2-IN HOUSE MANUFACTURE-R-2"] == {"S1"}


def test_flag30_blank_leftover_when_named_value_peels() -> None:
    """30 same-brand peels; the blank-brand cousin stays on the parent, not unmatched."""
    cat = Catalogs(
        cl={
            "m-t-blk-m": _cl_row(),
            "m-t-wht-m": _cl_row(
                **{"Custom Label": "M-T-WHT-M", "Brand": "", "Colour": "White"}
            ),
        }
    )
    gildan = [_order(f"G{i:02d}", "1-M-T-BLK-M", catalogs=cat) for i in range(30)]
    blank = _order("B1", "1-M-T-WHT-M", catalogs=cat)
    r = group_orders(gildan + [blank], RUN)
    assert r.unmatched == []
    peeled = [b for b in r.bins if {o.number for o in b.orders} == {f"G{i:02d}" for i in range(30)}]
    parent = [b for b in r.bins if {o.number for o in b.orders} == {"B1"}]
    assert len(peeled) == 1
    assert len(parent) == 1
    assert re.match(r"B\d+-S1-PRINTED-2-SUPPLY ON DEMAND-R-", peeled[0].process_name)
    assert re.match(r"B\d+-S1-PRINTED-2-SUPPLY ON DEMAND-R-", parent[0].process_name)
    assert peeled[0].process_name != parent[0].process_name
    assert {peeled[0].floor_code, parent[0].floor_code} == {"B1", "B2"}


