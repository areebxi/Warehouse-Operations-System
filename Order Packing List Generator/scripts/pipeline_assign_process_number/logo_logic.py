from pathlib import Path

import pandas as pd

from .normalize import _normalize, _normalize_key


def _item_quantity_for_row(row: pd.Series, df: pd.DataFrame) -> int:
    """Item Quantity for row; default 1 if missing or invalid."""
    if "Item Quantity" not in df.columns:
        return 1
    try:
        raw = row.get("Item Quantity", 1)
        if pd.isna(raw):
            return 1
        q = int(raw)
        return max(1, q)
    except (TypeError, ValueError):
        return 1


def compute_logo_id_unit_counts(
    df: pd.DataFrame,
) -> tuple[dict[str, int], set[tuple[str, str]]]:
    """
    Compute per-Logo ID unit counts for threshold and the set of (order, logo_id) pairs
    that are in full-logo orders. Only orders where all non-blank Logo IDs are the same
    (full-logo order) contribute; each such order adds sum(Item Quantity) for rows with
    that Logo ID. Multi-quantity rows count quantity times.
    Returns (unit_counts, full_logo_pairs) where unit_counts is normalized Logo ID -> total
    units and full_logo_pairs is set of (normalized Order Number, normalized Logo ID).
    """
    empty: set[tuple[str, str]] = set()
    if "Logo ID" not in df.columns or "Order Number" not in df.columns:
        return {}, empty
    unit_counts: dict[str, int] = {}
    full_logo_pairs: set[tuple[str, str]] = set()
    for _order_number, group in df.groupby("Order Number", sort=False):
        order_key = _normalize_key(str(_order_number))
        # All non-blank Logo IDs in this order (normalized keys)
        non_blank_keys = set()
        for _, row in group.iterrows():
            logo_val = _normalize(row.get("Logo ID", ""))
            if logo_val:
                non_blank_keys.add(_normalize_key(logo_val))
        if len(non_blank_keys) == 0:
            continue
        if len(non_blank_keys) > 1:
            # Mixed logos in this order: do not count for any Logo ID
            continue
        L = next(iter(non_blank_keys))
        # This order is full-logo for L; add Item Quantity and record (order, L)
        full_logo_pairs.add((order_key, L))
        for _, row in group.iterrows():
            if _normalize_key(row.get("Logo ID", "")) != L:
                continue
            q = _item_quantity_for_row(row, df)
            unit_counts[L] = unit_counts.get(L, 0) + q
    return unit_counts, full_logo_pairs

