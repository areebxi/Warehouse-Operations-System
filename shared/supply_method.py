"""Supply Method for grouping — stable façade.

Supervisor lock 2026-09-09, tightened for Custom Label on 2026-09-23.
"""

from __future__ import annotations

from typing import Any

from shared.areeb_taxonomy import cell
from shared.supply_method_rules import (
    WAREHOUSE_BODY_COLOURS,
    WAREHOUSE_GA_TEES,
    WAREHOUSE_TEE_COLOURS,
    is_cl_warehouse_body_suit,
    is_cl_warehouse_tee_colour,
    is_fotl,
    is_fotl_brand,
    is_gildan_brand,
    is_in_house_text,
    is_tshirt,
    is_vest_or_tank,
)

COL = "Supply Method"

WAREHOUSE_STOCK = "Warehouse Stock"
IN_HOUSE_MANUFACTURE = "In House Manufacture"
SUPPLIER_ON_DEMAND = "Supplier On Demand"


def classify_supply_method(
    *,
    brand: object = "",
    category_areeb: object = "",
    product_type: object = "",
    gender_apparel: object = "",
    custom_label: object = "",
    sku: object = "",
    description: object = "",
    allow_in_house: bool,
) -> str:
    """Return one of the three locked cell values. Never blank."""
    if allow_in_house and is_in_house_text(gender_apparel, custom_label, sku):
        return IN_HOUSE_MANUFACTURE
    if is_fotl(brand=brand, gender_apparel=gender_apparel) and is_tshirt(
        category_areeb=category_areeb,
        product_type=product_type,
        gender_apparel=gender_apparel,
        description=description,
    ):
        return WAREHOUSE_STOCK
    return SUPPLIER_ON_DEMAND


def classify_cl_row(row: dict[str, Any]) -> str:
    """CL colour gate. Plain / Packs stay on classify_plain_row / classify_packs_row."""
    gender_apparel = row.get("Gender Apparel")
    custom_label = row.get("Custom Label")
    sku = row.get("Warehouse SKU") or row.get("SKU")
    if is_in_house_text(gender_apparel, custom_label, sku):
        return IN_HOUSE_MANUFACTURE
    if is_cl_warehouse_body_suit(
        department=row.get("Department (Areeb)"),
        colour=row.get("Colour"),
        custom_label=custom_label,
        gender_apparel=gender_apparel,
        product_code=row.get("Supplier Product Code"),
    ):
        return WAREHOUSE_STOCK
    if (
        is_fotl(brand=row.get("Brand"), gender_apparel=gender_apparel)
        and is_tshirt(
            category_areeb=row.get("Category (Areeb)"),
            product_type=row.get("Product Type (Areeb)"),
            gender_apparel=gender_apparel,
        )
        and is_cl_warehouse_tee_colour(row.get("Department (Areeb)"), row.get("Colour"))
    ):
        return WAREHOUSE_STOCK
    return SUPPLIER_ON_DEMAND


def classify_plain_row(row: dict[str, Any]) -> str:
    return classify_supply_method(
        brand=row.get("Brand"),
        category_areeb=row.get("Category (Areeb)"),
        product_type=row.get("Product Type (Areeb)"),
        description=row.get("Description"),
        allow_in_house=False,
    )


def classify_packs_row(row: dict[str, Any]) -> str:
    brand = row.get("Brand Name")
    if not cell(brand):
        brand = row.get("Brand")
    return classify_supply_method(
        brand=brand,
        category_areeb=row.get("Category (Areeb)"),
        product_type=row.get("Product Type (Areeb)"),
        allow_in_house=False,
    )
