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

