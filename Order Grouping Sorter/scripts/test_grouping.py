"""ponytail: sorter grouping lock — fails if finish gate / caps / names drift."""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from catalogs import Catalogs
from grouping import (
    FIXED_BATCH_CODES,
    PERSONALISED_READY_TAG,
    Order,
    attrs_for_sku,
    finish_for_sku,
    group_orders,
    next_open_shift,
    order_numbers_in_date_folder,
    six_field_core,
    slotify,
    write_process_csvs,
)


RUN = date(2026, 9, 11)


def _ready(*extra: str) -> list[str]:
    """Personalised pile needs the ShipStation ready tag (supervisor 2026-09-25)."""
    return [PERSONALISED_READY_TAG, *extra]


def _cl_row(**extra: str) -> dict[str, str]:
    row = {
        "Custom Label": "M-T-BLK-M",
        "Supply Method": "Supplier On Demand",
        "Supplier Name": "BTC Activewear",
        "Printing Type": "DTF",
        "Customise": "",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
        "Product Style (Areeb)": "T-Shirt",
        "Department (Areeb)": "Mens",
        # Not Gildan — B40 peels Brand=Gildan + T-Shirts. Leftover fixtures need another brand.
        "Brand": "Other",
        "Size": "M",
        "Colour": "Black",
    }
    row.update(extra)
    return row


def _gildan_tee_cats(**extra: str) -> Catalogs:
    return Catalogs(cl={"m-t-blk-m": _cl_row(**{"Brand": "Gildan", **extra})}, plain={}, packs={})


def _sweatshirt_cats(**extra: str) -> Catalogs:
    row = _cl_row(
        **{
            "Custom Label": "M-SS-BLK-M",
            "Category (Areeb)": "Sweatshirts & Hoodies",
            "Product Type (Areeb)": "Sweatshirt",
            "Product Style (Areeb)": "Standard",
            "Brand": "Gildan",
            **extra,
        }
    )
    return Catalogs(cl={"m-ss-blk-m": row}, plain={}, packs={})


def _plain_row(**extra: str) -> dict[str, str]:
    row = {
        "SKU": "1243",
        "Supply Method": "Supplier On Demand",
        "Supplier Name": "BTC Activewear",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
        "Product Style (Areeb)": "Valueweight",
        "Department (Areeb)": "Mens Valueweight T",
        "Brand": "Fruit Of The Loom",
        "Size": "M",
        "Colour": "White",
    }
    row.update(extra)
    return row


def _packs_row(**extra: str) -> dict[str, str]:
    row = {
        "Channel Child SKU": "SET4741",
        "Supply Method": "Warehouse Stock",
        "Supplier Name": "BTC Activewear",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
        "Product Style (Areeb)": "Valueweight",
        "Department (Areeb)": "Mens Valueweight T",
        "Brand Name": "Fruit Of The Loom",
        "Pack Size": "5",
    }
    row.update(extra)
    return row


def _cats() -> Catalogs:
    return Catalogs(
        cl={"m-t-blk-m": _cl_row()},
        plain={"1243": _plain_row()},
        packs={"set4741": _packs_row()},
    )


def _order(
    number: str,
    sku: str,
    *,
    qty: int = 1,
    ship: str = "2026-09-11",
    tags: list[str] | None = None,
    store: str = "Amazon UK",
    catalogs: Catalogs | None = None,
    extra_lines: list[tuple[str, int]] | None = None,
    item_name: str = "",
) -> Order:
    cat = catalogs or _cats()
    lines = [attrs_for_sku(sku, qty, cat, item_name=item_name)]
    for extra_sku, extra_qty in extra_lines or []:
        lines.append(attrs_for_sku(extra_sku, extra_qty, cat))
    ship_by = None
    if ship and len(ship) >= 10 and ship[4] == "-" and ship[7] == "-":
        ship_by = date.fromisoformat(ship[:10])
    return Order(
        number=number,
        ship_by_raw=ship,
        ship_by=ship_by,
        tag_names=list(tags or []),
        store_name=store,
        lines=lines,
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


def test_resend_1014_only_and_blank_shipby() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order("R1", "77989LG-M-T-BLK-M", tags=["1014-ALL-RESEND"], catalogs=cat),
            _order("R2", "77989LG-M-T-BLK-M", tags=["1015-ALL-RESEND MANUALLY DISPATCHED"], catalogs=cat),
            _order("B1", "77989LG-M-T-BLK-M", ship="", catalogs=cat),
            _order(
                "M1",
                "77989LG-M-T-BLK-M",
                ship="",
                store="Manual Orders",
                catalogs=cat,
            ),
            _order(
                "E1",
                "77989LG-M-T-BLK-M",
                ship="",
                store="Etsy Apparel Villa",
                catalogs=cat,
            ),
        ],
        RUN,
    )
    assert [o.number for o in r.resend] == ["R1"]
    # Blank ship-by → today for every store (not unmatched).
    assert all(o.unmatched_reason != "blank ship-by" for o in r.unmatched)
    assert all(o.number != "B1" for o in r.unmatched)
    assert all(o.number != "M1" for o in r.unmatched)
    assert all(o.number != "E1" for o in r.unmatched)
    numbered = {o.number for b in r.bins for o in b.orders}
    assert {"B1", "M1", "E1"} <= numbered
    names = {b.process_name for b in r.bins}
    assert any(n.startswith("B1-S1-PRINTED-") for n in names)
    assert "resend" not in names
    assert "RESEND" not in names
    assert "UNMATCHED" not in names


def test_skip_dtfocean_wp_store() -> None:
    from grouping import EXCLUDE_STORES, orders_from_ss

    cat = _cats()
    raw = [
        {
            "orderNumber": "33335",
            "shipByDate": "2026-09-24",
            "storeId": 1,
            "tagIds": [],
            "items": [{"sku": "DTF-Transfer-5M", "name": "Buy DTF Transfer", "quantity": 1}],
        }
    ]
    out, post, empty, skipped = orders_from_ss(
        raw, {}, {1: "DTFOcean.co.uk WP"}, cat
    )
    assert out == []
    assert skipped == 1
    assert post == 0 and empty == 0
    assert "dtfocean.co.uk wp" in EXCLUDE_STORES


def test_fawad_and_prime_and_readymade() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order(
                "F1",
                "77989LG-M-T-BLK-M",
                store="MAS Clothing",
                tags=["Amazon Prime Order"],
                catalogs=cat,
            )
        ],
        RUN,
    )
    assert len(r.bins) == 1
    name = r.bins[0].process_name
    assert name == "B1-S1-PRINTED-1-SUPPLY ON DEMAND-R-1"
    assert r.bins[0].floor_code == "B1"


def test_warehouse_stock_supplier_slot_x() -> None:
    cat = Catalogs(
        cl={
            "m-t-wht-m": _cl_row(
                **{
                    "Custom Label": "M-T-WHT-M",
                    "Supply Method": "Warehouse Stock",
                    "Supplier Name": "BTC Activewear",
                    "Brand": "Fruit Of The Loom",
                    "Colour": "White",
                }
            )
        }
    )
    r = group_orders([_order("W1", "1-M-T-WHT-M", catalogs=cat)], RUN)
    name = r.bins[0].process_name
    assert r.bins[0].floor_code == "B100"
    assert name.startswith("B100-S1-PRINTED-2-WAREHOUSE STOCK-R-")
    assert "btc_activewear" not in name


def test_b50_on_demand_fotl_ready_made() -> None:
    """B50 = B100 twin with Supplier On Demand (locked 2026-09-30)."""
    cat = Catalogs(
        cl={
            "m-t-wht-m": _cl_row(
                **{
                    "Custom Label": "M-T-WHT-M",
                    "Supply Method": "Supplier On Demand",
                    "Supplier Name": "BTC Activewear",
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


def test_mixed_supply_goes_on_demand() -> None:
    cat = Catalogs(
        cl={
            "m-t-blk-2xl-yes": _cl_row(
                **{
                    "Custom Label": "M-T-BLK-2XL-YES",
                    "Supply Method": "Warehouse Stock",
                    "Customise": "Yes",
                }
            ),
            "w407-blk-o/s-yes": _cl_row(
                **{
                    "Custom Label": "W407-BLK-O/S-Yes",
                    "Supply Method": "Supplier On Demand",
                    "Customise": "Yes",
                    "Category (Areeb)": "Bags",
                    "Product Type (Areeb)": "Tote",
                }
            ),
        }
    )
    mixed = _order(
        "MIX",
        "166212LG-M-T-BLK-2XL-Yes",
        catalogs=cat,
        tags=_ready(),
        extra_lines=[("128968LG-W407-BLK-O/S-Yes", 1)],
    )
    r = group_orders([mixed], RUN)
    assert r.unmatched == []
    assert r.held == []
    assert r.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-P-1"


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


def test_slotify() -> None:
    assert slotify("BTC Activewear") == "btc_activewear"
    assert slotify("T-SHIRTS") == "t-shirts"


def test_inside_file_colour_groups_then_parts() -> None:
    cat = Catalogs(
        cl={
            "m-t-blk-m": _cl_row(**{"Colour": "Black"}),
            "m-t-nvy-m": _cl_row(**{"Custom Label": "M-T-NVY-M", "Colour": "Navy"}),
            "m-t-wht-m": _cl_row(**{"Custom Label": "M-T-WHT-M", "Colour": "White"}),
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


def test_blank_customise_is_readymade_not_unmatched() -> None:
    cat = _cats()
    r = group_orders([_order("C1", "77989LG-M-T-BLK-M", catalogs=cat)], RUN)
    assert r.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"
    assert r.unmatched == []


def test_mixed_customised_majority_units_tie_readymade() -> None:
    cat = Catalogs(
        cl={
            "m-t-blk-m": _cl_row(),
            "m-t-wht-m": _cl_row(
                **{"Custom Label": "M-T-WHT-M", "Customise": "Yes"}
            ),
        }
    )
    majority_r = _order(
        "RWIN",
        "77989LG-M-T-BLK-M",
        catalogs=cat,
        extra_lines=[
            ("77989LG-M-T-BLK-M", 1),
            ("77989LG-M-T-BLK-M", 1),
            ("88000LG-M-T-WHT-M", 1),
        ],
    )
    r = group_orders([majority_r], RUN)
    assert r.unmatched == []
    assert r.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"

    # 3 customised units vs 2 readymade lines — units, not line count.
    majority_p = _order(
        "PWIN",
        "88000LG-M-T-WHT-M",
        qty=3,
        catalogs=cat,
        tags=_ready(),
        extra_lines=[("77989LG-M-T-BLK-M", 1), ("77989LG-M-T-BLK-M", 1)],
    )
    r2 = group_orders([majority_p], RUN)
    assert r2.unmatched == []
    assert r2.held == []
    assert r2.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-P-1"

    tie = _order(
        "TIE",
        "77989LG-M-T-BLK-M",
        catalogs=cat,
        extra_lines=[("88000LG-M-T-WHT-M", 1)],
    )
    r3 = group_orders([tie], RUN)
    assert r3.unmatched == []
    assert r3.bins[0].process_name == "B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-1"


def test_write_process_csvs() -> None:
    from tempfile import TemporaryDirectory

    cat = _cats()
    r = group_orders(
        [
            _order("R1", "77989LG-M-T-BLK-M", tags=["1014-ALL-RESEND"], catalogs=cat),
            _order("B1", "77989LG-M-T-BLK-M", ship="", catalogs=cat),
            _order("U1", "NOPE-UNKNOWN", catalogs=cat),
            _order("G1", "77989LG-M-T-BLK-M", catalogs=cat),
        ],
        RUN,
    )
    with TemporaryDirectory() as td:
        root = Path(td)
        day = root / "11-09-2026"
        stale = day / "1st Shift"
        stale.mkdir(parents=True, exist_ok=True)
        (stale / "old-always-split.csv").write_text("stale\n", encoding="utf-8")
        paths = write_process_csvs(r, input_root=root)
        names = {p.name for p in paths}
        assert "RESEND.csv" in names
        assert "UNMATCHED.csv" in names
        assert any(n.startswith("B1-S1-PRINTED-") and n.endswith(".csv") for n in names)
        assert not (stale / "old-always-split.csv").exists()
        assert (day / "1st Shift" / "UNMATCHED.csv").is_file()
        assert not (day / "2nd Shift").exists()
        assert not (day / "3rd Shift").exists()
        text = (day / "1st Shift" / "RESEND.csv").read_text(encoding="utf-8")
        assert text.startswith("Order #,Ship By,Quantity,")
        assert "R1" in text
        unmatched = (day / "1st Shift" / "UNMATCHED.csv").read_text(encoding="utf-8")
        assert "U1" in unmatched
        assert "B1" not in unmatched
        process = next(p for p in paths if p.name.startswith("B1-S1-PRINTED-"))
        process_text = process.read_text(encoding="utf-8")
        assert "G1" in process_text
        assert "B1" in process_text  # blank ship-by → today
        second = day / "2nd Shift"
        second.mkdir(parents=True, exist_ok=True)
        keep = second / "keep-me.csv"
        keep.write_text("Order #\nOLD\n", encoding="utf-8")
        write_process_csvs(r, input_root=root)
        assert keep.is_file()
        assert keep.read_text(encoding="utf-8") == "Order #\nOLD\n"


def _fotl_cats(**extra: str) -> Catalogs:
    return Catalogs(
        cl={
            "m-t-wht-m": _cl_row(
                **{
                    "Custom Label": "M-T-WHT-M",
                    "Supply Method": "Warehouse Stock",
                    "Supplier Name": "BTC Activewear",
                    "Brand": "Fruit Of The Loom",
                    "Colour": "White",
                    **extra,
                }
            )
        }
    )


def _iron_cats(*, customise: str = "") -> Catalogs:
    return Catalogs(
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
                    "Customise": customise,
                }
            )
        }
    )


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
                    "Supply Method": "Warehouse Stock",
                    "Brand": "Fruit Of The Loom",
                    "Colour": "Black",
                    "Department (Areeb)": "Mens",
                }
            ),
            "k-t-blk-s": _cl_row(
                **{
                    "Custom Label": "K-T-BLK-S",
                    "Supply Method": "Warehouse Stock",
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


def test_named_ironon_includes_prime_sticker_is_b1050() -> None:
    iron = _iron_cats()
    sticker = Catalogs(
        cl={
            "sticker-a4": _cl_row(
                **{
                    "Custom Label": "STICKER-A4",
                    "Supply Method": "In House Manufacture",
                    "Supplier Name": "",
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


def test_personalised_without_ready_tag_is_held() -> None:
    cat = _fotl_cats(**{"Customise": "Yes"})
    ready = _order("OK", "1-M-T-WHT-M", catalogs=cat, tags=_ready())
    waiting = _order("WAIT", "1-M-T-WHT-M", catalogs=cat)
    not_ready = _order(
        "NR",
        "1-M-T-WHT-M",
        catalogs=cat,
        tags=["1003-Personalised-Design-Not Ready"],
    )
    r = group_orders([ready, waiting, not_ready], RUN)
    assert {o.number for o in r.held} == {"WAIT", "NR"}
    assert all(o.unmatched_reason == "personalised design not ready" for o in r.held)
    numbered = {o.number for b in r.bins for o in b.orders}
    assert numbered == {"OK"}
    assert "WAIT" not in numbered
    assert r.unmatched == []


def test_six_field_filename_tokens() -> None:
    left = [
        "printed",
        "own",
        "x",
        "prime",
        "dtf",
        "customised",
        "x",
        "x",
        "x",
        slotify("Warehouse Stock"),
        "x",
        "x",
    ]
    assert six_field_core(left, "1st") == "S1-PRINTED-1-WAREHOUSE STOCK-P"
    left[0] = "plain"
    left[3] = "non-prime"
    left[5] = "x"
    left[9] = slotify("Supplier On Demand")
    assert six_field_core(left, "2nd") == "S2-PLAIN-2-SUPPLY ON DEMAND-R"


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


def test_second_run_uses_s2_filename() -> None:
    cat = _cats()
    r = group_orders(
        [_order("G1", "77989LG-M-T-BLK-M", catalogs=cat)],
        RUN,
        shift_slot="2nd",
        shift_folder="2nd Shift",
    )
    assert r.bins[0].process_name == "B1-S2-PRINTED-2-SUPPLY ON DEMAND-R-1"
    assert r.bins[0].shift_folder == "2nd Shift"


def test_next_open_shift_and_written_order_numbers() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        root = Path(td)
        assert next_open_shift(root, RUN) == ("1st", "1st Shift")
        first = root / "11-09-2026" / "1st Shift"
        first.mkdir(parents=True)
        (first / "x.csv").write_text("Order #\nZ1\n", encoding="utf-8")
        assert next_open_shift(root, RUN) == ("2nd", "2nd Shift")
        assert order_numbers_in_date_folder(root, RUN) == {"Z1"}


def test_priority_today_then_prime_then_as_made() -> None:
    cat = _cats()
    r = group_orders(
        [
            _order("TN", "77989LG-M-T-BLK-M", catalogs=cat),
            _order("FN", "77989LG-M-T-BLK-M", ship="2026-09-20", catalogs=cat),
            _order("TP", "77989LG-M-T-BLK-M", tags=["Amazon Prime Order"], catalogs=cat),
        ],
        RUN,
    )
    by = {o.number: b.process_name for b in r.bins for o in b.orders}
    assert by["TP"] == "B1-S1-PRINTED-1-SUPPLY ON DEMAND-R-1"
    assert by["TN"] == "B2-S1-PRINTED-2-SUPPLY ON DEMAND-R-2"
    assert by["FN"] == "B2-S1-PRINTED-2-SUPPLY ON DEMAND-R-2"


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


def test_b40_gildan_b1050_sticker_b3700_sweatshirt() -> None:
    sticker = Catalogs(
        cl={
            "sticker-a4": _cl_row(
                **{
                    "Custom Label": "STICKER-A4",
                    "Supply Method": "In House Manufacture",
                    "Supplier Name": "",
                    "Brand": "",
                    "Category (Areeb)": "Stickers",
                    "Product Type (Areeb)": "Sticker",
                }
            )
        }
    )
    hoodie = Catalogs(
        cl={
            "m-h-blk-m": _cl_row(
                **{
                    "Custom Label": "M-H-BLK-M",
                    "Category (Areeb)": "Sweatshirts & Hoodies",
                    "Product Type (Areeb)": "Hoodie",
                    "Brand": "Gildan",
                }
            )
        }
    )
    # Blank Brand Heavy Cotton — style 5000 in SKU / Gender Apparel
    heavy = Catalogs(
        cl={
            "a3-5000-dhr-xl": _cl_row(
                **{
                    "Custom Label": "A3-5000-DHR-XL",
                    "Brand": "",
                    "Gender Apparel": "5000",
                    "Category (Areeb)": "T-Shirts",
                    "Product Type (Areeb)": "Short Sleeve T-Shirt",
                }
            ),
            "m-t-gd05-blk-m": _cl_row(
                **{
                    "Custom Label": "M-T-GD05-BLK-M",
                    "Brand": "",
                    "Gender Apparel": "G5000",
                    "Category (Areeb)": "T-Shirts",
                    "Product Type (Areeb)": "Short Sleeve T-Shirt",
                }
            ),
            # FOTL UID containing 15000 must NOT count as style 5000
            "m221-15000": _cl_row(
                **{
                    "Custom Label": "M221-15000",
                    "Brand": "Fruit Of The Loom",
                    "Gender Apparel": "FOTL Mens Valueweight Ringer T",
                    "Category (Areeb)": "T-Shirts",
                    "Product Type (Areeb)": "Short Sleeve T-Shirt",
                }
            ),
        }
    )
    r = group_orders(
        [
            _order("G40", "153132LG-M-T-BLK-M", catalogs=_gildan_tee_cats()),
            _order("H5", "999LG-A3-5000-DHR-XL", catalogs=heavy),
            _order("G5", "999LG-M-T-GD05-BLK-M", catalogs=heavy),
            _order("F15", "999LG-M221-15000", catalogs=heavy),
            _order("ST", "190941LG-STICKER-A4", catalogs=sticker),
            _order("SW", "88892LG-M-SS-BLK-M", catalogs=_sweatshirt_cats()),
            _order("HO", "130618LG-M-H-BLK-M", catalogs=hoodie),
            _order("OT", "77989LG-M-T-BLK-M", catalogs=_cats()),
        ],
        RUN,
    )
    by = {o.number: b.floor_code for b in r.bins for o in b.orders}
    assert by["G40"] == "B40"
    assert by["H5"] == "B40"
    assert by["G5"] == "B40"
    assert by["F15"] != "B40"  # 15000 is not style 5000
    assert by["ST"] == "B1050"
    assert by["SW"] == "B3700"
    assert by["HO"] == "B3600"
    assert by["OT"] not in FIXED_BATCH_CODES


def test_2026_09_28_batches_and_priority() -> None:
    fotl = _fotl_cats()
    mug = Catalogs(
        cl={"m61-mug-11oz": _cl_row(**{"Custom Label": "M61-MUG-11OZ", "Printing Type": "Sublimation",
                                         "Category (Areeb)": "Mugs", "Product Type (Areeb)": "Mug"})}
    )
    baby = Catalogs(
        cl={"m281-p6-c800t-30-0>3": _cl_row(**{"Custom Label": "M281-P6-C800T-30-0>3",
                                                "Category (Areeb)": "Babywear",
                                                "Product Type (Areeb)": "Body Suit"})}
    )
    # SKU IronOn wins even when the catalog category is not Iron-On.
    iron_sku = Catalogs(
        cl={"m280-p5-ironon-a6": _cl_row(**{"Custom Label": "M280-P5-IronOn-A6",
                                             "Supply Method": "In House Manufacture",
                                             "Supplier Name": "", "Category (Areeb)": "Other"})}
    )
    ss = _fotl_cats(**{"Custom Label": "M-T-SS-WHT"})
    ss = Catalogs(cl={"m-t-ss-wht": ss.cl["m-t-wht-m"]})
    uneek = Catalogs(cl={}, plain={"uc301": _plain_row(**{"SKU": "UC301", "Supplier Name": "Uneek Clothing"})}, packs={})

    def intl(o: Order) -> Order:
        o.ship_country = "IE"
        return o

    r = group_orders(
        [
            intl(_order("DQI", "179975LG-M-T-BLK-M", item_name="Dancing Queen", catalogs=_cats())),
            intl(_order("INT", "1-M-T-WHT-M", catalogs=fotl)),
            _order("MUG", "5LG-M61-MUG-11OZ", catalogs=mug),
            _order("BABY", "9LG-M281-P6-C800T-30-0>3", catalogs=baby),
            _order("NAMEP", "1-M-T-WHT-M", item_name="Personalised Tee", catalogs=fotl, tags=_ready()),
            _order("SSX", "1-M-T-SS-WHT", catalogs=ss),  # -SS- excluded from B100
            _order("IRSKU", "5LG-M280-P5-IronOn-A6", catalogs=iron_sku),
            _order("PK", "SET4741", catalogs=_cats()),
            _order("UN", "UC301-1", catalogs=uneek),
            _order("PL", "1243-1", catalogs=_cats()),
        ],
        RUN,
    )
    by = {o.number: b.floor_code for b in r.bins for o in b.orders}
    assert by["DQI"] == "B5500"  # peel beats international
    assert by["INT"] == "B10"
    assert by["MUG"] == "B70"
    assert by["BABY"] == "B3100"
    assert by["NAMEP"] == "B4000"  # Item Name Personali → personalised
    assert by["SSX"] != "B100"
    assert by["IRSKU"] == "B1000"
    assert by["PK"] == "B2400"
    assert by["UN"] == "B2300"
    assert by["PL"] == "B2000"  # plain sequence, not B1
    assert r.overlaps["B5500 over B10"] == 1


def test_plain_sequence_skips_reserved() -> None:
    from grouping import next_plain_batch_codes

    assert next_plain_batch_codes(6) == ["B2000", "B2100", "B2200", "B2500", "B2600", "B2700"]


if __name__ == "__main__":
    test_finish_gate_and_attribute_source()
    test_resend_1014_only_and_blank_shipby()
    test_fawad_and_prime_and_readymade()
    test_warehouse_stock_supplier_slot_x()
    test_plain_in_house_unmatched()
    test_printed_wins_and_mixed_flag1_unmatched()
    test_no_dash_sku_matches_cl_whole()
    test_mixed_supply_goes_on_demand()
    test_today_orders_never_held()
    test_future_fill_uses_future_slot_not_iso_date()
    test_flag30_peels_and_packs_skip_colour()
    test_slotify()
    test_inside_file_colour_groups_then_parts()
    test_printed_under_30_keeps_all_departments_in_one_process()
    test_flag30_blank_brand_stays_in_parent_not_unmatched()
    test_flag30_blank_leftover_when_named_value_peels()
    test_blank_customise_is_readymade_not_unmatched()
    test_mixed_customised_majority_units_tie_readymade()
    test_write_process_csvs()
    test_fixed_batch_codes_first_then_graph_leftover()
    test_named_floor_splits_today_future_when_over_mix()
    test_named_floor_fawad_prime_customised_ironon()
    test_named_floor_skips_30chain_and_keeps_inside_file()
    test_named_ironon_includes_prime_sticker_is_b1050()
    test_named_fawad_personalised_fotl_stays_on_run_shift()
    test_personalised_without_ready_tag_is_held()
    test_six_field_filename_tokens()
    test_small_pool_mixes_today_and_future()
    test_today_300_plus_future_splits_by_date()
    test_volume_300_mixes_today_and_later()
    test_volume_over_300_splits_even_if_today_is_small()
    test_named_floor_mixes_today_future_when_small()
    test_second_run_uses_s2_filename()
    test_next_open_shift_and_written_order_numbers()
    test_priority_today_then_prime_then_as_made()
    test_glow_and_sku_contain_fixed_batches()
    test_b40_gildan_b1050_sticker_b3700_sweatshirt()
    test_2026_09_28_batches_and_priority()
    test_plain_sequence_skips_reserved()
    print("ok")
