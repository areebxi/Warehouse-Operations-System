"""
GUI size reference helper functions.
"""

import pandas as pd

from src.core.design_processor import extract_size_code as extract_size_code_func, save_missing_size_reference_rows
from src.core.image_utils import get_size_from_reference as get_size_from_reference_func


def extract_size_code(gui, sku):
    """Extract size code from SKU by searching for size codes from the reference file"""
    overrides = getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set
    return extract_size_code_func(sku, gui.size_reference_df, overrides)


def get_size_from_reference(gui, size_code):
    """Get size dimensions from Size Reference file
    Returns Critical Width (column J) and Critical Height (column K) for logo scaling
    """
    base_code = None
    lookup_size_code = size_code

    # If size_code is a composite "BASE|BRACKET", split before lookup
    if isinstance(size_code, str) and "|" in size_code:
        parts = size_code.split("|", 1)
        if len(parts) == 2:
            base_code, lookup_size_code = parts[0], parts[1]

    return get_size_from_reference_func(
        gui.size_reference_df,
        lookup_size_code,
        gui.mm_to_pixel,
        base_code=base_code,
    )


def get_merged_text_from_reference(gui, size_code):
    """Get Merged column text from Size Reference file (column I)"""
    if gui.size_reference_df is None or size_code is None:
        return None

    if "Merge_clean" not in gui.size_reference_df.columns:
        return None

    # If size_code is composite "BASE|BRACKET", use base part for Merge lookup
    lookup_size_code = size_code
    if isinstance(size_code, str) and "|" in size_code:
        parts = size_code.split("|", 1)
        if len(parts) == 2:
            lookup_size_code = parts[0]

    from src.core.size_reference import _find_matching_row

    row, _match_type = _find_matching_row(gui.size_reference_df, lookup_size_code)
    if row is None:
        return None

    # Get Merged column (column I)
    merged_text = row.get("Merge", None)
    if pd.notna(merged_text):
        return str(merged_text).strip()

    return None


def save_missing_size_reference_rows_func(gui, df, missing_row_indices, source_file_path=None):
    """Save rows with missing size references to a new DTF Des file"""
    import os
    import queue_app

    app_dir = os.path.dirname(os.path.abspath(queue_app.__file__))
    return save_missing_size_reference_rows(df, missing_row_indices, source_file_path, app_dir)

