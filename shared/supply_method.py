"""Supply Method for grouping: one warehouse rule on CL, Plain, and Packs.

Supervisor lock 2026-09-09:
  Warehouse Stock        = Fruit of the Loom men / women / kids t-shirts only
  In House Manufacture   = Custom Label SKU or Gender Apparel contains
                           iron on / ironon / iron-on / sticker
                           (CL / printed only; plain cannot be in-house)
  Supplier On Demand     = Gildan t-shirts and everything else

Do not reuse CL column `Warehouse Stock` (Yes on China bags — not this split).
"""

from __future__ import annotations

import re
from typing import Any

from shared.areeb_taxonomy import cell

COL = "Supply Method"

WAREHOUSE_STOCK = "Warehouse Stock"
IN_HOUSE_MANUFACTURE = "In House Manufacture"
SUPPLIER_ON_DEMAND = "Supplier On Demand"

# Gender Apparel tokens used for the warehouse FOTL tee lines when Brand is blank.
WAREHOUSE_GA_TEES = frozenset({"Mens-T-Shirt", "Womens-T-Shirt", "Kids-T-Shirt"})

# Word-boundary: "Harvest" must not count as a vest.
_VEST_RE = re.compile(r"\b(?:vests?|tanks?|camisoles?)\b", re.I)


def _fold(value: object) -> str:
    return cell(value).casefold()


def _compact(value: object) -> str:
    return "".join(ch for ch in _fold(value) if ch.isalnum())


def is_gildan_brand(brand: object) -> bool:
    return "gildan" in _fold(brand)


def is_fotl_brand(brand: object) -> bool:
    folded = _fold(brand)
    if not folded:
        return False
    if "fruit" in folded and "loom" in folded:
        return True
    compact = _compact(brand)
    return compact in {"fotl", "folt"} or compact.startswith("fotl") or compact.startswith("folt")


def is_in_house_text(*parts: object) -> bool:
    """SKU / Gender Apparel contains iron on, ironon, iron-on, or sticker."""
    blob = "".join(_compact(p) for p in parts)
    return "ironon" in blob or "sticker" in blob


def is_vest_or_tank(
    *,
    product_type: object = "",
    gender_apparel: object = "",
    description: object = "",
) -> bool:
    blob = " ".join((_fold(product_type), _fold(gender_apparel), _fold(description)))
    return bool(_VEST_RE.search(blob))


def is_tshirt(
    *,
    category_areeb: object = "",
    product_type: object = "",
    gender_apparel: object = "",
    description: object = "",
) -> bool:
    if cell(category_areeb).upper() != "T-SHIRTS":
        return False
    return not is_vest_or_tank(
        product_type=product_type,
        gender_apparel=gender_apparel,
        description=description,
    )


def is_fotl(
    *,
    brand: object = "",
    gender_apparel: object = "",
) -> bool:
    """Fruit of the Loom identity. Gildan brand always wins (on-demand)."""
    if is_gildan_brand(brand):
        return False
    if is_fotl_brand(brand):
        return True
    ga = cell(gender_apparel)
    ga_fold = ga.casefold()
    if (
        ga_fold.startswith("fotl")
        or ga_fold.startswith("folt")
        or ga_fold.startswith("fruit of the loom")
    ):
        return True
    if ga in WAREHOUSE_GA_TEES:
        return not cell(brand) or is_fotl_brand(brand)
    return False


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
    return classify_supply_method(
        brand=row.get("Brand"),
        category_areeb=row.get("Category (Areeb)"),
        product_type=row.get("Product Type (Areeb)"),
        gender_apparel=row.get("Gender Apparel"),
        custom_label=row.get("Custom Label"),
        sku=row.get("Warehouse SKU") or row.get("SKU"),
        allow_in_house=True,
    )


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
