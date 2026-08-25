"""Expand per-row issue masks to whole merge groups.

Merge membership matches Step 6: Order Number appears >= 2 times in the frame,
or Item Quantity > 1.
"""

from __future__ import annotations

import pandas as pd

from .common import _normalize, _order_number_column
from .grouping_quantity import _get_qty


def expand_issue_mask_to_merge_groups(
    df: pd.DataFrame,
    issue_mask: pd.Series,
) -> pd.Series:
    """
    Return a boolean Series (aligned to ``df.index``) where any issue on a merge
    group expands to all rows of that group.

    - Prefer ``Order Number (Base)`` when present; else raw Order Number.
    - A row is merge if its order key appears >= 2 times or Item Quantity > 1.
    - Non-merge issues stay row-local.
    """
    out = pd.Series(False, index=df.index, dtype=bool)
    if df.empty:
        return out

    mask = issue_mask.reindex(df.index).fillna(False).astype(bool)
    if not mask.any():
        return out

    if "Order Number (Base)" in df.columns:
        keys = df["Order Number (Base)"].map(_normalize)
    else:
        on_col = _order_number_column(df)
        if on_col is None:
            return mask.copy()
        keys = df[on_col].map(_normalize)

    order_counts = keys.value_counts(dropna=False)

    is_merge = []
    for idx, row in df.iterrows():
        key = keys.at[idx]
        qty = _get_qty(row, df)
        is_merge.append(bool(order_counts.get(key, 0) >= 2 or qty > 1))
    is_merge_s = pd.Series(is_merge, index=df.index)

    # Row-local issues for non-merge rows.
    out = out | (mask & ~is_merge_s)

    # Expand merge groups that have any issue member.
    merge_issue_keys = set(keys.loc[mask & is_merge_s].tolist())
    merge_issue_keys.discard("")
    if merge_issue_keys:
        out = out | keys.isin(merge_issue_keys)

    return out.astype(bool)
