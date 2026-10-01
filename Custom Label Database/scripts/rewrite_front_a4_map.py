"""Front-print A4 size mapping helpers."""
from __future__ import annotations

import re

from fill_from_seeds import clean, map_print_sizes_key

RE_SR_KEY = re.compile(r"^(M\d+)\s*\((\d+)\)\s*$", re.I)
RE_CL_KEY = re.compile(r"^(M\d+)-(\d+)$", re.I)
POCKET_SUFFIX = frozenset({"P", "S", "S1", "S2"})


def map_size(size: str, ps: dict) -> str:
    key = map_print_sizes_key(size)
    if key and key in ps:
        return key
    s = clean(size)
    aliases = {
        "xs": "Small",
        "extra small": "Small",
        "s": "Small",
        "m": "Medium",
        "l": "Large",
        "small": "Small",
        "medium": "Medium",
        "large": "Large",
        "xl": "XL",
        "2xl": "2XL",
        "xxl": "2XL",
        "3xl": "3XL",
        "4xl": "4XL",
        "5xl": "5XL",
        "14-15y": "Small",
        "14-15 years": "Small",
        "12-14 years": "Small",
        "12-14y": "Small",
    }
    a = aliases.get(s.casefold(), "")
    if a in ps:
        return a
    m = re.match(r"^(\d+)-(\d+)Y$", s, re.I)
    if m:
        age = f"{m.group(1)}-{m.group(2)} Years"
        k2 = map_print_sizes_key(age)
        if k2 in ps:
            return k2
        for pk in ps:
            if age.casefold() in pk.casefold():
                return pk
    return ""


def expected_a4(size: str, ps: dict) -> tuple[int, int] | None:
    key = map_size(size, ps)
    if not key or "A4" not in ps[key]:
        return None
    w, h = ps[key]["A4"]
    return int(w), int(h)


def _is_front_pos_name(name: str) -> bool:
    n = clean(name).casefold()
    if not n:
        return True
    if "pocket" in n or "chest" in n or "sleeve" in n:
        return False
    if "back" in n and "front" not in n:
        return False
    return "front" in n or n in ("front center", "front print", "front centre")


def _cl_is_front_slot1(row: dict) -> bool:
    pos1 = clean(row.get("Position 1 Name"))
    if pos1:
        return _is_front_pos_name(pos1)
    pp = clean(row.get("Print Positions")).casefold()
    if not pp:
        return True
    if "pocket" in pp or "chest" in pp:
        return False
    if "back" in pp and "front" not in pp:
        return False
    return "front" in pp
