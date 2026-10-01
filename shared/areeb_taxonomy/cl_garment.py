"""Garment kind detection from Gender Apparel text."""
from __future__ import annotations

import re

import shared.taxonomy_catalog as tax
from shared.areeb_taxonomy.consts import _HIVIS_RE
from shared.areeb_taxonomy.values import _fold_ga

def _garment_kind(ga: str) -> tuple[str, str] | None:
    """Return (Category, kind) from Gender Apparel text. None = unknown."""
    cf = _fold_ga(ga)
    if not cf:
        return None
    if cf.startswith("dtf-ironon") or cf.startswith("ironon"):
        return tax.CAT_IRON, "ironon"
    if (
        cf.startswith("bg-")
        or cf.startswith("kc-bg")
        or cf.startswith("pc-")
        or cf.startswith("wb-")
        or cf.startswith("cc-w")
        or cf.startswith("eco ")
    ):
        return tax.CAT_BAGS, "bag"
    if cf.startswith("cap-"):
        return tax.CAT_HEAD, "cap"
    if any(
        token in cf
        for token in ("tote", "backpack", "shopper", "keyring", "china bag", "chinabag")
    ):
        return tax.CAT_BAGS, "bag"
    if _HIVIS_RE.search(cf):
        if "polo" in cf:
            return tax.CAT_POLO, "hi_viz_polo"
        if "t-shirt" in cf or "t shirt" in cf:
            return tax.CAT_TEE, "hi_viz_tee"
        if "trouser" in cf:
            return tax.CAT_SAFETY, "hi_viz_trouser"
        if "waist" in cf:
            return tax.CAT_SAFETY, "hi_viz_waistcoat"
        if "jacket" in cf or "bomber" in cf:
            return tax.CAT_SAFETY, "hi_viz_jacket"
        if "helmet" in cf:
            return tax.CAT_SAFETY, "helmet"
        return tax.CAT_SAFETY, "hi_vis"
    if "tutu" in cf:
        return tax.CAT_BABY, "tutu"
    if "waist coat" in cf or "waistcoat" in cf:
        return tax.CAT_SAFETY, "hi_viz_waistcoat"
    if "apron" in cf:
        return tax.CAT_HOSP, "apron"
    if "sticker" in cf:
        return tax.CAT_STICKER, "sticker"
    if cf == "mug" or cf.startswith("mug-"):
        return tax.CAT_MUGS, "mug"
    if "mask" in cf:
        return tax.CAT_ACC, "mask"
    if cf == "badge":
        return tax.CAT_ACC, "badge"
    if cf == "card":
        return tax.CAT_ACC, "card"
    if "photo acrylic" in cf:
        return tax.CAT_ACC, "photo"
    if "drawer lock" in cf:
        return tax.CAT_ACC, "lock"
    if cf == "only-design":
        return tax.CAT_IRON, "ironon"
    if any(
        token in cf
        for token in ("beanie", "snapback", "dad cap", "panel cap", "trucker cap", "pom pom")
    ):
        return tax.CAT_HEAD, "beanie" if "beanie" in cf else "cap"
    if "romper" in cf:
        return tax.CAT_BABY, "baby"
    if "body suit" in cf or "bodysuit" in cf or "toddler" in cf or cf.endswith("-bs"):
        return tax.CAT_BABY, "baby"
    if "tabard" in cf:
        return tax.CAT_HEALTH, "tabard"
    if "tunic" in cf:
        return tax.CAT_HEALTH, "tunic"
    if "scrub" in cf:
        return tax.CAT_HEALTH, "scrub"
    if "t-shirt" in cf and "hoodie" in cf:
        return tax.CAT_SETS, "tee_hoodie"
    if "trouser" in cf:
        return tax.CAT_TROUSER, "trouser"
    if re.search(r"\bshorts\b", cf) and "sleeve" not in cf:
        return tax.CAT_SHORTS, "shorts"
    if "jog" in cf:
        return tax.CAT_TROUSER, "jogger"
    if "rugby" in cf:
        return tax.CAT_SHIRT, "rugby"
    if "polo" in cf:
        if "longsleeve" in cf or "long sleeve" in cf:
            return tax.CAT_POLO, "long_polo"
        return tax.CAT_POLO, "polo"
    if "gilet" in cf or "bodywarmer" in cf or "body warmer" in cf:
        return tax.CAT_GILET, "gilet"
    if "cardigan" in cf:
        return tax.CAT_JACKET, "cardigan"
    if "fleece" in cf:
        return tax.CAT_FLEECE, "fleece"
    if any(
        token in cf
        for token in (
            "softshell",
            "soft shell",
            "outdoor jacket",
            "bomber",
            "padded",
            "active jacket",
        )
    ) or re.search(r"\bjacket\b", cf):
        if "sweat" in cf:
            return tax.CAT_SWEAT, "hoodie"
        return tax.CAT_JACKET, "jacket"
    if "hoodie" in cf or "hooded" in cf:
        return tax.CAT_SWEAT, "hoodie"
    if "sweatshirt" in cf or "crewneck" in cf:
        return tax.CAT_SWEAT, "sweatshirt"
    if "tank" in cf:
        return tax.CAT_TEE, "tank"
    if "vest" in cf:
        return tax.CAT_TEE, "vest"
    if "long sleeve" in cf and ("t-shirt" in cf or "t shirt" in cf or cf.endswith(" t")):
        return tax.CAT_TEE, "long_sleeve"
    if "t-shirt" in cf or "t shirt" in cf or re.search(r"\bt$", cf):
        return tax.CAT_TEE, "tee"
    if "poplin" in cf or "oxford" in cf or re.search(r"\bshirt\b", cf):
        return tax.CAT_SHIRT, "woven"
    return None
