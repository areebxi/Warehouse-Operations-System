"""Gender-apparel, position, and shirt/size-key helpers for fill_from_seeds."""
from __future__ import annotations

import re

from fill_seeds_maps import (
    AGE_TO_PRINT,
    AGE_TO_SR,
    LETTER_TO_MEN_PRINT,
    LETTER_TO_SR,
    PE_AGE,
    RE_NOT_SHIRT_GA,
    RE_SHIRT_GA,
    RE_SHIRT_SKU,
    SUFFIX_TO_NAME,
)
from fill_seeds_util import clean


def g1_format(text: str) -> str:
    if not text:
        return text
    out: list[str] = []
    for word in text.split():
        if "-" in word:
            out.append("-".join(part.capitalize() for part in word.split("-")))
        else:
            out.append(word.capitalize())
    return " ".join(out)



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
    s = clean(size)
    if not s:
        return ""
    lower = s.lower()
    for src, dest in AGE_TO_PRINT.items():
        if src.lower() == lower:
            return dest
    for src, dest in LETTER_TO_MEN_PRINT.items():
        if src.lower() == lower:
            return dest
    if s in PE_AGE:
        age_sr = PE_AGE[s]
        return AGE_TO_PRINT.get(age_sr, AGE_TO_PRINT.get(age_sr + " Years", ""))
    return ""


def is_shirt_row(gender_apparel: str, custom_label: str, size: str = "") -> bool:
    """All shirt kinds (tee/polo/hoodie/sweat/tank) or a mappable Size band."""
    ga = clean(gender_apparel)
    if RE_NOT_SHIRT_GA.search(ga):
        return False
    if map_print_sizes_key(size):
        return True
    if RE_SHIRT_GA.search(ga):
        return True
    return bool(RE_SHIRT_SKU.search(clean(custom_label)))


def has_exact_mock_uid(custom_label: str, size_index) -> bool:
    m = re.match(r"^(M\d+)-(\d+)$", clean(custom_label).upper())
    if not m:
        return False
    key = f"{m.group(1)} ({m.group(2)})"
    return key in size_index.by_exact_sku


def classify(name: str) -> str:
    """Classify a position name. Kebab-case front/back/pocket still classifies."""
    n = name.lower().strip()
    if not n:
        return "empty"
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


def normalize_gender_apparel_for_sr_sku(gender_apparel: str) -> list[str]:
    s = clean(gender_apparel).upper()
    if not s:
        return []
    cands: list[str] = []
    if s.endswith("-BS") and len(s) > 3:
        base = s[: -len("-BS")]
        if base and base != s:
            cands.append(base)
    if s.startswith("BG-") and len(s) > len("BG-"):
        cands.append(s.replace("BG-", "", 1))
        remainder = s.replace("BG-", "", 1)
        if "CHINA" in remainder and "BAG" in remainder:
            cands.append("BG-" + remainder.replace("-", ""))
    out: list[str] = []
    seen: set[str] = set()
    for x in cands:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out

