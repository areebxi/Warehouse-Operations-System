"""Supplier Name for grouping: BTC Activewear / Uneek Clothing / Absolute Apparels.

Supervisor lock 2026-09-09:
  BTC Activewear      = BTC Product Data UID or SPC, leftover numeric SKU, Packs BTC
  Uneek Clothing      = Uneek Short Code or Product Code
  Absolute Apparels   = babysuits purchased from Absolute only
                        (styles C800T / C8020T / C8030T)
  (blank)             = CL in-house iron-on / sticker — no supplier

Absolute Product Data is a full wholesale price list. The warehouse only
buys babysuits from them. Do not mark Gildan / bodywarmers / polos as Absolute
just because they appear on that sheet.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from shared import cl_columns as clc
from shared.areeb_taxonomy import cell
from shared.supply_method import is_in_house_text

COL = clc.SUPPLIER_NAME

BTC_ACTIVEWEAR = "BTC Activewear"
UNEEK_CLOTHING = "Uneek Clothing"
ABSOLUTE_APPARELS = "Absolute Apparels"

# Absolute sheet: C800T Body Suit Baby, C8020T L/S Body Suit Baby, C8030T Romper Suit Baby.
ABSOLUTE_BABY_STYLES = frozenset({"C800T", "C8020T", "C8030T"})

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokens(*parts: object) -> set[str]:
    out: set[str] = set()
    for part in parts:
        out.update(_TOKEN_RE.findall(cell(part).upper()))
    return out


def is_absolute_babysuit(
    *parts: object,
    styles: Iterable[str] = ABSOLUTE_BABY_STYLES,
) -> bool:
    """True when SKU / Gender Apparel / product code contains an Absolute babysuit style."""
    wanted = {cell(s).upper() for s in styles if cell(s)}
    return bool(_tokens(*parts) & wanted)


def _in_map(index: dict[str, Any], key: object) -> bool:
    k = cell(key)
    if not k:
        return False
    return k in index or k.casefold() in index


def join_supplier(
    *,
    sku: object = "",
    product_code: object = "",
    extra_keys: tuple[object, ...] = (),
    cat: Any,
) -> str:
    """BTC UID, else Uneek short, else BTC SPC, else Uneek product code, else BTC."""
    keys = (sku, *extra_keys)
    for key in keys:
        if _in_map(cat.btc_by_uid, key):
            return BTC_ACTIVEWEAR
    for key in keys:
        if _in_map(cat.uneek_by_short, key):
            return UNEEK_CLOTHING
    if _in_map(cat.btc_by_spc, product_code):
        return BTC_ACTIVEWEAR
    for key in (product_code, sku, *extra_keys):
        if _in_map(cat.uneek_by_code, key):
            return UNEEK_CLOTHING
        if _in_map(cat.uneek_by_short, key):
            return UNEEK_CLOTHING
    return BTC_ACTIVEWEAR


def classify_supply_name(
    *,
    sku: object = "",
    product_code: object = "",
    gender_apparel: object = "",
    custom_label: object = "",
    extra_keys: tuple[object, ...] = (),
    allow_blank_in_house: bool,
    cat: Any,
) -> str:
    if allow_blank_in_house and is_in_house_text(gender_apparel, custom_label, sku):
        return ""
    if is_absolute_babysuit(custom_label, gender_apparel, sku, product_code, *extra_keys):
        return ABSOLUTE_APPARELS
    return join_supplier(
        sku=sku,
        product_code=product_code,
        extra_keys=extra_keys,
        cat=cat,
    )


def classify_cl_row(row: dict[str, Any], cat: Any) -> str:
    label = row.get(clc.CUSTOM_LABEL)
    return classify_supply_name(
        sku=row.get(clc.SUPPLIER_SKU) or row.get(clc.WAREHOUSE_SKU),
        product_code=row.get(clc.SUPPLIER_PRODUCT_CODE),
        gender_apparel=row.get(clc.GENDER_APPAREL),
        custom_label=label,
        extra_keys=(label,),
        allow_blank_in_house=True,
        cat=cat,
    )


def classify_plain_row(row: dict[str, Any], cat: Any) -> str:
    return classify_supply_name(
        sku=row.get("SKU"),
        product_code=row.get("Product Code"),
        allow_blank_in_house=False,
        cat=cat,
    )


def classify_packs_row(row: dict[str, Any], cat: Any) -> str:
    return classify_supply_name(
        sku=row.get("Item 1 SKU"),
        product_code=row.get("Product Code"),
        extra_keys=(row.get("Channel Child SKU"),),
        allow_blank_in_house=False,
        cat=cat,
    )
