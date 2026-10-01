"""Normalize / map helpers for generate_from_mocks."""
from __future__ import annotations

import re

import pandas as pd

SEED_COLS = [
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
]

SIZE_TO_WORD = {
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "XL": "Extra Large",
    "XS": "Extra Small",
}

AGE_BANDS = {
    "1-2",
    "2-3",
    "3-4",
    "5-6",
    "7-8",
    "9-11",
    "12-13",
    "12-14",
    "14-15",
}

COLOUR_TYPOS = {
    "Fuschia": "Fuchsia",
    "Colbalt Blue": "Cobalt Blue",
    "Sport Grey": "Sports Grey",
    "Light-Pink": "Light Pink",
}
COLOUR_ABBREV = {
    "Dark Heather": "Dark Heather Grey",
    "Azure": "Azure Blue",
}

PRINT_POS_MAP = {
    "Front Print": "Front Center",
    "Back Print": "Back Center",
    "Left Chest": "Front Left Pocket",
    "Front & Back Print": "Front Center, Back Center",
    "Left Chest & Back Print": "Front Left Pocket, Back Center",
    "Front  Print with Both Sleeves": "Front Center, Sleeve",
    "Front Print with Both Sleeves": "Front Center, Sleeve",
    "Front & Back with Both Sleeves": "Front Center, Back Center, Sleeve",
    "Front & Back with Right Sleeve": "Front Center, Back Center, Right Sleeve",
    "Front & Back with Left Sleeve": "Front Center, Back Center, Sleeve",
    "Left Chest & Left Sleeves": "Front Left Pocket, Sleeve",
    "Left Neck & Left Sleeve Bottom": "Front Left Pocket, Sleeve",
    "Front Print & Inside Print": "Front Center, Inside",
    "Front Print & Front Pocket": "Front Center, Front Left Pocket",
}

RE_CRLF = re.compile(r"[\r\n]+")
RE_SPECIAL = re.compile(r"[^A-Za-z0-9 ,\-/().+#]")


def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return RE_CRLF.sub(" ", s).strip()


def strip_special(text: str) -> str:
    """Remove special chars (™, &, apostrophe, etc.); keep dash/comma/basic punctuation."""
    s = clean(text)
    if not s:
        return ""
    s = s.replace("&", " and ")
    s = s.replace("*", " x ")
    s = RE_SPECIAL.sub("", s)
    s = re.sub(r" {2,}", " ", s).strip()
    s = re.sub(r"-{2,}", "-", s)
    return s.strip(" -")


def apparel_image_slug(*parts: str) -> str:
    combined = " ".join(p for p in (strip_special(x) for x in parts) if p)
    if not combined:
        return ""
    slug = re.sub(r"\s+", "-", combined)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def normalize_description(description: str) -> str:
    """Normalize PE Description for Gender Apparel (match existing FOTL-style names)."""
    desc = clean(description)
    if not desc:
        return ""
    desc = desc.replace("Men's", "Mens")
    desc = desc.replace("Kid's", "Kids")
    desc = desc.replace("Ladies'", "Ladies")
    desc = desc.replace("Women's", "Womens")
    return strip_special(desc)


def gender_apparel_from_pe(brand_code: str, description: str) -> str:
    """Gender Apparel = '{Brand Code} {Description}'."""
    code = strip_special(brand_code)
    desc = normalize_description(description)
    if not code or not desc:
        return ""
    return f"{code} {desc}".strip()


def normalize_size(size: str) -> str:
    s = strip_special(size)
    if not s:
        return ""
    if s in SIZE_TO_WORD:
        return SIZE_TO_WORD[s]
    if s in AGE_BANDS:
        return f"{s} Years"
    if re.fullmatch(r"\d+-\d+", s):
        return f"{s} Years"
    if s.endswith(" Years"):
        return s
    return s


def normalize_colour(colour: str) -> str:
    c = strip_special(colour)
    if not c:
        return ""
    c = COLOUR_TYPOS.get(c, c)
    c = COLOUR_ABBREV.get(c, c)
    return c


def map_print_positions(printing_position: str, mock_id: str) -> str:
    pp = clean(printing_position)
    key = re.sub(r"\s+", " ", pp).strip()
    mapped = PRINT_POS_MAP.get(pp) or PRINT_POS_MAP.get(key)
    if not mapped:
        for k, v in PRINT_POS_MAP.items():
            if re.sub(r"\s+", " ", k).strip() == key:
                mapped = v
                break
    if not mapped:
        return ""
    if "," in mapped:
        return f"{mapped} ({mock_id})"
    return mapped


def split_product_codes(raw: str) -> list[str]:
    """Split '61082-61430-61036' or '18000 / 18000B' into SPC tokens."""
    s = clean(raw)
    if not s or s.upper() in ("N/A", "NA"):
        return []
    s = s.replace("/", "-")
    parts = []
    for tok in re.split(r"[\s\-]+", s):
        tok = tok.strip()
        if tok and tok.upper() not in ("N/A", "NA"):
            parts.append(tok)
    return parts
