"""Supply Method for grouping — stable façade.

Supervisor lock 2026-09-09, tightened for Custom Label on 2026-09-23.
"""

from __future__ import annotations

from typing import Any

from shared import cl_columns as clc
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

# NocoDB Stock_Type column (live CL); Plain/Packs still use spaced "Supply Method".
COL = clc.SUPPLY_METHOD

WAREHOUSE_STOCK = "Warehouse Stock"
IN_HOUSE_MANUFACTURE = "In House Manufacture"
SUPPLIER_ON_DEMAND = "Supplier On Demand"

# Live NocoDB Stock_Type → locked Supply Method trio (supervisor 2026-10-04).
# Blank stays blank. Seasonal/Non-Seasonal are both warehouse stock.
_STOCK_TYPE_MAP = {
    "order on demand": SUPPLIER_ON_DEMAND,
    "supplier on demand": SUPPLIER_ON_DEMAND,
    "warehouse stock": WAREHOUSE_STOCK,
    "warehouse stock (non-seasonal)": WAREHOUSE_STOCK,
    "warehouse stock (seasonal)": WAREHOUSE_STOCK,
    "in house manufacture": IN_HOUSE_MANUFACTURE,
}


def normalize_stock_type(raw: object) -> str:
    """Map NocoDB Stock_Type (or already-locked Supply Method) → locked trio.

    Blank stays blank. Unknown non-blank values pass through unchanged.
    """
    s = cell(raw)
    if not s:
        return ""
    return _STOCK_TYPE_MAP.get(s.casefold(), s)


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
    gender_apparel = row.get(clc.GENDER_APPAREL)
    custom_label = row.get(clc.CUSTOM_LABEL)
    sku = row.get(clc.WAREHOUSE_SKU) or row.get("SKU")
    if is_in_house_text(gender_apparel, custom_label, sku):
        return IN_HOUSE_MANUFACTURE
    if is_cl_warehouse_body_suit(
        department=row.get(clc.DEPARTMENT_AREEB),
        colour=row.get(clc.COLOUR),
        custom_label=custom_label,
        gender_apparel=gender_apparel,
        product_code=row.get(clc.SUPPLIER_PRODUCT_CODE),
    ):
        return WAREHOUSE_STOCK
    if (
        is_fotl(brand=row.get(clc.BRAND), gender_apparel=gender_apparel)
        and is_tshirt(
            category_areeb=row.get(clc.CATEGORY_AREEB),
            product_type=row.get(clc.PRODUCT_TYPE_AREEB),
            gender_apparel=gender_apparel,
        )
        and is_cl_warehouse_tee_colour(
            row.get(clc.DEPARTMENT_AREEB), row.get(clc.COLOUR)
        )
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
