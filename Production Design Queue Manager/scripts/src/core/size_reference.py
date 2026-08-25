"""
Size reference utilities for looking up dimensions from reference DataFrames.
"""
import pandas as pd
from src.core.size_lookup_index import get_indexed_row, get_size_reference_index
from typing import Any, Optional, Dict, List, Tuple, Union


# Constants (pixel values at 300 DPI: px = mm * 300 / 25.4)
DEFAULT_DESIGN_PADDING: int = 94  # Horizontal padding between designs (~8 mm)
DEFAULT_VERTICAL_PADDING: int = 177  # Vertical padding between rows / from top & bottom (~15 mm)
COLOR_BAR_WIDTH: int = 59  # Width of color bar reservation in pixels
COLOR_BAR_SPACING: int = 142  # Spacing for color bar (~12 mm)
NON_BAR_MARGIN: int = 24  # Margin on the side opposite the color bar (~2 mm)

RowLike = Union[pd.Series, Dict[str, Any]]


def _row_get(row: RowLike, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return row.get(key, default)


def _row_has_brackets(row: RowLike) -> bool:
    brackets = _row_get(row, "Merge_brackets", [])
    if not isinstance(brackets, list):
        return False
    return any(str(b).strip() for b in brackets if b is not None and str(b).strip().lower() not in ("nan", "none"))


def _find_contains_base_row(
    size_reference_df: pd.DataFrame,
    needle: str,
) -> Optional[RowLike]:
    """Find first bracket-free Merge_clean that contains needle (case-insensitive)."""
    index = get_size_reference_index(size_reference_df)
    needle_upper = needle.upper()
    if index is not None:
        for base in index.bases_first_order:
            if needle_upper not in base:
                continue
            # Prefer bare-base rows; skip bases that only exist as bracketed variants
            row_idx = index.by_base.get(base)
            if row_idx is None:
                continue
            return get_indexed_row(size_reference_df, row_idx)
        return None

    contains = size_reference_df[
        size_reference_df['Merge_clean'].str.contains(needle, case=False, na=False, regex=False)
    ]
    for _, row in contains.iterrows():
        if not _row_has_brackets(row):
            return row
    return None


def _find_matching_row(
    size_reference_df: pd.DataFrame,
    size_code: str,
    base_code: Optional[str] = None
) -> Tuple[Optional[RowLike], Optional[str]]:
    """Find matching row in size reference DataFrame."""
    size_code_upper = size_code.upper()
    base_code_upper = base_code.upper() if base_code else None
    index = get_size_reference_index(size_reference_df)

    # Prefer base+bracket scoped lookup when possible
    if base_code_upper and 'Merge_brackets' in size_reference_df.columns and 'Merge_clean' in size_reference_df.columns:
        if index is not None:
            row_idx = index.by_base_bracket.get((base_code_upper, size_code_upper))
            if row_idx is not None:
                return get_indexed_row(size_reference_df, row_idx), "bracket"

            row_idx = index.by_base.get(base_code_upper)
            if row_idx is not None:
                return get_indexed_row(size_reference_df, row_idx), "exact"
        else:
            for _, row in size_reference_df.iterrows():
                row_base = str(row.get('Merge_clean', '')).strip().upper()
                if not row_base or row_base in ('NAN', 'NONE'):
                    continue
                if row_base != base_code_upper:
                    continue

                bracket_codes = row.get('Merge_brackets', [])
                if isinstance(bracket_codes, list):
                    for bracket_code in bracket_codes:
                        bracket_code_str = str(bracket_code).strip().upper()
                        if bracket_code_str == size_code_upper:
                            return row, "bracket"

            for _, row in size_reference_df.iterrows():
                row_base = str(row.get('Merge_clean', '')).strip().upper()
                if row_base == base_code_upper and not _row_has_brackets(row):
                    return row, "exact"

        contains_row = _find_contains_base_row(size_reference_df, base_code)
        if contains_row is not None:
            return contains_row, "contains"

    # Generic bracket-only match
    if 'Merge_brackets' in size_reference_df.columns:
        if index is not None:
            row_idx = index.by_bracket.get(size_code_upper)
            if row_idx is not None:
                return get_indexed_row(size_reference_df, row_idx), "bracket"
        else:
            for _, row in size_reference_df.iterrows():
                bracket_codes = row.get('Merge_brackets', [])
                if isinstance(bracket_codes, list):
                    for bracket_code in bracket_codes:
                        bracket_code_str = str(bracket_code).strip().upper()
                        if bracket_code_str == size_code_upper:
                            return row, "bracket"

    # Base codes exact match on Merge_clean (bracket-free rows only)
    if index is not None:
        row_idx = index.by_base.get(size_code_upper)
        if row_idx is not None:
            return get_indexed_row(size_reference_df, row_idx), "exact"
    else:
        exact_match = size_reference_df[
            size_reference_df['Merge_clean'].str.upper() == size_code_upper
        ]
        for _, row in exact_match.iterrows():
            if not _row_has_brackets(row):
                return row, "exact"

    contains_row = _find_contains_base_row(size_reference_df, size_code)
    if contains_row is not None:
        return contains_row, "contains"

    return None, None


def _find_dimension_value(
    row: RowLike,
    size_reference_df: pd.DataFrame,
    column_names: List[str]
) -> Tuple[Optional[float], Optional[str]]:
    """Find dimension value from row using named columns only."""
    for col in column_names:
        if col in size_reference_df.columns:
            value = _row_get(row, col, None)
            if pd.notna(value):
                try:
                    return float(value), col
                except (ValueError, TypeError):
                    continue
    return None, None


def _build_size_result(
    width_mm: float,
    height_mm: float,
    mm_to_pixel_factor: float,
    size_code: str,
    merge_entry: Optional[str],
    match_type: str,
    width_col_name: Optional[str],
    height_col_name: Optional[str]
) -> Dict[str, float]:
    """Build result dictionary for size lookup."""
    return {
        'width_mm': width_mm,
        'height_mm': height_mm,
        'width_px': int(width_mm * mm_to_pixel_factor),
        'height_px': int(height_mm * mm_to_pixel_factor),
        'match_type': match_type,
        'width_col_name': width_col_name,
        'height_col_name': height_col_name,
        'size_code': size_code,
        'merge_entry': merge_entry or size_code,
    }


def get_size_from_reference(
    size_reference_df: Optional[pd.DataFrame],
    size_code: Optional[str],
    mm_to_pixel_factor: float,
    base_code: Optional[str] = None
) -> Optional[Dict[str, float]]:
    """Get size dimensions from the size reference DataFrame."""
    if size_reference_df is None or size_code is None:
        return None

    if 'Merge_clean' not in size_reference_df.columns:
        return None

    row, match_type = _find_matching_row(size_reference_df, size_code, base_code=base_code)
    if row is None:
        return None

    # Best-effort full Merge cell text for logging
    merge_entry = None
    try:
        if 'Merge' in size_reference_df.columns:
            merge_entry_val = _row_get(row, 'Merge', None)
            if pd.notna(merge_entry_val):
                merge_entry = str(merge_entry_val)
        if not merge_entry:
            merge_entry_val = _row_get(row, 'Merge_clean', None)
            if pd.notna(merge_entry_val):
                merge_entry = str(merge_entry_val)
    except Exception:
        merge_entry = None

    width_cols = ['Target width used for logo scaling', 'Target width', 'Logo Width', 'CritWidth', 'Size Width']
    height_cols = ['Target height used for logo scaling', 'Target height', 'Logo Height', 'CritHeight', 'Size Height']

    width_mm, width_col_name = _find_dimension_value(row, size_reference_df, width_cols)
    height_mm, height_col_name = _find_dimension_value(row, size_reference_df, height_cols)

    if pd.notna(width_mm) and pd.notna(height_mm):
        size_info = _build_size_result(
            width_mm,
            height_mm,
            mm_to_pixel_factor,
            size_code,
            merge_entry,
            match_type,
            width_col_name,
            height_col_name,
        )
        return size_info

    return None
