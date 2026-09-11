"""
GUI size reference helper functions.
"""

import pandas as pd

from src.core.cl_print_sizes import cl_sku_has_print_size
from src.core.design_processor import extract_size_code as extract_size_code_func, save_missing_size_reference_rows


def extract_size_code(gui, sku):
    """Label-only size code hint (CL CSV owns live print dimensions)."""
    overrides = getattr(gui, "print_size_overrides", None) or gui.pocket_design_ids_set
    return extract_size_code_func(sku, None, overrides)


def sku_missing_cl_print_size(gui, sku) -> bool:
    """True when Item SKU has no CL print-size row."""
    return not cl_sku_has_print_size(sku, getattr(gui, "cl_csv_path", None))


def get_size_from_reference(gui, size_code):
    """Deprecated: live sizes come from CL CSV, not workbook Size References."""
    return None


def get_merged_text_from_reference(gui, size_code):
    """Deprecated: workbook Merge column is archive-only."""
    return None


def save_missing_size_reference_rows_func(gui, df, missing_row_indices, source_file_path=None):
    """Save rows with missing size references to a new DTF Des file"""
    import os
    import queue_app

    app_dir = os.path.dirname(os.path.abspath(queue_app.__file__))
    return save_missing_size_reference_rows(df, missing_row_indices, source_file_path, app_dir)
