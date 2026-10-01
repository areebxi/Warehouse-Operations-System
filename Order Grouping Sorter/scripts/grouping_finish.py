"""Finish gate and catalog line attributes."""
from __future__ import annotations

from typing import Mapping, Optional

from shared.areeb_taxonomy import cell

from catalogs import SRC_PACKS, Catalogs
from grouping_models import LineAttrs, sku_is_plain_override

def finish_for_sku(sku: object, catalogs: Catalogs) -> Optional[str]:
    if sku_is_plain_override(sku):
        return "plain"
    if catalogs.lookup_cl(sku) is not None:
        return "printed"
    if catalogs.lookup_plain(sku) is not None:
        return "plain"
    if catalogs.lookup_packs(sku) is not None:
        return "plain"
    return None


def _row_brand_size_colour(source: str, row: Mapping[str, str]) -> tuple[str, str, str]:
    if source == SRC_PACKS:
        return cell(row.get("Brand Name")), cell(row.get("Pack Size")), ""
    return cell(row.get("Brand")), cell(row.get("Size")), cell(row.get("Colour"))


def attrs_for_sku(
    sku: object, qty: int, catalogs: Catalogs, *, item_name: str = ""
) -> LineAttrs:
    finish = finish_for_sku(sku, catalogs)
    source, row = catalogs.attribute_row(sku)
    if row is None:
        return LineAttrs(
            sku=cell(sku), qty=qty, finish=finish, source=None, item_name=item_name
        )
    brand, size, colour = _row_brand_size_colour(source or "", row)
    return LineAttrs(
        sku=cell(sku),
        qty=qty,
        finish=finish,
        source=source,
        supply_method=cell(row.get("Supply Method")),
        supplier=cell(row.get("Supplier Name")),
        printing_type=cell(row.get("Printing Type")),
        customise=cell(row.get("Customise")),
        category=cell(row.get("Category (Areeb)")),
        product_type=cell(row.get("Product Type (Areeb)")),
        product_style=cell(row.get("Product Style (Areeb)")),
        department=cell(row.get("Department (Areeb)")),
        brand=brand,
        size=size,
        colour=colour,
        item_name=item_name,
        gender_apparel=cell(row.get("Gender Apparel")),
    )


