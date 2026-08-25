"""
Indexed lookups for Size Reference DataFrames.

Built once after loading Configuration Workbook / a manual size-reference file,
then reused for O(1)/O(unique-bases) SKU and dimension lookups instead of full
DataFrame scans (iterrows / str.contains on every row).

Rows are also cached as plain dicts because ``DataFrame.iloc`` is extremely slow
on this workbook (object columns with list values in Merge_brackets).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd


@dataclass
class SizeReferenceIndex:
    """Precomputed indexes over a size-reference DataFrame."""

    # Row payloads as plain dicts (fast alternative to DataFrame.iloc)
    records: List[Dict[str, Any]] = field(default_factory=list)
    # (BASE, BRACKET) -> first row index
    by_base_bracket: Dict[Tuple[str, str], int] = field(default_factory=dict)
    # BRACKET -> first row index (bracket-only fallback)
    by_bracket: Dict[str, int] = field(default_factory=dict)
    # BASE (Merge_clean upper) -> first row index
    by_base: Dict[str, int] = field(default_factory=dict)
    # Exact Merge cell text (stripped) -> list of row indices (multi-position groups)
    by_merge_text: Dict[str, List[int]] = field(default_factory=dict)
    # Unique bases in first-appearance order
    bases_first_order: List[str] = field(default_factory=list)
    # Unique bases sorted longest-first (substring matching in SKUs)
    bases_longest_first: List[str] = field(default_factory=list)
    # BASE -> bracket codes in first-seen order
    brackets_by_base: Dict[str, List[str]] = field(default_factory=dict)


_INDEX_ATTR = "size_lookup_index"


def _norm(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip().upper()
    if not text or text in ("NAN", "NONE"):
        return ""
    return text


def build_size_reference_index(df: Optional[pd.DataFrame]) -> Optional[SizeReferenceIndex]:
    """Build lookup indexes from a prepared size-reference DataFrame."""
    if df is None or "Merge_clean" not in df.columns:
        return None

    index = SizeReferenceIndex(records=df.to_dict("records"))
    seen_bases: Set[str] = set()
    bracket_sets: Dict[str, Set[str]] = {}

    has_brackets_col = "Merge_brackets" in df.columns
    has_merge_col = "Merge" in df.columns

    merge_clean_values = df["Merge_clean"].tolist()
    merge_brackets_values = (
        df["Merge_brackets"].tolist() if has_brackets_col else [None] * len(df)
    )
    merge_values = df["Merge"].tolist() if has_merge_col else [None] * len(df)

    for i in range(len(df)):
        base = _norm(merge_clean_values[i])
        brackets = merge_brackets_values[i] if has_brackets_col else None
        has_any_bracket = isinstance(brackets, list) and any(
            _norm(b) for b in brackets
        )

        if base:
            if base not in seen_bases:
                seen_bases.add(base)
                index.bases_first_order.append(base)
                index.brackets_by_base[base] = []
                bracket_sets[base] = set()
            # Bare-base lookup only for rows with no brackets, so M-T (B4A)
            # cannot win an exact match for a plain M-T size code.
            if base not in index.by_base and not has_any_bracket:
                index.by_base[base] = i

        if has_merge_col:
            merge_text = str(merge_values[i]).strip() if pd.notna(merge_values[i]) else ""
            if merge_text and merge_text.lower() != "nan":
                index.by_merge_text.setdefault(merge_text, []).append(i)

        if not has_brackets_col or not base or not isinstance(brackets, list):
            continue

        for bracket in brackets:
            bracket_norm = _norm(bracket)
            if not bracket_norm:
                continue
            key = (base, bracket_norm)
            if key not in index.by_base_bracket:
                index.by_base_bracket[key] = i
            if bracket_norm not in index.by_bracket:
                index.by_bracket[bracket_norm] = i
            if bracket_norm not in bracket_sets[base]:
                bracket_sets[base].add(bracket_norm)
                index.brackets_by_base[base].append(bracket_norm)

    index.bases_longest_first = sorted(index.bases_first_order, key=len, reverse=True)
    return index


def attach_size_reference_index(df: Optional[pd.DataFrame]) -> Optional[pd.DataFrame]:
    """Attach a SizeReferenceIndex onto ``df.attrs`` and return ``df``."""
    if df is None:
        return None
    index = build_size_reference_index(df)
    if index is not None:
        df.attrs[_INDEX_ATTR] = index
    return df


def get_size_reference_index(df: Optional[pd.DataFrame]) -> Optional[SizeReferenceIndex]:
    """Return an attached index, building one lazily if missing."""
    if df is None:
        return None
    index = df.attrs.get(_INDEX_ATTR)
    if isinstance(index, SizeReferenceIndex):
        return index
    index = build_size_reference_index(df)
    if index is not None:
        df.attrs[_INDEX_ATTR] = index
    return index


def get_indexed_row(
    size_reference_df: pd.DataFrame,
    row_idx: int,
) -> Dict[str, Any]:
    """Return a row payload without using DataFrame.iloc."""
    index = get_size_reference_index(size_reference_df)
    if index is not None and 0 <= row_idx < len(index.records):
        return index.records[row_idx]
    return size_reference_df.iloc[row_idx].to_dict()
