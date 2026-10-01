"""Department, bag type, and product-type mapping for CL classify."""
from __future__ import annotations

import re

import shared.taxonomy_catalog as tax
from shared.areeb_taxonomy.consts import (
    GENDER_GENERAL,
    GENDER_KIDS,
    GENDER_MENS,
    GENDER_UNISEX,
    GENDER_WOMENS,
    _HIVIS_RE,
    _KIDS_RE,
    _MENS_RE,
    _UNISEX_RE,
    _WOMENS_RE,
)
from shared.areeb_taxonomy.garment_tables import _CODE_RE, _IRON_SIZES, _NON_APPAREL
from shared.areeb_taxonomy.values import _fold_ga

def _department_for(ga: str, category: str) -> str:
    if category == tax.CAT_BABY or category == tax.CAT_SETS:
        return GENDER_KIDS
    if category in _NON_APPAREL:
        if category == tax.CAT_HOSP and _KIDS_RE.search(ga):
            return GENDER_KIDS
        return GENDER_GENERAL
    if _KIDS_RE.search(ga):
        return GENDER_KIDS
    if _WOMENS_RE.search(ga):
        return GENDER_WOMENS
    if _UNISEX_RE.search(ga) or _HIVIS_RE.search(ga):
        return GENDER_UNISEX
    if category == tax.CAT_SAFETY or (category == tax.CAT_HEALTH and "scrub" in _fold_ga(ga)):
        return GENDER_UNISEX
    if _MENS_RE.search(ga):
        return GENDER_MENS
    if category in {
        tax.CAT_TEE,
        tax.CAT_SWEAT,
        tax.CAT_POLO,
        tax.CAT_SHIRT,
        tax.CAT_TROUSER,
        tax.CAT_SHORTS,
        tax.CAT_JACKET,
        tax.CAT_FLEECE,
        tax.CAT_GILET,
        tax.CAT_HEALTH,
    }:
        return GENDER_MENS
    return GENDER_GENERAL


def _codes_in(text: str) -> list[str]:
    found = _CODE_RE.findall(text or "")
    out: list[str] = []
    seen: set[str] = set()
    for raw in sorted(found, key=len, reverse=True):
        token = raw.upper()
        if token in _IRON_SIZES or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _first_named_code(text: str) -> str:
    for token in _codes_in(text):
        hit = tax.style_from_code(token)
        if hit:
            return token
    return ""


def _bag_type(ga: str) -> str:
    code = _first_named_code(ga)
    hit = tax.bag_type_from_code(code)
    if hit:
        return hit
    cf = _fold_ga(ga)
    if "backpack" in cf:
        return tax.TYPE_BACKPACK
    if "book bag" in cf:
        return tax.TYPE_BOOK
    if "gymsac" in cf or "gym sac" in cf:
        return tax.TYPE_GYMSAC
    if "pencil" in cf:
        return tax.TYPE_PENCIL
    if "lunch" in cf or "cooler" in cf or "sandwich" in cf:
        return tax.TYPE_LUNCH
    if "drawstring" in cf:
        return tax.TYPE_DRAWSTRING
    if "barrel" in cf or "dance bag" in cf:
        return tax.TYPE_BARREL
    if any(tok in cf for tok in ("tote", "shopper", "bag for life", "china")):
        return tax.TYPE_TOTE
    return tax.TYPE_BAG_ACC


def _product_type(category: str, kind: str, ga: str) -> str:
    code = _first_named_code(ga)
    cf = _fold_ga(ga)
    by_kind = {
        "ironon": tax.TYPE_IRON,
        "bag": _bag_type(ga),
        "cap": tax.head_type_from_code(code) or tax.TYPE_CAP,
        "beanie": tax.head_type_from_code(code) or tax.TYPE_BEANIE,
        "helmet": tax.TYPE_HELMET,
        "sticker": tax.TYPE_STICKER,
        "mug": tax.TYPE_MUG,
        "mask": tax.TYPE_MASK,
        "badge": tax.TYPE_BADGE,
        "card": tax.TYPE_CARD,
        "photo": tax.TYPE_PHOTO,
        "lock": tax.TYPE_LOCK,
        "tutu": tax.TYPE_TUTU,
        "apron": tax.TYPE_APRON,
        "tee_hoodie": tax.TYPE_SET,
        "hi_viz_polo": tax.TYPE_HV_POLO,
        "hi_viz_tee": tax.TYPE_HV_TEE,
        "hi_viz_trouser": tax.TYPE_HV_TROUSER,
        "hi_viz_waistcoat": tax.TYPE_HV_VEST,
        "hi_viz_jacket": tax.TYPE_HV_JACKET,
        "hi_vis": tax.TYPE_HV_VEST,
        "tabard": tax.TYPE_TABARD,
        "tunic": tax.TYPE_TUNIC,
        "scrub": tax.TYPE_SCRUB,
        "jogger": tax.TYPE_JOGGER,
        "shorts": tax.TYPE_SHORTS,
        "rugby": tax.TYPE_RUGBY,
        "gilet": tax.TYPE_GILET,
        "cardigan": tax.TYPE_CARDIGAN,
        "fleece": tax.TYPE_FLEECE,
        "jacket": tax.TYPE_JACKET,
        "woven": tax.TYPE_SHIRT,
        "long_polo": tax.TYPE_LS_POLO,
        "polo": tax.TYPE_SS_POLO,
        "long_sleeve": tax.TYPE_LS_TEE,
        "tank": tax.TYPE_TANK,
        "vest": tax.TYPE_TANK,
        "tee": tax.TYPE_SS_TEE,
    }
    if kind == "baby":
        if "romper" in cf or tax.style_from_code(code) == "Baby Romper":
            return tax.TYPE_ROMPER
        if "body" in cf or tax.style_from_code(code) in {"Baby Body Suit", "Baby Bodysuit"}:
            return tax.TYPE_BODY
        return tax.TYPE_BABY_TEE
    if kind == "hoodie":
        if "full zip" in cf or "full-zip" in cf or "sweat jacket" in cf:
            return tax.TYPE_ZIP_HOODIE
        return tax.TYPE_HOODIE
    if kind == "sweatshirt":
        return tax.TYPE_SWEAT
    if kind == "trouser":
        if "cargo" in cf:
            return tax.TYPE_CARGO
        return tax.TYPE_TROUSER
    if kind in by_kind:
        return by_kind[kind]
    if category == tax.CAT_TEE:
        return tax.TYPE_SS_TEE
    if category == tax.CAT_SWEAT:
        return tax.TYPE_HOODIE
    if category == tax.CAT_POLO:
        return tax.TYPE_SS_POLO
    return category
