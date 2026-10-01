"""Plain leftover Areeb classify (no UID / Short Code / SPC)."""
from __future__ import annotations

from shared.areeb_taxonomy.consts import SOURCE_PLAIN_LEFTOVER
from shared.areeb_taxonomy.plain_cat import _plain_cat_type
from shared.areeb_taxonomy.values import AreebValues, cell

def plain_leftover(*, brand: object = "", description: object = "") -> AreebValues:
    """Fill leftover Plain Areeb from the row itself. Category/Type use BTC vocabulary."""
    desc = cell(description)
    brand_s = cell(brand)
    category, product_type = _plain_cat_type(desc)
    if not (category or product_type or brand_s or desc):
        return AreebValues()
    return AreebValues(
        category=category,
        product_type=product_type,
        product_style=brand_s,
        department=desc,
        source=SOURCE_PLAIN_LEFTOVER,
    )
