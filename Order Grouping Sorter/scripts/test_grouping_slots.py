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
                    "Custom_Label": "M-T-WHT-M",
                    "Stock_Type": "Warehouse Stock",
                    "Supplier_Name": "BTC Activewear",
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


def test_mixed_supply_goes_on_demand() -> None:
    cat = Catalogs(
        cl={
            "m-t-blk-2xl-yes": _cl_row(
                **{
                    "Custom_Label": "M-T-BLK-2XL-YES",
                    "Stock_Type": "Warehouse Stock",
                    "Customise": "Yes",
                }
            ),
            "w407-blk-o/s-yes": _cl_row(
                **{
                    "Custom_Label": "W407-BLK-O/S-Yes",
                    "Stock_Type": "Supplier On Demand",
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


