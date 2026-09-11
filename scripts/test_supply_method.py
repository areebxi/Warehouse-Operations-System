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
        },
        {
            "Brand": "Fruit of the Loom",
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "Childrens T-Shirt",
            "Gender Apparel": "Kids-T-Shirt",
        },
        {
            "Brand": "",
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "Ladies Short Sleeve T-Shirts",
            "Gender Apparel": "Womens-T-Shirt",
        },
        {
            "Brand": "Fruit Of The Loom",
            "Category (Areeb)": "T-SHIRTS",
            "Product Type (Areeb)": "Mens Long Sleeve T-Shirt",
            "Gender Apparel": "FOTL Mens Valueweight Long Sleeve Baseball T-Shirt",
        },
    ):
        assert classify_cl_row(row) == WAREHOUSE_STOCK, row


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


def test_fotl_vest_is_not_warehouse() -> None:
    vest = {
        "Brand": "Fruit Of The Loom",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "Athletic Vest",
        "Gender Apparel": "FOTL Mens Valueweight Athletic Vest",
    }
    assert classify_cl_row(vest) == SUPPLIER_ON_DEMAND


def test_harvest_pack_name_is_not_a_vest() -> None:
    pack = {
        "Brand Name": "Fruit Of The Loom",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
        "Name": "Pack of 3 - Fruit Of The Loom - Men's Iconic 150 T - Autumn Harvest - S",
    }
    assert classify_packs_row(pack) == WAREHOUSE_STOCK


def test_plain_and_packs_never_in_house() -> None:
    fotl_tee = {
        "Brand": "Fruit Of The Loom",
        "Brand Name": "Fruit of the Loom",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
        "Description": "Men's Valueweight T",
        "Name": "Men's Valueweight T",
    }
    assert classify_plain_row(fotl_tee) == WAREHOUSE_STOCK
    assert classify_packs_row(fotl_tee) == WAREHOUSE_STOCK
    gildan_pack = {
        "Brand Name": "Gildan",
        "Category (Areeb)": "T-SHIRTS",
        "Product Type (Areeb)": "MENS SHORT SLEEVE T-SHIRT",
    }
    assert classify_packs_row(gildan_pack) == SUPPLIER_ON_DEMAND
    assert (
        classify_supply_method(
            brand="Fruit Of The Loom",
            category_areeb="T-SHIRTS",
            product_type="MENS SHORT SLEEVE T-SHIRT",
            allow_in_house=False,
        )
        == WAREHOUSE_STOCK
    )


if __name__ == "__main__":
    test_fotl_tees_are_warehouse()
    test_gildan_and_everything_else_on_demand()
    test_iron_on_and_sticker_in_house_on_cl_only()
    test_fotl_vest_is_not_warehouse()
    test_harvest_pack_name_is_not_a_vest()
    test_plain_and_packs_never_in_house()
    print("ok")
