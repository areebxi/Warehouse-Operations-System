"""Assign base / base-1 / base-2 Order Number suffixes for merge (duplicate) orders.

Used by Step 6 grouping and by Preflight so custom Logo/Design Image lookups
match the same stems as packing PDF generation.
"""

from __future__ import annotations

import pandas as pd

from scripts.pipeline_runtime.order_number_csv import coerce_order_number_columns

from .common import _customise_is_yes, _normalize, _order_number_column
from .grouping_quantity import _get_qty


def assign_order_number_suffixes_for_customise(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rewrite Order Number to base / base-1 / … in current row order.

    Requires ``Order Number (Base)``. For Customise=Yes rows, also sets
    ``Logo/Design Image`` to the rewritten order number. Position resets when
    ``Order Number (Base)`` changes.
    """
    if df.empty:
        return df

    out = df.copy()
    on_col = _order_number_column(out)
    if (
        on_col is None
        or "Order Number (Base)" not in out.columns
        or "Customise" not in out.columns
    ):
        return out

    current_base: str | None = None
    position = 0
    for row_idx in out.index:
        base_val = _normalize(out.at[row_idx, "Order Number (Base)"])
        if base_val != current_base:
            current_base = base_val
            position = 0
        new_order = current_base if position == 0 else f"{current_base}-{position}"
        out.at[row_idx, on_col] = new_order
        if (
            _customise_is_yes(out.at[row_idx, "Customise"])
            and "Logo/Design Image" in out.columns
        ):
            out.at[row_idx, "Logo/Design Image"] = new_order
        position += 1
    return out


def assign_merge_order_number_suffixes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Step-6 merge duplicate-order suffixes for custom logo lookup.

    Merge rows (Order Number appears 2+ times in ``df``, or Item Quantity > 1)
    are sorted by Recipient Name, Order Number, then original order; then
    assigned ``base``, ``base-1``, ``base-2``, …. Customise=Yes rows get
    ``Logo/Design Image`` updated to match. Non-merge rows keep their Order
    Number but receive ``Order Number (Base)``.
    """
    if df.empty:
        return df

    out = coerce_order_number_columns(df.copy())
    on_col = _order_number_column(out)
    if on_col is None:
        return out

    out["Order Number (Base)"] = out[on_col].map(_normalize)

    if "Customise" not in out.columns:
        return out

    order_counts = out[on_col].value_counts(dropna=False)
    is_merge = []
    for _, row in out.iterrows():
        on = row.get(on_col)
        qty = _get_qty(row, out)
        is_merge.append(bool(order_counts.get(on, 0) >= 2 or qty > 1))

    merge_mask = pd.Series(is_merge, index=out.index)
    if not merge_mask.any():
        return out

    merge_df = out.loc[merge_mask].copy()
    merge_df["_suffix_orig_idx"] = range(len(merge_df))

    if "Recipient Name" in merge_df.columns:
        merge_df["_recipient_sort"] = (
            merge_df["Recipient Name"].fillna("").astype(str).str.strip().str.lower()
        )
    else:
        merge_df["_recipient_sort"] = ""

    sort_cols = ["_recipient_sort", on_col, "_suffix_orig_idx"]
    merge_df = merge_df.sort_values(sort_cols)
    merge_df = assign_order_number_suffixes_for_customise(merge_df)

    for idx in merge_df.index:
        out.at[idx, on_col] = merge_df.at[idx, on_col]
        if "Logo/Design Image" in out.columns:
            out.at[idx, "Logo/Design Image"] = merge_df.at[idx, "Logo/Design Image"]

    return out
