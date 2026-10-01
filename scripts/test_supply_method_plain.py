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
from test_supply_method_cl import (
    test_fotl_tees_are_warehouse,
    test_cl_colour_gate_and_body_suits,
    test_gildan_and_everything_else_on_demand,
    test_iron_on_and_sticker_in_house_on_cl_only,
)
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
