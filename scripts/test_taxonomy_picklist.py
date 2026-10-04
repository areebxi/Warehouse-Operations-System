"""ponytail: closed taxonomy pick-list — fails if fill can invent a new drive."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import shared.taxonomy_catalog as tax
from shared.areeb_taxonomy import leftover_cl, plain_leftover
from shared.taxonomy_picklist import (
    DIM_CATEGORY,
    DIM_DEPARTMENT,
    DIM_PRODUCT_STYLE,
    DIM_PRODUCT_TYPE,
    DIM_SUBCATEGORY,
    allowed,
    pick,
)


def main() -> None:
    assert pick(DIM_CATEGORY, "t-shirts") == "T-Shirts"
    assert pick(DIM_CATEGORY, "T-SHIRTS") == "T-Shirts"
    assert pick(DIM_CATEGORY, "SWEATSHIRTS AND HOODIES") == "Sweatshirts & Hoodies"
    assert pick(DIM_CATEGORY, "Brand New Category Drive") == ""
    assert pick(DIM_PRODUCT_TYPE, "mens short sleeve t-shirt") == "Short Sleeve T-Shirt"
    assert pick(DIM_PRODUCT_TYPE, "MENS SHORT SLEEVE T-SHIRT") == "Short Sleeve T-Shirt"
    assert pick(DIM_PRODUCT_STYLE, "valueweight") == "Valueweight"
    assert pick(DIM_PRODUCT_STYLE, "BG125L") == "Maxi Fashion Backpack"
    assert pick(DIM_PRODUCT_STYLE, "InventedWidgetStyle") == ""
    assert pick(DIM_SUBCATEGORY, "Mens Short Sleeve T-Shirt") == "Short Sleeve T-Shirt"
    assert pick(DIM_DEPARTMENT, "mens") == "Mens"

    styles = allowed(DIM_PRODUCT_STYLE)
    cats = allowed(DIM_CATEGORY)
    types = allowed(DIM_PRODUCT_TYPE)
    assert len(cats) == len(tax.CATEGORIES)
    assert len(types) == len(tax.PRODUCT_TYPES)
    for name in tax.PRODUCT_STYLES:
        assert name in styles, name
    for code, name in tax.STYLE_BY_CODE.items():
        assert pick(DIM_PRODUCT_STYLE, code) == name, code

    tee = leftover_cl({"Gender_Apparel": "Mens-T-Shirt"})
    assert tee.category == "T-Shirts"
    assert tee.product_type == "Short Sleeve T-Shirt"
    assert tee.product_style == "Standard"
    assert tee.department == "Mens"

    bag = leftover_cl({"Gender_Apparel": "BG-BG125L"})
    assert bag.category == "Bags"
    assert bag.product_type == "Backpack"
    assert bag.product_style == "Maxi Fashion Backpack"

    gym = leftover_cl({"Gender_Apparel": "BG-BG5"})
    assert gym.product_type == "Gymsac"
    assert gym.product_style == "Budget Gymsac"

    invented = leftover_cl({"Gender_Apparel": "Mens UniqueWidget T-Shirt"})
    assert invented.category == "T-Shirts"
    assert invented.product_type == "Short Sleeve T-Shirt"
    assert invented.product_style == ""

    left = plain_leftover(brand="B&C", description="Women's Slim Fit Tee")
    assert left.category == "T-SHIRTS"
    assert left.product_type == "Ladies Short Sleeve T-Shirts"
    assert left.product_style == "B&C"

    print("taxonomy pick-list ok")


if __name__ == "__main__":
    main()
