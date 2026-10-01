from __future__ import annotations

from typing import Callable, Dict

import pandas as pd


def build_order_counts_impl(
    df: pd.DataFrame,
    *,
    safe_str: Callable[[object], str],
) -> dict:
    counts: dict = {}
    first_idx: dict = {}
    base_series = df.get("Order Number (Base)")
    order_series = df.get("Order Number", pd.Series(dtype=object))
    for idx, on in order_series.items():
        base_val = ""
        if base_series is not None:
            try:
                base_val = safe_str(base_series.iloc[idx])
            except Exception:
                base_val = ""
        key = base_val or safe_str(on)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
        if key not in first_idx:
            first_idx[key] = idx
    for key, idx in first_idx.items():
        counts[("__first__", key)] = idx
    return counts

def build_process_totals_impl(
    df: pd.DataFrame,
    *,
    parse_process_and_item: Callable[[object], Tuple[Optional[str], Optional[str]]],
) -> Dict[str, int]:
    totals: Dict[str, int] = {}
    col = df.get("Process and Item Number")
    if col is None:
        return totals
    for val in col:
        process_id, _item = parse_process_and_item(val)
        if not process_id:
            continue
        totals[process_id] = totals.get(process_id, 0) + 1
    return totals

