"""Four Areeb 30-chain columns: maps + classify.

Plain / Packs: blank-only copy from BTC / Uneek.
Plain leftover (no UID / Short Code / SPC): Brand + Description; Category/Type from Description in BTC language.
Custom Label: warehouse `cl_standard` from Gender Apparel only. Never BTC, Uneek, Brand, or PE cells.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

AREEB_COLS = (
    "Category (Areeb)",
    "Product Type (Areeb)",
    "Product Style (Areeb)",
    "Department (Areeb)",
)

BTC_SRC = {
    "Category (Areeb)": "Department",
    "Product Type (Areeb)": "Sub Department",
    "Product Style (Areeb)": "Brand",
    "Department (Areeb)": "Description",
}

UNEEK_SRC = {
    "Category (Areeb)": "Category",
    "Product Type (Areeb)": "Product Name",
    "Product Style (Areeb)": "Full Description",
    "Department (Areeb)": "Gender",
}

GENDER_MENS = "Mens"
GENDER_WOMENS = "Womens"
GENDER_KIDS = "Kids"
GENDER_UNISEX = "Unisex"
GENDER_GENERAL = "General"

# Exact Gender Apparel → warehouse 4-tuple. Overrides the pattern engine.
# Tuple: Category, Product Type, Product Style, Department (gender only).
CL_STANDARD_RULES: dict[str, tuple[str, str, str, str]] = {
    "Mens-T-Shirt": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "T-Shirt", GENDER_MENS),
    "Womens-T-Shirt": ("T-SHIRTS", "Ladies Short Sleeve T-Shirts", "T-Shirt", GENDER_WOMENS),
    "Kids-T-Shirt": ("T-SHIRTS", "Childrens T-Shirt", "T-Shirt", GENDER_KIDS),
    "GILDAN Heavy Cotton Adult T-Shirt": (
        "T-SHIRTS",
        "MENS SHORT SLEEVE T-SHIRT",
        "Heavy Cotton",
        GENDER_MENS,
    ),
    "GILDAN Softstyle Adult T-Shirt": (
        "T-SHIRTS",
        "MENS SHORT SLEEVE T-SHIRT",
        "Softstyle",
        GENDER_MENS,
    ),
    "GILDAN Softstyle Ladies T Shirt": (
        "T-SHIRTS",
        "Ladies Short Sleeve T-Shirts",
        "Softstyle",
        GENDER_WOMENS,
    ),
    "GILDAN Softstyle Ladies Tank Top": (
        "T-SHIRTS",
        "Ladies Vests, Camisoles, Etc.",
        "Softstyle Tank",
        GENDER_WOMENS,
    ),
    "FOTL Kids Valueweight T": ("T-SHIRTS", "Childrens T-Shirt", "Valueweight", GENDER_KIDS),
    "5000": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "Heavy Cotton", GENDER_MENS),
    "G5000": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "Heavy Cotton", GENDER_MENS),
    "2400": ("T-SHIRTS", "Mens Long Sleeve T-Shirt", "Ultra Cotton", GENDER_MENS),
    "61026": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "61026", GENDER_MENS),
    "61168-Ringer": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "Ringer", GENDER_MENS),
    "TD02B": ("T-SHIRTS", "Childrens T-Shirt", "TD02B", GENDER_KIDS),
    "CA3001T": ("T-SHIRTS", "Childrens T-Shirt", "CA3001T", GENDER_KIDS),
    "JC003": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "JC003", GENDER_MENS),
    "JC03J": ("T-SHIRTS", "Childrens T-Shirt", "JC03J", GENDER_KIDS),
    "Acid Wash Vintage Rust": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "Acid Wash Vintage Rust", GENDER_MENS),
    "Acid Wash Optic Wash": ("T-SHIRTS", "MENS SHORT SLEEVE T-SHIRT", "Acid Wash Optic Wash", GENDER_MENS),
    "Mens-Hoodie": ("SWEATSHIRTS AND HOODIES", "Mens Sweatshirts & Hoodies", "Hoodie", GENDER_MENS),
    "Mens-Sweatshirt": ("SWEATSHIRTS AND HOODIES", "Mens Sweatshirts & Hoodies", "Sweatshirt", GENDER_MENS),
    "Womens-Sweatshirt": (
        "SWEATSHIRTS AND HOODIES",
        "Ladies Sweatshirts And Hoodies",
        "Sweatshirt",
        GENDER_WOMENS,
    ),
    "Kids-Hoodie": (
        "SWEATSHIRTS AND HOODIES",
        "Childrens Sweatshirts And Hoodies",
        "Hoodie",
        GENDER_KIDS,
    ),
    "Kids-Sweatshirt": (
        "SWEATSHIRTS AND HOODIES",
        "Childrens Sweatshirts And Hoodies",
        "Sweatshirt",
        GENDER_KIDS,
    ),
    "GILDAN Heavy Blend Adult Hooded Sweatshirt": (
        "SWEATSHIRTS AND HOODIES",
        "Mens Sweatshirts & Hoodies",
        "Heavy Blend",
        GENDER_MENS,
    ),
    "GILDAN Softstyle Midw Fleece Youth Hoodie": (
        "SWEATSHIRTS AND HOODIES",
        "Childrens Sweatshirts And Hoodies",
        "Softstyle Midweight Fleece",
        GENDER_KIDS,
    ),
    "GILDAN Softstyle Midweight Fleece Youth Hoodie": (
        "SWEATSHIRTS AND HOODIES",
        "Childrens Sweatshirts And Hoodies",
        "Softstyle Midweight Fleece",
        GENDER_KIDS,
    ),
    "JH001-Hoodie": ("SWEATSHIRTS AND HOODIES", "Mens Sweatshirts & Hoodies", "JH001", GENDER_MENS),
    "JH01J-Hoodie": (
        "SWEATSHIRTS AND HOODIES",
        "Childrens Sweatshirts And Hoodies",
        "JH01J",
        GENDER_KIDS,
    ),
    "C2200-Hoodie": ("SWEATSHIRTS AND HOODIES", "Mens Sweatshirts & Hoodies", "C2200", GENDER_MENS),
    "C2400": ("SWEATSHIRTS AND HOODIES", "Mens Sweatshirts & Hoodies", "C2400", GENDER_MENS),
    "SF500B-Hoodie": (
        "SWEATSHIRTS AND HOODIES",
        "Childrens Sweatshirts And Hoodies",
        "SF500B",
        GENDER_KIDS,
    ),
    "Kids-T-Shirt-Hoodie": ("Sets", "T-Shirt and Hoodie", "Kids Set", GENDER_KIDS),
    "85800L-Polo-T-Shirt": ("POLO SHIRTS", "Ladies Short Sleeve Polo Shirts", "85800L", GENDER_WOMENS),
    "64800-Polo T-Shirt": ("POLO SHIRTS", "MENS SHORT SLEEVE POLO SHIRTS", "64800", GENDER_MENS),
    "UCC003-Mens-Polo": ("POLO SHIRTS", "MENS SHORT SLEEVE POLO SHIRTS", "UCC003", GENDER_MENS),
    "Uneek Hi-Viz Polo Shirt": ("POLO SHIRTS", "Hi-Viz Polo Shirt", "Hi-Viz Polo", GENDER_UNISEX),
    "64200": ("T-SHIRTS", "Mens Tank Tops, Vest Etc", "64200", GENDER_MENS),
    "64200L": ("T-SHIRTS", "Ladies Vests, Camisoles, Etc.", "64200L", GENDER_WOMENS),
    "C800T-BS": ("Babywear", "Baby And Toddlerwear", "C800T", GENDER_KIDS),
    "C8030T-BS": ("Babywear", "Baby And Toddlerwear", "C8030T", GENDER_KIDS),
    "BZ02-Toddler-T-Shirt": ("Babywear", "Baby And Toddlerwear", "BZ02", GENDER_KIDS),
    "BZ10-Body Suit": ("Babywear", "Baby And Toddlerwear", "BZ10", GENDER_KIDS),
    "Kids-Toddler 61033": ("Babywear", "Baby And Toddlerwear", "61033", GENDER_KIDS),
    "China Bag": ("Bags", "Bags, Backpacks Etc", "China Bag", GENDER_GENERAL),
    "Cotton-Shopper": ("Bags", "Bags, Backpacks Etc", "Cotton Shopper", GENDER_GENERAL),
    "BagBase Boutique Wristlet Keyring": (
        "Bags",
        "Bags, Backpacks Etc",
        "Boutique Wristlet Keyring",
        GENDER_GENERAL,
    ),
    "PC-QD442": ("Bags", "Bags, Backpacks Etc", "QD442", GENDER_GENERAL),
    "WB-QD440": ("Bags", "Bags, Backpacks Etc", "QD440", GENDER_GENERAL),
    "W696": ("Bags", "Bags, Backpacks Etc", "W696", GENDER_GENERAL),
    "W265": ("Bags", "Bags, Backpacks Etc", "W265", GENDER_GENERAL),
    "BG745": ("Bags", "Bags, Backpacks Etc", "BG745", GENDER_GENERAL),
    "Yoko Hi-Vis Class 2 Waistcoat": ("Safetywear", "Hi-Vis Waistcoat", "Class 2", GENDER_UNISEX),
    "Hi-Vis-HVW801": ("Safetywear", "Hi-Vis Waistcoat", "HVW801", GENDER_UNISEX),
    "Beechfield Original Patch Beanie": ("HEADWEAR", "Beanie", "Original Patch", GENDER_GENERAL),
    "Beechfield Snowstar Patch Beanie": ("HEADWEAR", "Beanie", "Snowstar Patch", GENDER_GENERAL),
    "BEECH Original Patch Beanie": ("HEADWEAR", "Beanie", "Original Patch", GENDER_GENERAL),
    "BEECH Snowstar Patch Beanie": ("HEADWEAR", "Beanie", "Snowstar Patch", GENDER_GENERAL),
    "Cap-B445": ("HEADWEAR", "Cap", "B445", GENDER_GENERAL),
    "Cap-B641": ("HEADWEAR", "Cap", "B641", GENDER_GENERAL),
    "Westford Mill FairTrade Cotton Junior Apron": (
        "Hospitality",
        "Apron",
        "FairTrade Cotton Junior",
        GENDER_KIDS,
    ),
    "WFMILL FairTrade Cotton Junior Apron": (
        "Hospitality",
        "Apron",
        "FairTrade Cotton Junior",
        GENDER_KIDS,
    ),
    "AA77-Apron": ("Hospitality", "Apron", "AA77", GENDER_GENERAL),
    "W364-Apron": ("Hospitality", "Apron", "W364", GENDER_GENERAL),
    "Sticker": ("Stickers", "Sticker", "Sticker", GENDER_GENERAL),
    "Stickers": ("Stickers", "Sticker", "Circle", GENDER_GENERAL),
    "STICKER": ("Stickers", "Sticker", "A4", GENDER_GENERAL),
    "Mug": ("Mugs", "Mug", "Mug", GENDER_GENERAL),
    "Mug-M61": ("Mugs", "Mug", "M61", GENDER_GENERAL),
    "Mask": ("Masks", "Face Mask", "Face Mask", GENDER_GENERAL),
    "6M014V": ("Masks", "Face Mask", "6M014V", GENDER_GENERAL),
    "Badge": ("Badges", "Badge", "25mm", GENDER_GENERAL),
    "Card": ("Cards", "Card", "A5", GENDER_GENERAL),
    "Photo Acrylic": ("Photo Acrylic", "Photo Acrylic", "Photo Acrylic", GENDER_GENERAL),
    "Baby Drawer Lock": ("Accessories", "Baby Drawer Lock", "Baby Drawer Lock", GENDER_GENERAL),
    "Only-Design": ("Iron-On", "Iron-On Transfer", "Iron-On", GENDER_GENERAL),
    "Kids-Tutu": ("Tutus", "Tutu", "Tutu", GENDER_KIDS),
}

CL_LEFTOVER_RULES = CL_STANDARD_RULES
CL_STANDARD_RULES_FOLD = {k.casefold(): v for k, v in CL_STANDARD_RULES.items()}
CL_LEFTOVER_RULES_FOLD = CL_STANDARD_RULES_FOLD

SOURCE_BTC_UID = "btc_uid"
SOURCE_BTC_SPC = "btc_spc"
SOURCE_UNEEK_SHORT = "uneek_short"
SOURCE_UNEEK_CODE = "uneek_code"
SOURCE_CL_STANDARD = "cl_standard"
SOURCE_CL_GA = SOURCE_CL_STANDARD
SOURCE_CL_EXISTING = "cl_existing"
SOURCE_PLAIN_LEFTOVER = "plain_leftover"
SOURCE_NONE = ""

_KIDS_RE = re.compile(
    r"\b(children'?s|childrens?|kids?|child|youth|infant|bab(?:y|ies)|toddler|junior)\b",
    re.I,
)
_WOMENS_RE = re.compile(r"\b(women'?s|womens?|ladies|lady|girl)\b", re.I)
_PLAIN_KIDS_RE = re.compile(
    r"\b(children'?s|childrens?|kids?|youth|infant|bab(?:y|ies)|toddler|junior|girl'?s|girls|boy'?s|boys)\b",
    re.I,
)
_PLAIN_WOMENS_RE = re.compile(r"\b(women'?s|womens?|ladies|lady)\b", re.I)
_MENS_RE = re.compile(r"\b(men'?s|mens?|male|adults?)\b", re.I)
_UNISEX_RE = re.compile(r"\bunisex\b", re.I)
_HIVIS_RE = re.compile(r"hi[-\s]?vi[sz]", re.I)

_CL_BRAND_PREFIXES = (
    "fruit of the loom",
    "westford mill",
    "wfmill",
    "beechfield",
    "bagbase",
    "bagbas",
    "gildan",
    "fotl",
    "folt",
    "uneek",
    "yoko",
    "delta",
    "beech",
)

_NON_APPAREL = frozenset(
    {
        "Bags",
        "Iron-On",
        "Stickers",
        "Mugs",
        "Masks",
        "Badges",
        "Cards",
        "Photo Acrylic",
        "Accessories",
        "HEADWEAR",
        "Hospitality",
    }
)

_GARMENT_PHRASES = tuple(
    sorted(
        (
            "full zip hooded sweatshirt",
            "full zip micro fleece jacket",
            "full zip microfleece jacket",
            "full zip fleece jacket",
            "full zip soft shell jacket",
            "full zip softshell jacket",
            "full zip fleece",
            "quarter zip microfleece jacket",
            "quarter zip sweatshirt",
            "1/4 zip micro fleece jacket",
            "hooded sweatshirt",
            "crewneck sweatshirt",
            "crew neck sweatshirt",
            "crew neck t-shirt",
            "crew neck t shirt",
            "long sleeve baseball t-shirt",
            "long sleeve poplin shirt",
            "short sleeve poplin shirt",
            "long sleeve t-shirt",
            "long sleeve t shirt",
            "hi viz short sleeve polo shirt",
            "hi-viz short sleeve polo shirt",
            "hi viz short sleeve t shirt",
            "hi-viz short sleeve t shirt",
            "hi-viz polo shirt",
            "hi viz polo shirt",
            "hi-vis class 2 waistcoat",
            "hi-vis baseball safety helmet",
            "childrens hi-viz waist coat",
            "printable softshell gilet",
            "printable soft shell jacket",
            "padded bodywarmer",
            "body warmer",
            "waist coat",
            "waistcoat",
            "athletic vest",
            "tank top",
            "polo shirt",
            "poloshirt",
            "t-shirt",
            "t shirt",
            "sweat jacket",
            "sweatshirt",
            "crewneck",
            "hoodie",
            "hooded",
            "softshell jacket",
            "soft shell jacket",
            "outdoor jacket",
            "fleece jacket",
            "active jacket",
            "bomber jacket",
            "road safety jacket",
            "safety helmet",
            "jogging pants",
            "jog bottoms",
            "cargo shorts",
            "cargo trousers",
            "cargo trouser",
            "trouser regular",
            "trouser long",
            "trouser short",
            "trousers",
            "trouser",
            "rugby shirt",
            "body suit",
            "bodysuit",
            "baseball t-shirt",
            "ringer t",
            "poplin full sleeve shirt",
            "poplin half sleeve shirt",
            "pinpoint oxford full sleeve shirt",
            "pinpoint oxford half sleeve shirt",
            "full sleeve shirt",
            "half sleeve shirt",
            "longsleeve poloshirt",
            "long sleeve",
            "short sleeve",
            "full zip",
            "quarter zip",
            "microfleece",
            "micro fleece",
            "softshell",
            "soft shell",
            "cardigan",
            "gilet",
            "jacket",
            "fleece",
            "beanie",
            "beanies",
            "snapback",
            "trucker cap",
            "dad cap",
            "panel cap",
            "apron",
            "tunic",
            "tabard",
            "scrub",
            "shorts",
            "polo",
            "vest",
            "shirt",
            "tote bag",
            "backpack",
            "shopper",
            "keyring",
            "helmet",
            "mask",
            "mug",
            "sticker",
            "stickers",
            "tutu",
            "bag",
        ),
        key=len,
        reverse=True,
    )
)

_KIND_STYLE = {
    "ironon": "Iron-On",
    "bag": "Bag",
    "cap": "Cap",
    "beanie": "Beanie",
    "helmet": "Helmet",
    "sticker": "Sticker",
    "mug": "Mug",
    "mask": "Face Mask",
    "badge": "Badge",
    "card": "Card",
    "photo": "Photo Acrylic",
    "lock": "Baby Drawer Lock",
    "tutu": "Tutu",
    "apron": "Apron",
    "tee_hoodie": "Kids Set",
    "baby": "Babywear",
    "hi_viz_polo": "Hi-Viz Polo",
    "hi_viz_tee": "Hi-Viz T-Shirt",
    "hi_viz_trouser": "Hi-Viz Trouser",
    "hi_viz_waistcoat": "Hi-Viz Waistcoat",
    "hi_viz_jacket": "Hi-Viz Jacket",
    "hi_vis": "Hi-Vis",
    "hoodie": "Hoodie",
    "sweatshirt": "Sweatshirt",
    "tee": "T-Shirt",
    "long_sleeve": "Long Sleeve",
    "tank": "Tank",
    "vest": "Vest",
    "polo": "Polo",
    "long_polo": "Long Sleeve Polo",
    "woven": "Shirt",
    "trouser": "Trouser",
    "shorts": "Shorts",
    "jogger": "Joggers",
    "jacket": "Jacket",
    "fleece": "Fleece",
    "gilet": "Gilet",
    "cardigan": "Cardigan",
    "rugby": "Rugby Shirt",
    "tunic": "Tunic",
    "scrub": "Scrub",
    "tabard": "Tabard",
}


def cell(value: object) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if s.lower() in ("nan", "none", "none"):
        return ""
    if s.endswith(".0") and s[:-2].isdigit():
        return s[:-2]
    return s


def keyfold(value: object) -> str:
    return cell(value).casefold()


def _norm_ga(ga: object) -> str:
    s = cell(ga)
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("TrouserLong", "Trouser Long")
    s = s.replace("Crew New", "Crewneck")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _fold_ga(ga: object) -> str:
    return _norm_ga(ga).casefold()


@dataclass(frozen=True)
class AreebValues:
    category: str = ""
    product_type: str = ""
    product_style: str = ""
    department: str = ""
    source: str = SOURCE_NONE

    def as_dict(self) -> dict[str, str]:
        return {
            "Category (Areeb)": self.category,
            "Product Type (Areeb)": self.product_type,
            "Product Style (Areeb)": self.product_style,
            "Department (Areeb)": self.department,
        }

    def any_filled(self) -> bool:
        return bool(self.category or self.product_type or self.product_style or self.department)

    def all_filled(self) -> bool:
        return bool(self.category and self.product_type and self.product_style and self.department)


def coalesce_areeb(base: AreebValues, extra: AreebValues) -> AreebValues:
    """Keep supplier cells; fill only the holes from leftover."""
    if not extra.any_filled() or base.all_filled():
        return base
    return AreebValues(
        category=base.category or extra.category,
        product_type=base.product_type or extra.product_type,
        product_style=base.product_style or extra.product_style,
        department=base.department or extra.department,
        source=base.source or extra.source,
    )


def from_src_row(row: Mapping[str, Any], src_map: dict[str, str], source: str) -> AreebValues:
    picked = {areeb: cell(row.get(src)) for areeb, src in src_map.items()}
    return AreebValues(
        category=picked["Category (Areeb)"],
        product_type=picked["Product Type (Areeb)"],
        product_style=picked["Product Style (Areeb)"],
        department=picked["Department (Areeb)"],
        source=source if any(picked.values()) else SOURCE_NONE,
    )


def _values_from_tuple(parts: tuple[str, str, str, str]) -> AreebValues:
    category, product_type, product_style, department = parts
    return AreebValues(
        category=category,
        product_type=product_type,
        product_style=product_style,
        department=department,
        source=SOURCE_CL_STANDARD if any(parts) else SOURCE_NONE,
    )


def _ironon_style(ga: str) -> str:
    lower = ga.casefold()
    for prefix in ("dtf-ironon-", "dtf-ironon", "ironon-", "ironon"):
        if lower.startswith(prefix):
            rest = ga[len(prefix) :].lstrip("-")
            return rest or "Iron-On"
    return "Iron-On"


def _strip_brand(folded: str) -> str:
    for prefix in _CL_BRAND_PREFIXES:
        if folded == prefix:
            return ""
        if folded.startswith(prefix + " ") or folded.startswith(prefix + "-"):
            return folded[len(prefix) :].lstrip(" -")
    return folded


def _title_style(text: str) -> str:
    bits: list[str] = []
    for raw in text.split():
        low = raw.casefold()
        if low in {"ux", "v"}:
            bits.append(raw.upper())
        elif low in {"hi-viz", "hi-vis", "hiviz"}:
            bits.append("Hi-Viz")
        else:
            bits.append(raw[:1].upper() + raw[1:] if raw else raw)
    return " ".join(bits)


def _garment_kind(ga: str) -> tuple[str, str] | None:
    """Return (Category, kind) from Gender Apparel text. None = unknown."""
    cf = _fold_ga(ga)
    if not cf:
        return None
    if cf.startswith("dtf-ironon") or cf.startswith("ironon"):
        return "Iron-On", "ironon"
    if (
        cf.startswith("bg-")
        or cf.startswith("kc-bg")
        or cf.startswith("pc-")
        or cf.startswith("wb-")
        or cf.startswith("cc-w")
        or cf.startswith("eco ")
    ):
        return "Bags", "bag"
    if cf.startswith("cap-"):
        return "HEADWEAR", "cap"
    if any(
        token in cf
        for token in ("tote", "backpack", "shopper", "keyring", "china bag", "chinabag")
    ):
        return "Bags", "bag"
    if _HIVIS_RE.search(cf):
        if "polo" in cf:
            return "POLO SHIRTS", "hi_viz_polo"
        if "t-shirt" in cf or "t shirt" in cf:
            return "T-SHIRTS", "hi_viz_tee"
        if "trouser" in cf:
            return "Safetywear", "hi_viz_trouser"
        if "waist" in cf:
            return "Safetywear", "hi_viz_waistcoat"
        if "jacket" in cf or "bomber" in cf:
            return "Safetywear", "hi_viz_jacket"
        if "helmet" in cf:
            return "Safetywear", "helmet"
        return "Safetywear", "hi_vis"
    if "tutu" in cf:
        return "Tutus", "tutu"
    if "waist coat" in cf or "waistcoat" in cf:
        return "Safetywear", "hi_viz_waistcoat"
    if "apron" in cf:
        return "Hospitality", "apron"
    if "sticker" in cf:
        return "Stickers", "sticker"
    if cf == "mug" or cf.startswith("mug-"):
        return "Mugs", "mug"
    if "mask" in cf:
        return "Masks", "mask"
    if cf == "badge":
        return "Badges", "badge"
    if cf == "card":
        return "Cards", "card"
    if "photo acrylic" in cf:
        return "Photo Acrylic", "photo"
    if "drawer lock" in cf:
        return "Accessories", "lock"
    if cf == "only-design":
        return "Iron-On", "ironon"
    if any(
        token in cf
        for token in ("beanie", "snapback", "dad cap", "panel cap", "trucker cap", "pom pom")
    ):
        return "HEADWEAR", "beanie" if "beanie" in cf else "cap"
    if "body suit" in cf or "bodysuit" in cf or "toddler" in cf or cf.endswith("-bs"):
        return "Babywear", "baby"
    if "tabard" in cf:
        return "Healthcare", "tabard"
    if "tunic" in cf:
        return "Healthcare", "tunic"
    if "scrub" in cf:
        return "Healthcare", "scrub"
    if "t-shirt" in cf and "hoodie" in cf:
        return "Sets", "tee_hoodie"
    if "trouser" in cf:
        return "Trousers", "trouser"
    if re.search(r"\bshorts\b", cf) and "sleeve" not in cf:
        return "Shorts", "shorts"
    if "jog" in cf:
        return "Joggers", "jogger"
    if "rugby" in cf:
        return "Rugby Shirts", "rugby"
    if "polo" in cf:
        if "longsleeve" in cf or "long sleeve" in cf:
            return "POLO SHIRTS", "long_polo"
        return "POLO SHIRTS", "polo"
    if "gilet" in cf or "bodywarmer" in cf or "body warmer" in cf:
        return "Gilets", "gilet"
    if "cardigan" in cf:
        return "Jackets", "cardigan"
    if "fleece" in cf:
        return "Fleeces", "fleece"
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
            return "SWEATSHIRTS AND HOODIES", "hoodie"
        return "Jackets", "jacket"
    if "hoodie" in cf or "hooded" in cf:
        return "SWEATSHIRTS AND HOODIES", "hoodie"
    if "sweatshirt" in cf or "crewneck" in cf:
        return "SWEATSHIRTS AND HOODIES", "sweatshirt"
    if "tank" in cf:
        return "T-SHIRTS", "tank"
    if "vest" in cf:
        return "T-SHIRTS", "vest"
    if "long sleeve" in cf and ("t-shirt" in cf or "t shirt" in cf or cf.endswith(" t")):
        return "T-SHIRTS", "long_sleeve"
    if "t-shirt" in cf or "t shirt" in cf or re.search(r"\bt$", cf):
        return "T-SHIRTS", "tee"
    if "poplin" in cf or "oxford" in cf or re.search(r"\bshirt\b", cf):
        return "Shirts", "woven"
    return None


def _department_for(ga: str, category: str) -> str:
    if category == "Babywear" or category == "Tutus" or category == "Sets":
        return GENDER_KIDS
    if category in _NON_APPAREL:
        if category == "Hospitality" and _KIDS_RE.search(ga):
            return GENDER_KIDS
        return GENDER_GENERAL
    if _KIDS_RE.search(ga):
        return GENDER_KIDS
    if _WOMENS_RE.search(ga):
        return GENDER_WOMENS
    if _UNISEX_RE.search(ga) or _HIVIS_RE.search(ga):
        return GENDER_UNISEX
    if category == "Safetywear" or (category == "Healthcare" and "scrub" in _fold_ga(ga)):
        return GENDER_UNISEX
    if _MENS_RE.search(ga):
        return GENDER_MENS
    if category in {
        "T-SHIRTS",
        "SWEATSHIRTS AND HOODIES",
        "POLO SHIRTS",
        "Shirts",
        "Trousers",
        "Shorts",
        "Jackets",
        "Fleeces",
        "Gilets",
        "Joggers",
        "Rugby Shirts",
        "Healthcare",
    }:
        return GENDER_MENS
    return GENDER_GENERAL


def _product_type(category: str, kind: str, dept: str) -> str:
    by_kind = {
        "ironon": "Iron-On Transfer",
        "bag": "Bags, Backpacks Etc",
        "cap": "Cap",
        "beanie": "Beanie",
        "helmet": "Safety Helmet",
        "sticker": "Sticker",
        "mug": "Mug",
        "mask": "Face Mask",
        "badge": "Badge",
        "card": "Card",
        "photo": "Photo Acrylic",
        "lock": "Baby Drawer Lock",
        "tutu": "Tutu",
        "apron": "Apron",
        "tee_hoodie": "T-Shirt and Hoodie",
        "baby": "Baby And Toddlerwear",
        "hi_viz_polo": "Hi-Viz Polo Shirt",
        "hi_viz_tee": "Hi-Viz T-Shirt",
        "hi_viz_trouser": "Hi-Vis Trouser",
        "hi_viz_waistcoat": "Hi-Vis Waistcoat",
        "hi_viz_jacket": "Hi-Vis Jacket",
        "hi_vis": "Hi-Vis",
        "tabard": "Tabard",
        "tunic": "Tunic",
        "scrub": "Scrub",
        "jogger": "Jog Bottoms",
        "shorts": "Shorts",
        "rugby": "Rugby Shirt",
        "gilet": "Gilet",
        "cardigan": "Cardigan",
        "fleece": "Fleece",
        "jacket": "Jacket",
        "trouser": "Trouser",
        "woven": "Woven Shirt",
        "long_polo": "Long Sleeve Polo Shirt",
    }
    if kind in by_kind:
        if kind == "tunic":
            return {
                GENDER_WOMENS: "Ladies Tunic",
                GENDER_MENS: "Mens Tunic",
                GENDER_UNISEX: "Tunic",
            }.get(dept, "Tunic")
        if kind == "trouser":
            return {
                GENDER_WOMENS: "Ladies Trousers",
                GENDER_KIDS: "Childrens Trousers",
                GENDER_UNISEX: "Trouser",
            }.get(dept, "Mens Trousers")
        if kind == "woven":
            return {
                GENDER_WOMENS: "Ladies Woven Shirt",
                GENDER_KIDS: "Childrens Woven Shirt",
            }.get(dept, "Mens Woven Shirt")
        if kind == "jacket":
            return {
                GENDER_WOMENS: "Ladies Jacket",
                GENDER_KIDS: "Childrens Jacket",
            }.get(dept, "Mens Jacket")
        if kind == "fleece":
            return {
                GENDER_WOMENS: "Ladies Fleece",
                GENDER_KIDS: "Childrens Fleece",
            }.get(dept, "Mens Fleece")
        if kind == "polo":
            return {
                GENDER_WOMENS: "Ladies Short Sleeve Polo Shirts",
                GENDER_KIDS: "Childrens Polo Shirt",
                GENDER_UNISEX: "Unisex Polo Shirt",
            }.get(dept, "MENS SHORT SLEEVE POLO SHIRTS")
        if kind == "long_polo":
            return {
                GENDER_WOMENS: "Ladies Long Sleeve Polo Shirt",
                GENDER_KIDS: "Childrens Long Sleeve Polo Shirt",
            }.get(dept, "Mens Long Sleeve Polo Shirt")
        return by_kind[kind]
    if category == "T-SHIRTS":
        if kind == "long_sleeve":
            return {
                GENDER_WOMENS: "Ladies Long Sleeve T-Shirt",
                GENDER_KIDS: "Childrens Long Sleeve T-Shirt",
            }.get(dept, "Mens Long Sleeve T-Shirt")
        if kind == "tank":
            return {
                GENDER_WOMENS: "Ladies Vests, Camisoles, Etc.",
                GENDER_KIDS: "Childrens Vest",
            }.get(dept, "Mens Tank Tops, Vest Etc")
        if kind == "vest":
            return {
                GENDER_WOMENS: "Ladies Vests, Camisoles, Etc.",
                GENDER_KIDS: "Childrens Vest",
            }.get(dept, "Athletic Vest")
        return {
            GENDER_WOMENS: "Ladies Short Sleeve T-Shirts",
            GENDER_KIDS: "Childrens T-Shirt",
            GENDER_UNISEX: "Unisex T-Shirt",
        }.get(dept, "MENS SHORT SLEEVE T-SHIRT")
    if category == "SWEATSHIRTS AND HOODIES":
        return {
            GENDER_WOMENS: "Ladies Sweatshirts And Hoodies",
            GENDER_KIDS: "Childrens Sweatshirts And Hoodies",
            GENDER_UNISEX: "Unisex Sweatshirts & Hoodies",
        }.get(dept, "Mens Sweatshirts & Hoodies")
    if category == "POLO SHIRTS":
        return {
            GENDER_WOMENS: "Ladies Short Sleeve Polo Shirts",
            GENDER_KIDS: "Childrens Polo Shirt",
            GENDER_UNISEX: "Unisex Polo Shirt",
        }.get(dept, "MENS SHORT SLEEVE POLO SHIRTS")
    return category


def _style_from_ga(ga: str, kind: str) -> str:
    cf = _fold_ga(ga)
    orig = _norm_ga(ga)
    if cf.startswith("dtf-ironon") or cf.startswith("ironon"):
        return _ironon_style(orig)
    if cf.startswith("bg-"):
        return "-".join(orig.split("-")[1:]) or orig
    if cf.startswith("cap-"):
        return orig.split("-", 1)[-1]
    if cf.startswith("pc-") or cf.startswith("wb-") or cf.startswith("kc-") or cf.startswith("cc-"):
        return orig.split("-", 1)[-1]
    hyphen = re.match(r"^([A-Za-z0-9]+)(?:-(hoodie|polo|apron|bs|t-shirt).*)?$", orig, re.I)
    if hyphen and orig.count("-") >= 1 and _garment_kind(orig) and orig.split("-", 1)[0].isalnum():
        head = orig.split("-", 1)[0]
        if head.casefold() not in _CL_BRAND_PREFIXES and not re.search(r"[a-z]{4,}", head.casefold()):
            if any(ch.isdigit() for ch in head) or head.isupper():
                return head
    folded = _strip_brand(cf)
    folded = _KIDS_RE.sub(" ", folded)
    folded = _WOMENS_RE.sub(" ", folded)
    folded = _MENS_RE.sub(" ", folded)
    folded = _UNISEX_RE.sub(" ", folded)
    folded = _HIVIS_RE.sub(" ", folded)
    for phrase in _GARMENT_PHRASES:
        folded = folded.replace(phrase, " ")
    folded = re.sub(r"\s+", " ", folded).strip(" -")
    if folded.endswith(" t"):
        folded = folded[:-2].strip()
    if folded:
        return _title_style(folded)
    return _KIND_STYLE.get(kind, kind.replace("_", " ").title())


def _classify_ga_pattern(ga: str) -> AreebValues:
    hit = _garment_kind(ga)
    if not hit:
        return AreebValues()
    category, kind = hit
    dept = _department_for(ga, category)
    return _values_from_tuple(
        (category, _product_type(category, kind, dept), _style_from_ga(ga, kind), dept)
    )


def cl_standard(row: Mapping[str, Any]) -> AreebValues:
    """Warehouse Areeb 4-tuple from Gender Apparel. Department is gender only."""
    ga = _norm_ga(row.get("Gender Apparel"))
    if not ga:
        return AreebValues()
    exact = CL_STANDARD_RULES.get(ga) or CL_STANDARD_RULES_FOLD.get(ga.casefold())
    if exact:
        return _values_from_tuple(exact)
    return _classify_ga_pattern(ga)


leftover_cl = cl_standard
classify_cl = cl_standard


def _plain_gender(desc: str) -> str:
    if _PLAIN_KIDS_RE.search(desc):
        return GENDER_KIDS
    if _PLAIN_WOMENS_RE.search(desc):
        return GENDER_WOMENS
    if _UNISEX_RE.search(desc):
        return GENDER_UNISEX
    return GENDER_MENS


def _plain_pick(g: str, mens: str, ladies: str, kids: str, unisex: str | None = None) -> str:
    if g == GENDER_KIDS:
        return kids
    if g == GENDER_WOMENS:
        return ladies
    if g == GENDER_UNISEX:
        return unisex or mens
    return mens


def _plain_cat_type(desc: str) -> tuple[str, str]:
    """Map Plain Description → BTC Department / Sub Department. Empty desc → blank."""
    cf = _fold_ga(desc)
    if not cf:
        return "", ""
    g = _plain_gender(desc)
    if _HIVIS_RE.search(cf):
        ptype = "Childrens Hi-Vis" if g == GENDER_KIDS else "Hi Vis Clothing"
        return "Safetywear", ptype
    if any(tok in cf for tok in ("backpack", "tote", "shopper", "holdall", "duffle", "duffel", "rucksack")):
        return "Bags", "Bags, Backpacks Etc"
    if re.search(r"\bbag\b", cf) and "bodybag" not in cf:
        return "Bags", "Bags, Backpacks Etc"
    if any(tok in cf for tok in ("scarf", "neckwarmer", "snood")):
        return "HEADWEAR", "Scarves And Neckwear"
    if any(tok in cf for tok in ("beanie", "snapback", "trucker", "dad cap")) or re.search(
        r"\b(cap|hat|hats)\b", cf
    ):
        return "HEADWEAR", "Caps & Hats Etc"
    if "hoodie" in cf or "hooded" in cf or re.search(r"\bhoody\b", cf):
        return "SWEATSHIRTS AND HOODIES", _plain_pick(
            g,
            "Mens Sweatshirts & Hoodies",
            "Ladies Sweatshirts And Hoodies",
            "Childrens Sweatshirts And Hoodies",
            "UNISEX SWEATSHIRTS & HOODIES",
        )
    if "sweatshirt" in cf or "crewneck" in cf or "crew neck" in cf or re.search(r"\bsweat\b", cf):
        return "SWEATSHIRTS AND HOODIES", _plain_pick(
            g,
            "Mens Sweatshirts & Hoodies",
            "Ladies Sweatshirts And Hoodies",
            "Childrens Sweatshirts And Hoodies",
            "UNISEX SWEATSHIRTS & HOODIES",
        )
    if "polo" in cf:
        if "long sleeve" in cf or "longsleeve" in cf:
            return "POLO SHIRTS", _plain_pick(
                g,
                "Mens Long Sleeve Polo Shirts",
                "Ladies Long Sleeve Polo Shirts",
                "Childrens Polo Shirts",
                "Unisex Polo",
            )
        return "POLO SHIRTS", _plain_pick(
            g,
            "MENS SHORT SLEEVE POLO SHIRTS",
            "Ladies Short Sleeve Polo Shirts",
            "Childrens Polo Shirts",
            "Unisex Polo",
        )
    if "tank" in cf or re.search(r"\bvests?\b", cf):
        return "T-SHIRTS", _plain_pick(
            g,
            "Mens Tank Tops, Vest Etc",
            "Ladies Vests, Camisoles, Etc.",
            "Childrens T-Shirt",
            "UNISEX T-SHIRT",
        )
    if (
        "t-shirt" in cf
        or "t shirt" in cf
        or re.search(r"\btee\b", cf)
        or re.search(r"\bt$", cf)
        or " t/" in cf
        or cf.endswith(" t")
    ):
        if "long sleeve" in cf or "longsleeve" in cf or " lsl" in cf:
            return "T-SHIRTS", _plain_pick(
                g,
                "MENS LONG SLEEVE T-SHIRTS",
                "LADIES LONG SLEEVE T-SHIRTS",
                "Childrens T-Shirt",
                "Unisex Long Sleeve T-Shirt",
            )
        return "T-SHIRTS", _plain_pick(
            g,
            "MENS SHORT SLEEVE T-SHIRT",
            "Ladies Short Sleeve T-Shirts",
            "Childrens T-Shirt",
            "UNISEX T-SHIRT",
        )
    if "softshell" in cf or "soft shell" in cf:
        return "OUTERWEAR", _plain_pick(
            g,
            "Mens Softshell",
            "Ladies Softshell",
            "Childrens jackets",
            "Softshell",
        )
    if "fleece" in cf:
        return "OUTERWEAR", _plain_pick(
            g,
            "Mens Fleeces",
            "Ladies Fleeces",
            "Childrens Fleeces",
            "Unisex Fleece",
        )
    if any(tok in cf for tok in ("gilet", "bodywarmer", "body warmer", "body-warmer")):
        return "OUTERWEAR", _plain_pick(
            g,
            "MENS OUTER JACKETS",
            "Ladies Jackets",
            "Childrens jackets",
            "Unisex Jacket",
        )
    if any(
        tok in cf
        for tok in (
            "windbreaker",
            "jacket",
            "parka",
            "anorak",
            "raincoat",
            "shower",
            "bomber",
            "coat",
        )
    ):
        return "OUTERWEAR", _plain_pick(
            g,
            "MENS OUTER JACKETS",
            "Ladies Jackets",
            "Childrens jackets",
            "Unisex Jacket",
        )
    if any(tok in cf for tok in ("jogger", "jog pant", "jogpant", "sweatpant")) or re.search(
        r"\b(trousers?|pants)\b", cf
    ):
        return "TROUSERS & JOGPANTS", _plain_pick(
            g,
            "MENS TROUSERS AND JOGPANTS",
            "Ladies Trousers And Jog Pants",
            "Childrens Trousers And Jogpants",
            "UNISEX TROUSERS & JOGPANTS",
        )
    if re.search(r"\bshorts\b", cf) and "sleeve" not in cf:
        return "TROUSERS & JOGPANTS", _plain_pick(
            g,
            "Mens Shorts",
            "Ladies Shorts",
            "Childrens Trousers And Jogpants",
            "Mens Shorts",
        )
    if re.search(r"\bdress\b", cf):
        return "Corporate Wear", "Ladies Dress"
    if re.search(r"\bskirt\b", cf):
        return "Corporate Wear", "Ladies Skirts"
    if any(tok in cf for tok in ("apron", "tabard")):
        return "Hospitallity", "Aprons And Tabards"
    if "tunic" in cf:
        return "Hospitallity", "Ladies Tunic" if g != GENDER_MENS else "Aprons And Tabards"
    if "chef" in cf:
        return "Hospitallity", _plain_pick(
            g,
            "Unisex Chefswear",
            "Ladies Chefswear",
            "Unisex Chefswear",
            "Unisex Chefswear",
        )
    if "bib" in cf or "bodysuit" in cf or "body suit" in cf or "romper" in cf:
        return "Babywear", "Baby And Toddlerwear"
    if any(tok in cf for tok in ("knit", "jumper", "cardigan", "sweater")) and "sweatshirt" not in cf:
        return "Knitwear", _plain_pick(
            g,
            "Men's Knitwear",
            "Ladies Knitwear",
            "Men's Knitwear",
            "Men's Knitwear",
        )
    if "midlayer" in cf or "mid layer" in cf:
        return "OUTERWEAR", "Mens Midlayer"
    if any(tok in cf for tok in ("boot", "shoe", "footwear", "trainer")):
        return "Footwear", "Footwear"
    if "glove" in cf:
        return "Accessories", "Gloves"
    if "sock" in cf:
        return "Accessories", "Socks"
    if "poplin" in cf or "oxford" in cf or re.search(r"\bshirts?\b", cf):
        return "Shirts & Blouses", _plain_pick(
            g,
            "Mens Shirts",
            "Ladies Shirts",
            "Mens Shirts",
            "Mens Shirts",
        )
    if "wrap" in cf or "keyring" in cf or "key ring" in cf:
        return "Accessories", "Accessories"
    return "Accessories", "Accessories"


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


class AreebCatalogs:
    """In-memory BTC + Uneek indexes (Plain / Packs only)."""

    def __init__(self) -> None:
        self.btc_by_uid: dict[str, dict[str, str]] = {}
        self.btc_by_spc: dict[str, dict[str, str]] = {}
        self.uneek_by_short: dict[str, dict[str, str]] = {}
        self.uneek_by_code: dict[str, dict[str, str]] = {}

    def btc_uid(self, sku: object) -> AreebValues:
        row = self.btc_by_uid.get(cell(sku)) or self.btc_by_uid.get(keyfold(sku))
        if not row:
            return AreebValues()
        return from_src_row(row, BTC_SRC, SOURCE_BTC_UID)

    def btc_spc(self, code: object) -> AreebValues:
        row = self.btc_by_spc.get(cell(code)) or self.btc_by_spc.get(keyfold(code))
        if not row:
            return AreebValues()
        return from_src_row(row, BTC_SRC, SOURCE_BTC_SPC)

    def uneek_short(self, code: object) -> AreebValues:
        k = cell(code)
        row = self.uneek_by_short.get(k) or self.uneek_by_short.get(k.casefold())
        if not row:
            return AreebValues()
        return from_src_row(row, UNEEK_SRC, SOURCE_UNEEK_SHORT)

    def uneek_product_code(self, code: object) -> AreebValues:
        k = cell(code)
        row = self.uneek_by_code.get(k) or self.uneek_by_code.get(k.casefold())
        if not row:
            return AreebValues()
        return from_src_row(row, UNEEK_SRC, SOURCE_UNEEK_CODE)

    def classify_plain(
        self,
        sku: object,
        product_code: object = "",
        brand: object = "",
        description: object = "",
    ) -> AreebValues:
        leftover = plain_leftover(brand=brand, description=description)
        hit = self.btc_uid(sku)
        if hit.any_filled():
            if hit.all_filled():
                return hit
            return coalesce_areeb(hit, leftover)
        hit = self.uneek_short(sku)
        if hit.any_filled():
            if hit.all_filled():
                return hit
            return coalesce_areeb(hit, leftover)
        hit = self.btc_spc(product_code)
        if hit.any_filled():
            if hit.all_filled():
                return hit
            return coalesce_areeb(hit, leftover)
        return leftover

    def classify_packs(
        self,
        *,
        item1_sku: object = "",
        product_code: object = "",
        channel_child_sku: object = "",
    ) -> AreebValues:
        hit = self.btc_uid(item1_sku)
        if hit.any_filled():
            return hit
        hit = self.btc_spc(product_code)
        if hit.any_filled():
            return hit
        for key in (channel_child_sku, item1_sku, product_code):
            hit = self.uneek_short(key)
            if hit.any_filled():
                return hit
            hit = self.uneek_product_code(key)
            if hit.any_filled():
                return hit
        return AreebValues()

    def classify_cl(self, row: Mapping[str, Any]) -> AreebValues:
        return cl_standard(row)


def _norm_row(row: Mapping[str, Any]) -> dict[str, str]:
    return {str(k): cell(v) for k, v in row.items()}


def load_btc_into(cat: AreebCatalogs, rows: list[Mapping[str, Any]]) -> None:
    for raw in rows:
        row = _norm_row(raw)
        uid = cell(row.get("UID") or row.get("Sku") or row.get("SKU"))
        if not uid or uid.startswith("["):
            continue
        if uid not in cat.btc_by_uid:
            cat.btc_by_uid[uid] = row
            cat.btc_by_uid[uid.casefold()] = row
        spc = cell(row.get("SPC"))
        if spc and spc not in cat.btc_by_spc:
            cat.btc_by_spc[spc] = row
            cat.btc_by_spc[spc.casefold()] = row


def load_uneek_into(cat: AreebCatalogs, rows: list[Mapping[str, Any]]) -> None:
    for raw in rows:
        row = _norm_row(raw)
        short = cell(row.get("Short Code"))
        if short and short not in cat.uneek_by_short:
            cat.uneek_by_short[short] = row
            cat.uneek_by_short[short.casefold()] = row
        code = cell(row.get("Product Code"))
        if code and code not in cat.uneek_by_code:
            cat.uneek_by_code[code] = row
            cat.uneek_by_code[code.casefold()] = row


def load_btc_csv(path: Path) -> list[dict[str, str]]:
    import csv

    last_err: Exception | None = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with path.open(encoding=enc, newline="") as f:
                return [{k: cell(v) for k, v in row.items()} for row in csv.DictReader(f)]
        except UnicodeDecodeError as exc:
            last_err = exc
            continue
    raise last_err or RuntimeError(f"Could not decode {path}")


def load_uneek_xlsx(path: Path) -> list[dict[str, str]]:
    from openpyxl import load_workbook

    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[wb.sheetnames[0]]
        rows_iter = ws.iter_rows(values_only=True)
        headers = [cell(h) for h in next(rows_iter)]
        out: list[dict[str, str]] = []
        for raw in rows_iter:
            row = {headers[i]: cell(raw[i] if i < len(raw) else "") for i in range(len(headers)) if headers[i]}
            if any(row.values()):
                out.append(row)
        return out
    finally:
        wb.close()


def load_catalogs(
    *,
    btc_path: Path | None = None,
    uneek_path: Path | None = None,
) -> AreebCatalogs:
    from shared import paths as wh

    cat = AreebCatalogs()
    load_btc_into(cat, load_btc_csv(btc_path or wh.btc_product_data_path()))
    load_uneek_into(cat, load_uneek_xlsx(uneek_path or wh.uneek_product_data_path()))
    return cat


def apply_blank_only(current: Mapping[str, Any], values: AreebValues) -> dict[str, str]:
    """Return Areeb cells to write: only where current is blank and incoming is non-blank."""
    out: dict[str, str] = {}
    incoming = values.as_dict()
    for col in AREEB_COLS:
        if cell(current.get(col)):
            continue
        val = incoming[col]
        if val:
            out[col] = val
    return out


def apply_areeb(current: Mapping[str, Any], values: AreebValues) -> dict[str, str]:
    """Blank-only for supplier joins. CL standard overwrites all four Areeb cells."""
    if values.source != SOURCE_CL_STANDARD:
        return apply_blank_only(current, values)
    out: dict[str, str] = {}
    for col, val in values.as_dict().items():
        if val and cell(current.get(col)) != val:
            out[col] = val
    return out
