"""Shared fixtures for sorter grouping tests."""
from __future__ import annotations

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
    next_plain_batch_codes,
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
        "Custom_Label": "M-T-BLK-M",
        "Stock_Type": "Supplier On Demand",
        "Supplier_Name": "BTC Activewear",
        "Printing_Type": "DTF",
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
            "Custom_Label": "M-SS-BLK-M",
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


def _fotl_cats(**extra: str) -> Catalogs:
    return Catalogs(
        cl={
            "m-t-wht-m": _cl_row(
                **{
                    "Custom_Label": "M-T-WHT-M",
                    "Stock_Type": "Warehouse Stock",
                    "Supplier_Name": "BTC Activewear",
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
                    "Custom_Label": "DTF-IronOn-A4",
                    "Stock_Type": "In House Manufacture",
                    "Supplier_Name": "",
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


