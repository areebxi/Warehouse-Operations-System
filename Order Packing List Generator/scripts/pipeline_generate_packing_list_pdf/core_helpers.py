from __future__ import annotations

import re
from typing import Callable, Optional, Tuple

import pandas as pd


def _strip_integer_float_text(text: str) -> str:
    """4055007854.0 -> 4055007854 when the value is a whole-number float string."""
    if text.endswith(".0"):
        whole, dot, frac = text.partition(".")
        if dot and frac == "0" and whole.lstrip("-").isdigit():
            return whole
    return text


def safe_str_impl(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    s = str(val).strip()
    return _strip_integer_float_text(s)


def normalize_label_impl(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


def normalize_lower_impl(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip().lower()


def parse_process_and_item_impl(
    val,
    *,
    safe_str: Callable[[object], str],
    process_item_re: re.Pattern[str],
) -> Tuple[Optional[str], Optional[str]]:
    s = safe_str(val)
    if not s:
        return None, None
    m = process_item_re.match(s)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def is_plain_order_sku_impl(item_sku: str) -> bool:
    """True when Item SKU marks a plain order (PDF skips logo image lookup/draw)."""
    s = (item_sku or "").lower()
    return "plainlg" in s or "plain" in s


def logo_design_tokens_impl(
    logo_design_val,
    *,
    safe_str: Callable[[object], str],
) -> list[str]:
    s = safe_str(logo_design_val)
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip()][:5]


def position_tokens_impl(
    position_val,
    *,
    safe_str: Callable[[object], str],
) -> list[str]:
    s = safe_str(position_val)
    if not s:
        return []
    return [t.strip() for t in s.split(",") if t.strip()][:5]


def classify_position_token_impl(
    position_token: str,
    *,
    safe_str: Callable[[object], str],
) -> Tuple[bool, bool, bool]:
    s = safe_str(position_token).lower()
    if not s:
        return False, False, False
    has_front = "front" in s
    has_pocket = "pocket" in s
    has_back = "back" in s
    return has_front, has_pocket, has_back


def get_field_value_impl(
    row_series,
    field_key: str,
    order_number_counts: dict,
    *,
    safe_str: Callable[[object], str],
    logo_design_tokens: Callable[[object], list[str]],
) -> str:
    if field_key == "Items":
        base_order = safe_str(
            row_series.get("Order Number (Base)") or row_series.get("Order Number")
        )
        count = order_number_counts.get(base_order, 1)
        return f"Items = {count}" if count > 1 else ""
    if field_key == "Order Number":
        return safe_str(row_series.get("Order Number"))
    if field_key == "Item Quantity":
        raw_val = row_series.get("Item Quantity", "")
        try:
            num = float(raw_val)
        except (TypeError, ValueError):
            return safe_str(raw_val)
        if pd.isna(num):
            return ""
        if num.is_integer():
            return str(int(num))
        return safe_str(raw_val)
    if field_key in (
        "Logo/Design Image (1st)",
        "Logo/Design Image (2nd)",
        "Logo/Design Image (3rd)",
        "Logo/Design Image (4th)",
        "Logo/Design Image (5th)",
    ):
        tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
        if field_key == "Logo/Design Image (1st)":
            return tokens[0] if len(tokens) > 0 else ""
        if field_key == "Logo/Design Image (2nd)":
            return tokens[1] if len(tokens) > 1 else ""
        if field_key == "Logo/Design Image (3rd)":
            return tokens[2] if len(tokens) > 2 else ""
        if field_key == "Logo/Design Image (4th)":
            return tokens[3] if len(tokens) > 3 else ""
        if field_key == "Logo/Design Image (5th)":
            return tokens[4] if len(tokens) > 4 else ""
    return safe_str(row_series.get(field_key, ""))


def truncate_impl(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1] + "\u2026"

