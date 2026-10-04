"""Finish gate and catalog line attributes."""
from __future__ import annotations

from typing import Mapping, Optional

from shared import cl_columns as clc
from shared.areeb_taxonomy import cell
from shared.supply_method import normalize_stock_type

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
    # CL uses NocoDB underscored headers; Plain/Packs keep spaced warehouse names.
    return LineAttrs(
        sku=cell(sku),
        qty=qty,
        finish=finish,
        source=source,
        supply_method=normalize_stock_type(
            row.get(clc.SUPPLY_METHOD) or row.get("Supply Method")
        ),
        supplier=cell(row.get(clc.SUPPLIER_NAME) or row.get("Supplier Name")),
        printing_type=cell(row.get(clc.PRINTING_TYPE) or row.get("Printing Type")),
        customise=cell(row.get(clc.CUSTOMISE) or row.get("Customise")),
        category=cell(row.get(clc.CATEGORY_AREEB)),
        product_type=cell(row.get(clc.PRODUCT_TYPE_AREEB)),
        product_style=cell(row.get(clc.PRODUCT_STYLE_AREEB)),
        department=cell(row.get(clc.DEPARTMENT_AREEB)),
        brand=brand,
        size=size,
        colour=colour,
        item_name=item_name,
        gender_apparel=cell(
            row.get(clc.GENDER_APPAREL) or row.get("Gender Apparel")
        ),
    )


