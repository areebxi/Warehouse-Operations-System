"""Constants and SKU string helpers for size_code_logic."""
from __future__ import annotations

import re

import pandas as pd

FLAG_TOKENS = frozenset({"YES", "Y", "NO", "N"})
GENDER_LETTERS = frozenset({"M", "W", "K"})
# Tokens that are noise for common-code fallback
NOISE_TOKENS = frozenset(
    {
        "YES",
        "Y",
        "NO",
        "N",
        "BLK",
        "WHI",
        "WHE",
        "NAV",
        "NVY",
        "RED",
        "PNK",
        "LPNK",
        "HPNK",
        "GRN",
        "BLU",
        "LBL",
        "LBLU",
        "ORG",
        "ORN",
        "YEL",
        "PRP",
        "GRY",
        "GRY",
        "BGE",
        "CRM",
        "NTRL",
        "MULTI",
        "PACK",
        "PAK",
        "PER",
        "F",
        "B",
        "P",
        "S",
        "M",
        "L",
        "XL",
        "XS",
        "2XL",
        "3XL",
        "4XL",
        "5XL",
        "XXL",
        "YS",
        "YXS",
        "YM",
        "YL",
        "YXL",
        "Y2XL",
        "LG",
        "ALG",
    }
)
COMMON_ALLOW = frozenset({"A3", "A4", "A5", "A6", "BS", "BG", "QD", "SH", "W", "C"})
COMMON_PREFIXES = ("BG", "QD", "SH", "TPC", "BZ", "C8", "W1", "SF")

POCKET_ADULT = (80, 100)
POCKET_KIDS = (65, 80)

RE_PAREN = re.compile(r"\(([^)]*)\)")
RE_CRLF = re.compile(r"[\r\n]+")


def clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() in ("nan", "none"):
        return ""
    return RE_CRLF.sub(" ", s).strip()


def to_num(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def normalize_sku(sku: str) -> tuple[str, list[str]]:
    """Uppercase SKU; split on '-'; drop empties; strip trailing '.' on tokens."""
    s = clean(sku).upper()
    tokens = [t.rstrip(".") for t in s.split("-") if t and t.rstrip(".")]
    return s, tokens


def strip_trailing_flags(tokens: list[str]) -> list[str]:
    out = list(tokens)
    while out and out[-1] in FLAG_TOKENS:
        out.pop()
    return out


def parse_sku_value(sku_val: str) -> tuple[str, list[str]]:
    """'K-SS (YXS)' / 'M-T (-L)' / 'K-SS (YS) (YXS)' → (base, brackets)."""
    raw = clean(sku_val).upper()
    if not raw:
        return "", []
    brackets = [b.strip().upper() for b in RE_PAREN.findall(raw) if b.strip()]
    base = RE_PAREN.sub("", raw)
    base = re.sub(r"\s+", " ", base).strip()
    base = re.sub(r"\s*-\s*", "-", base)
    return base, brackets


def is_leading_dash_bracket(bracket: str) -> bool:
    return bracket.startswith("-")
