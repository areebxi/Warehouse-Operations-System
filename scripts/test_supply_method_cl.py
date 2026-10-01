"""ponytail: Supply Method lock — fails if FOTL tee / iron-on / Gildan routing drifts."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from shared.supply_method import (
    IN_HOUSE_MANUFACTURE,
    SUPPLIER_ON_DEMAND,
    WAREHOUSE_STOCK,
    classify_cl_row,
    classify_packs_row,
    classify_plain_row,
    classify_supply_method,
)
def test_fotl_tees_are_warehouse() -> None:
    for row in (
        {
            "Brand": "Fruit Of The Loom",
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
            "Gender Apparel": "FOTL Mens Valueweight T",
            "Department (Areeb)": "Mens",
            "Colour": "Azure Blue",
        },
        {
            "Brand": "Fruit of the Loom",
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "Childrens T-Shirt",
            "Gender Apparel": "Kids-T-Shirt",
            "Department (Areeb)": "Kids",
            "Colour": "Sports Grey",
        },
        {
            "Brand": "",
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "Ladies Short Sleeve T-Shirts",
            "Gender Apparel": "Womens-T-Shirt",
            "Department (Areeb)": "Womens",
            "Colour": "Heliconia",
        },
        {
            "Brand": "Fruit Of The Loom",
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "Mens Long Sleeve T-Shirt",
            "Gender Apparel": "FOTL Mens Valueweight Long Sleeve Baseball T-Shirt",
            "Department (Areeb)": "Mens",
            "Colour": "White",
        },
    ):
        assert classify_cl_row(row) == WAREHOUSE_STOCK, row
def test_cl_colour_gate_and_body_suits() -> None:
    deep_navy = {
        "Brand": "Fruit Of The Loom",
        "Category (Areeb)": "T-Shirts",
        "Product Type (Areeb)": "Short Sleeve T-Shirt",
        "Gender Apparel": "FOTL Mens Valueweight T",
        "Department (Areeb)": "Mens",
        "Colour": "Deep Navy",
    }
    assert classify_cl_row(deep_navy) == SUPPLIER_ON_DEMAND
    mens_heliconia = {**deep_navy, "Colour": "Heliconia"}
    assert classify_cl_row(mens_heliconia) == SUPPLIER_ON_DEMAND
    ladies_sports = {
        **deep_navy,
        "Department (Areeb)": "Ladies",
        "Gender Apparel": "Womens-T-Shirt",
        "Colour": "Sports Grey",
    }
    assert classify_cl_row(ladies_sports) == SUPPLIER_ON_DEMAND
    kids_yellow = {
        **deep_navy,
        "Department (Areeb)": "Kids",
        "Gender Apparel": "Kids-T-Shirt",
        "Colour": "Yellow",
    }
    assert classify_cl_row(kids_yellow) == SUPPLIER_ON_DEMAND
    baseball = {**deep_navy, "Colour": "White/Black"}
    assert classify_cl_row(baseball) == SUPPLIER_ON_DEMAND
    body = {
        "Department (Areeb)": "Kids",
        "Product Type (Areeb)": "Body Suit",
        "Gender Apparel": "C800T-BS",
        "Custom Label": "M281-P5-C800T-30-0-3",
        "Colour": "Lemon Yellow",
        "Supplier Name": "Absolute Apparels",
    }
    assert classify_cl_row(body) == WAREHOUSE_STOCK
    romper = {
        **body,
        "Product Type (Areeb)": "Romper",
        "Gender Apparel": "C8030T-BS",
        "Custom Label": "C8030T-WHI-0-3M",
        "Colour": "White",
    }
    assert classify_cl_row(romper) == WAREHOUSE_STOCK
    off_body = {**body, "Colour": "Navy"}
    assert classify_cl_row(off_body) == SUPPLIER_ON_DEMAND
    c8020 = {**body, "Custom Label": "C8020T-BLK-0-3", "Gender Apparel": "C8020T-BS", "Colour": "Black"}
    assert classify_cl_row(c8020) == SUPPLIER_ON_DEMAND
    bz10 = {**body, "Custom Label": "BZ10-BLK", "Gender Apparel": "BZ10-Body Suit", "Colour": "Black"}
    assert classify_cl_row(bz10) == SUPPLIER_ON_DEMAND
def test_gildan_and_everything_else_on_demand() -> None:
    gildan = {
        "Brand": "Gildan",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
        "Gender Apparel": "GILDAN Heavy Cotton Adult T-Shirt",
    }
    assert classify_cl_row(gildan) == SUPPLIER_ON_DEMAND
    hoodie = {
        "Brand": "Fruit Of The Loom",
        "Category (Areeb)": "SWEATSHIRTS AND HOODIES",
        "Product Type (Areeb)": "Mens Sweatshirts & Hoodies",
        "Gender Apparel": "Mens-Hoodie",
    }
    assert classify_cl_row(hoodie) == SUPPLIER_ON_DEMAND
    bag = {
        "Brand": "",
        "Category (Areeb)": "Bags",
        "Product Type (Areeb)": "Bags, Backpacks Etc",
        "Gender Apparel": "BG-China-Bag",
        "Custom Label": "BG-Chinabag-BLK-O/S",
    }
    assert classify_cl_row(bag) == SUPPLIER_ON_DEMAND
    gildan_on_womens_token = {
        "Brand": "GILDAN",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "Ladies Short Sleeve T-Shirts",
        "Gender Apparel": "Womens-T-Shirt",
    }
    assert classify_cl_row(gildan_on_womens_token) == SUPPLIER_ON_DEMAND
def test_iron_on_and_sticker_in_house_on_cl_only() -> None:
    for row in (
        {
            "Gender Apparel": "DTF-IronOn-A4",
            "Custom Label": "DTF-IronOn-A4",
        },
        {
            "Gender Apparel": "Mens-T-Shirt",
            "Custom Label": "M260-P5-iron-on-A4",
        },
        {
            "Gender Apparel": "iron on transfer",
            "Custom Label": "ABC",
        },
        {
            "Gender Apparel": "Sticker",
            "Custom Label": "STICKER-A6",
        },
        {
            "Gender Apparel": "Stickers",
            "Custom Label": "something",
        },
    ):
        assert classify_cl_row(row) == IN_HOUSE_MANUFACTURE, row
        assert classify_plain_row(row) == SUPPLIER_ON_DEMAND, row
    only_design = {
        "Gender Apparel": "Only-Design",
        "Custom Label": "Only-Design",
    }
    assert classify_cl_row(only_design) == SUPPLIER_ON_DEMAND
