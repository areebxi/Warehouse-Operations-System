"""String / position helpers for phase5_print_sizes."""
from __future__ import annotations

import re

import pandas as pd

from phase5_maps import (
    AGE_TO_PRINT,
    AGE_TO_SR,
    KNOWN_HUMAN,
    LETTER_TO_MEN_PRINT,
    LETTER_TO_SR,
    PE_AGE,
    RE_CRLF,
    RE_MOCK,
    SUFFIX_TO_NAME,
)


def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    s = RE_CRLF.sub(" ", s)
    return s.strip()


def to_num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s:
        return None
    try:
        n = float(s)
        if n != n:  # NaN
            return None
        return int(n) if n == int(n) else n
    except (TypeError, ValueError):
        return None


def extract_mock(pp: str) -> str:
    m = RE_MOCK.search(pp)
    return f"M{m.group(1)}" if m else ""


def split_positions(pp: str) -> list[str]:
    pp = RE_MOCK.sub("", pp)
    parts = re.split(r"\s*,\s*|\s*&\s*", pp)
    return [p.strip() for p in parts if p.strip()]


def is_age_size(size: str) -> bool:
    s = size.lower()
    return (
        "year" in s
        or size in PE_AGE
        or size in AGE_TO_PRINT
        or size in AGE_TO_SR
        or bool(re.match(r"^\d+-\d+y", s, re.I))
    )


def sr_gender(gender_apparel: str, size: str) -> str:
    if is_age_size(size):
        return "Kids"
    g = gender_apparel.lower()
    if any(x in g for x in ("kid", "child", "youth", "junior", "infant", "baby", "toddler")):
        return "Kids"
    if any(x in g for x in ("women", "woman", "ladies", "lady", "girl", "female")):
        return "Women"
    return "Men"


def map_sr_size(size: str) -> str:
    if size in AGE_TO_SR:
        return AGE_TO_SR[size]
    if size in LETTER_TO_SR:
        return LETTER_TO_SR[size]
    if size in PE_AGE:
        return PE_AGE[size]
    return size


def map_print_sizes_key(size: str) -> str:
    if size in AGE_TO_PRINT:
        return AGE_TO_PRINT[size]
    if size in LETTER_TO_MEN_PRINT:
        return LETTER_TO_MEN_PRINT[size]
    if size in PE_AGE:
        age_sr = PE_AGE[size]
        return AGE_TO_PRINT.get(age_sr, AGE_TO_PRINT.get(age_sr + " Years", ""))
    return ""


def classify(name: str) -> str:
    n = name.lower().strip()
    if not n:
        return "empty"
    if n not in KNOWN_HUMAN and "-" in n:
        return "other"
    if "sleeve" in n or "corner" in n or n == "inside":
        return "other"
    if "pocket" in n or "chest" in n:
        return "pocket"
    if "back" in n:
        return "back"
    if "front" in n:
        return "front"
    return "other"


def infer_printing_position(pos_list: list[str]) -> str:
    kinds = [classify(p) for p in pos_list]
    has_p = "pocket" in kinds
    has_f = "front" in kinds
    has_b = "back" in kinds
    if has_p and has_b:
        return "Left Chest & Back Print"
    if has_f and has_b:
        return "Front & Back Print"
    if has_p:
        return "Left Chest"
    if has_b and not has_f:
        return "Back Print"
    if has_f:
        return "Front Print"
    return ""


def paper_from_printing_size(val: str) -> str:
    s = (val or "").upper()
    if "A3" in s:
        return "A3"
    if "A4" in s:
        return "A4"
    return "A4"


def suffix_name(suffix: str, printing_position: str) -> str:
    suf = (suffix or "").upper()
    if suf in SUFFIX_TO_NAME:
        return SUFFIX_TO_NAME[suf]
    pp = (printing_position or "").strip()
    if pp == "Left Chest":
        return "Front Left Pocket"
    if pp == "Front Print":
        return "Front Center"
    if pp == "Back Print":
        return "Back Center"
    return ""


def kinds_in(names: list[str]) -> set[str]:
    return {classify(n) for n in names if n}


def mm_str(val) -> str:
    if val is None or val == "":
        return ""
    return str(int(val)) if isinstance(val, float) and val == int(val) else str(val)
