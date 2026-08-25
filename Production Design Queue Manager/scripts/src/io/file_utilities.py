"""
File utility functions for extracting and processing design codes and filenames.

This module provides utility functions for:
    - Extracting design codes from SKUs
    - Removing apparel size prefixes
    - Extracting text from filenames
    - Common image extensions constant
"""

import os
import pandas as pd
from typing import Optional, List, Union


# Common image extensions - centralized to avoid duplication
# The app should always match PNG files, so we restrict
# all image searches to `.png` going forward.
IMAGE_EXTENSIONS: List[str] = ['.png']


def extract_design_code(sku: Union[str, pd.Series, None]) -> Optional[str]:
    """Extract design code from SKU.

    The design code is typically the first part before the first dash.
    If no dash is found, returns the entire SKU string.
    """
    if not sku or pd.isna(sku):
        return None

    sku_str = str(sku)
    if '-' in sku_str:
        return sku_str.split('-')[0].strip()
    return sku_str.strip()


def remove_apparel_size_prefix(design_code: Union[str, None]) -> str:
    """Remove common apparel size prefixes from the beginning of design code."""
    if not design_code:
        return ""

    design_code_str = str(design_code).strip()
    design_code_upper = design_code_str.upper()

    # Common apparel size prefixes (ordered from longest to shortest)
    size_prefixes = ['XXXXL', 'XXXL', 'XXL', '3XL', '4XL', '2XL', 'XL', 'XS', 'YS', 'YM', 'YL', 'S', 'M', 'L']

    for prefix in size_prefixes:
        if design_code_upper.startswith(prefix):
            remaining = design_code_str[len(prefix):]
            if remaining:
                return remaining

    return design_code_str


def extract_text_after_des(filename: Optional[str]) -> Optional[str]:
    """Extract process number after 'Des-' from filename (DTF Des files)."""
    if not filename:
        return None

    if 'Des-' in filename:
        idx = filename.find('Des-')
        if idx != -1:
            # 4 is length of 'Des-'
            text_after = filename[idx + 4:]
            # Handle case where text_after is just extension (e.g., ".xlsx")
            if text_after and text_after.startswith('.'):
                return ""

            text_after = os.path.splitext(text_after)[0].strip()
            return text_after if text_after else ""

    return None

