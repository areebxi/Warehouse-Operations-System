import re

import pandas as pd

from .config import FAWAD_LOGO_TOKEN_RE, NORMAL_LOGO_TOKEN_RE, PRIME_TAG_EXACT


def _order_number_as_logo_token(order_num) -> str:
    """Order number for Logo/Design Image — avoid pandas 4055007854.0 float strings."""
    if pd.isna(order_num):
        return ""
    if isinstance(order_num, float) and order_num.is_integer():
        return str(int(order_num))
    s = str(order_num).strip() if isinstance(order_num, str) else str(order_num)
    if s.endswith(".0"):
        whole, dot, frac = s.partition(".")
        if dot and frac == "0" and whole.lstrip("-").isdigit():
            return whole
    return s


def _is_prime(tags_val) -> bool:
    """True if any tag after split/strip equals 'Amazon Prime Order'."""
    if pd.isna(tags_val):
        return False
    s = str(tags_val).strip()
    if not s:
        return False
    parts = [p.strip() for p in s.split(",")]
    return PRIME_TAG_EXACT in parts


def _extract_normal_logo_tokens(item_sku) -> str:
    """Extract all LG, TSU, AV, HK, and fawad+digits tokens from Item SKU in order of appearance.
    Normalize (trim), unique, joined by ', '.
    """
    if pd.isna(item_sku) or not isinstance(item_sku, str):
        return ""
    s = str(item_sku)
    ordered = []
    for m in NORMAL_LOGO_TOKEN_RE.finditer(s):
        ordered.append((m.start(), m.group(1)))
    for m in FAWAD_LOGO_TOKEN_RE.finditer(s):
        ordered.append((m.start(), m.group(1)))
    ordered.sort(key=lambda x: x[0])
    if not ordered:
        return ""
    seen = set()
    unique = []
    for _, raw in ordered:
        t = str(raw).strip()
        if not t:
            continue
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return ", ".join(unique)


def _first_logo_id(item_sku) -> str:
    """First LG/TSU/AV/HK/fawad+digits token from Item SKU; blank if none."""
    normalized = _extract_normal_logo_tokens(item_sku)
    if not normalized:
        return ""
    return normalized.split(", ")[0]


def _first_per_token(item_sku) -> str:
    """First (prefix+\d+PER) token from Item SKU, case unchanged; blank if none."""
    tokens = re.findall(
        r"[A-Za-z0-9]*\d+PER",
        str(item_sku) if not pd.isna(item_sku) and isinstance(item_sku, str) else "",
    )
    if not tokens:
        return ""
    return tokens[0]


def _customise_is_yes(val) -> bool:
    """True if Customise is 'Yes' (case-insensitive, trimmed)."""
    if pd.isna(val):
        return False
    return str(val).strip().lower() == "yes"

