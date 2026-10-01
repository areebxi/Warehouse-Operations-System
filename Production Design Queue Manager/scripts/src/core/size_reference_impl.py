from __future__ import annotations
import pandas as pd
from src.core.size_lookup_index import get_indexed_row, get_size_reference_index
from typing import Any, Optional, Dict, List, Tuple, Union

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
