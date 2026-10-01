"""Helpers for print_sizes_simulation."""
from __future__ import annotations

import re

import pandas as pd


def nonempty(s) -> bool:
    if pd.isna(s):
        return False
    return str(s).strip() not in ("", "nan")


def extract_mock(pp: str) -> str:
    m = re.search(r"\(M(\d+)\)", pp)
    return f"M{m.group(1)}" if m else ""


def split_positions(pp: str) -> list[str]:
    pp = re.sub(r"\s*\(M\d+\)\s*$", "", pp)
    parts = re.split(r",\s*|\s*&\s*", pp)
    return [p.strip() for p in parts if p.strip()]


AGE_MAP = {
    "1-2 Years": "1-2Y",
    "2-3 Years": "2-3Y",
    "3-4 Years": "3-4Y/YXS",
    "5-6 Years": "5-6Y/YS",
    "7-8 Years": "7-8Y/YM",
    "9-11 Years": "9-11Y/YL",
    "12-13 Years": "12-13Y/YXL",
}

MEN_SIZE = {
    "Small": "Men Small",
    "Medium": "Men Medium",
    "Large": "Men Large",
    "Extra Large": "Men XL",
    "Extra Small": "Men Small",
    "2XL": "Men 2XL",
    "3XL": "Men 3XL",
    "4XL": "Men 4XL",
    "5XL": "Men 5XL",
    "XL": "Men XL",
    "L": "Men Large",
    "M": "Men Medium",
    "S": "Men Small",
}

WOMEN_SIZE = {
    "Small": "Women Small",
    "Medium": "Women Medium",
    "Large": "Women Large",
    "Extra Large": "Women XL",
    "XL": "Women XL",
}


def normalize_db_size_for_print(size_val: str, gender_apparel: str, apparel_sizes: list[str]) -> str:
    """Try to map DB Size + Gender Apparel to Print Sizes Apparel Size key."""
    s = size_val.strip()
    ga = gender_apparel.lower()
    if s in AGE_MAP:
        return AGE_MAP[s]
    if "men" in ga or "mens" in ga or "male" in ga:
        if s in MEN_SIZE:
            return MEN_SIZE[s]
    if "women" in ga or "ladies" in ga or "womens" in ga:
        if s in WOMEN_SIZE:
            return WOMEN_SIZE[s]
    for a in apparel_sizes:
        if s.lower() == a.lower() or s in a:
            return a
    return ""


def db_gender(ga: str) -> str:
    g = ga.lower()
    if "men" in g or "boy" in g:
        return "Men"
    if "women" in g or "ladies" in g or "girl" in g:
        return "Women"
    return ""


def pos_to_print_type(pos_name: str) -> str:
    p = pos_name.lower()
    if "back" in p and "front" not in p:
        return "A3"
    if "pocket" in p or "chest" in p or "neck" in p or "left corner" in p or "right corner" in p:
        return "Neck"
    if "sleeve" in p:
        return "Neck"
    if "front" in p or "center" in p or "centre" in p:
        return "A4"
    return "A4"
