"""
Helpers for position-based multi design resolution across modes.
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from src.core.size_reference import (
    _find_matching_row,
    _find_dimension_value,
    _build_size_result,
)
from src.core.size_lookup_index import get_size_reference_index


def _to_int(value: Any) -> Optional[int]:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        parsed = int(float(str(value).strip()))
        return parsed if parsed > 0 else None
    except (TypeError, ValueError):
        return None


def _clean_str(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text if text else None


def _extract_size_info(
    row: Any,
    size_reference_df: pd.DataFrame,
    lookup_size_code: str,
    mm_to_pixel_factor: float,
    match_type: str,
) -> Optional[Dict[str, float]]:
    width_cols = [
        "Target width used for logo scaling",
        "Target width",
        "Logo Width",
        "CritWidth",
        "Size Width",
    ]
    height_cols = [
        "Target height used for logo scaling",
        "Target height",
        "Logo Height",
        "CritHeight",
        "Size Height",
    ]
    width_mm, width_col_name = _find_dimension_value(row, size_reference_df, width_cols)
    height_mm, height_col_name = _find_dimension_value(row, size_reference_df, height_cols)

    if width_mm is None or height_mm is None or pd.isna(width_mm) or pd.isna(height_mm):
        return None

    merge_entry = _clean_str(row.get("Merge")) or _clean_str(row.get("Merge_clean")) or lookup_size_code
    return _build_size_result(
        float(width_mm),
        float(height_mm),
        mm_to_pixel_factor,
        lookup_size_code,
        merge_entry,
        match_type,
        width_col_name,
        height_col_name,
    )


def _row_design_count(row: Any) -> Optional[int]:
    """Read Number of Designs / Number of Positions from a size-reference row."""
    count = _to_int(row.get("Number of Positions"))
    if count is None:
        count = _to_int(row.get("Number of Designs"))
    return count


def _row_suffix(row: Any) -> Optional[str]:
    """Read Suffix / Position from a size-reference row."""
    return _clean_str(row.get("Position")) or _clean_str(row.get("Suffix"))


def get_position_size_entries(
    size_reference_df: Optional[pd.DataFrame],
    lookup_size_code: Optional[str],
    mm_to_pixel_factor: float,
    base_code: Optional[str] = None,
    force_single: bool = False,
) -> List[Dict[str, Any]]:
    """Resolve one or many size entries based on Number of Designs / Suffix."""
    if (
        size_reference_df is None
        or not lookup_size_code
        or "Merge_clean" not in size_reference_df.columns
    ):
        return [{"position": None, "size_info": None}]

    match_row, match_type = _find_matching_row(
        size_reference_df, lookup_size_code, base_code=base_code
    )
    if match_row is None or not match_type:
        return [{"position": None, "size_info": None}]

    count = _row_design_count(match_row)
    merge_key = _clean_str(match_row.get("Merge_clean"))
    if force_single or count is None or count < 2 or not merge_key:
        return [
            {
                "position": None,
                "size_info": _extract_size_info(
                    match_row,
                    size_reference_df,
                    lookup_size_code,
                    mm_to_pixel_factor,
                    match_type,
                ),
            }
        ]

    # Group by the exact Merge cell (includes bracket design IDs). Grouping only
    # by Merge_clean incorrectly pulls every design that shares a base code
    # (e.g. all M118 rows) when the workbook has many product variants.
    merge_text = _clean_str(match_row.get("Merge"))
    if merge_text and "Merge" in size_reference_df.columns:
        index = get_size_reference_index(size_reference_df)
        if index is not None and merge_text in index.by_merge_text:
            group_indices = [
                i
                for i in index.by_merge_text[merge_text]
                if _row_design_count(index.records[i]) == count
            ]
            group_rows = [index.records[i] for i in group_indices]
        else:
            count_series = (
                size_reference_df["Number of Positions"].apply(_to_int)
                if "Number of Positions" in size_reference_df.columns
                else size_reference_df["Number of Designs"].apply(_to_int)
            )
            group = size_reference_df[
                (size_reference_df["Merge"].astype(str).str.strip() == merge_text)
                & (count_series == count)
            ]
            group_rows = group.to_dict("records")
    else:
        count_series = (
            size_reference_df["Number of Positions"].apply(_to_int)
            if "Number of Positions" in size_reference_df.columns
            else size_reference_df["Number of Designs"].apply(_to_int)
        )
        group = size_reference_df[
            (size_reference_df["Merge_clean"].astype(str).str.strip().str.upper() == merge_key.upper())
            & (count_series == count)
        ]
        group_rows = group.to_dict("records")

    entries: List[Dict[str, Any]] = []
    for row in group_rows:
        position = _row_suffix(row)
        if not position:
            continue
        size_info = _extract_size_info(
            row,
            size_reference_df,
            lookup_size_code,
            mm_to_pixel_factor,
            match_type,
        )
        entries.append({"position": position, "size_info": size_info})

    if not entries:
        return [
            {
                "position": None,
                "size_info": _extract_size_info(
                    match_row,
                    size_reference_df,
                    lookup_size_code,
                    mm_to_pixel_factor,
                    match_type,
                ),
            }
        ]

    return entries


def build_positioned_stems(base_stems: List[str], position: Optional[str]) -> List[str]:
    """Append the position suffix to each base stem."""
    clean = _clean_str(position)
    if not clean:
        return [stem for stem in base_stems if stem]

    stems: List[str] = []
    for stem in base_stems:
        if not stem:
            continue
        stems.append(f"{stem}-{clean}")
    return stems

