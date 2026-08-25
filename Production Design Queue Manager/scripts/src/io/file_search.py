"""
File search utilities for finding design files in folders.

This module provides functions for:
    - Finding design files by code, SKU, or order number
    - Basic search strategies (exact, case-insensitive, etc.)

It also logs which search strategy successfully located a design (or if no
file was found) via the shared run logger, so the console log shows how
each image file was chosen during a run.
"""
import os
import pandas as pd
from typing import Optional, List, Union
from src.io.file_utilities import IMAGE_EXTENSIONS, extract_design_code, remove_apparel_size_prefix
from src.system.logging.utils import get_run_logger

# Re-export from vba_file_search for backwards compatibility
from src.io.vba_file_search import find_design_file_vba_logic

__all__ = [
    'find_design_file_by_code',
    'find_design_file_by_sku',
    'find_design_file',
    'find_design_file_vba_logic',
]


def find_design_file_by_code(
    design_code: Optional[str],
    folder: Optional[str],
    extensions: Optional[List[str]] = None
) -> Optional[str]:
    """Find design file by design code in a folder."""
    if not folder or not design_code:
        return None

    if extensions is None:
        extensions = IMAGE_EXTENSIONS

    # Try exact match with design code first
    for ext in extensions:
        file_path = os.path.join(folder, f"{design_code}{ext}")
        if os.path.exists(file_path):
            return file_path

    # Try case-insensitive match with design code
    try:
        design_code_lower = design_code.lower()
        for file in os.listdir(folder):
            file_lower = file.lower()
            file_name_without_ext = os.path.splitext(file_lower)[0]

            # Check if file starts with design code
            if file_name_without_ext.startswith(design_code_lower):
                if any(file_lower.endswith(ext) for ext in extensions):
                    return os.path.join(folder, file)
    except (FileNotFoundError, PermissionError, OSError):
        return None

    return None


def find_design_file_by_sku(
    sku: Optional[str],
    folder: Optional[str],
    extensions: Optional[List[str]] = None
) -> Optional[str]:
    """Find design file by full SKU in a folder."""
    if not folder or not sku:
        return None

    if extensions is None:
        extensions = IMAGE_EXTENSIONS

    try:
        sku_str = str(sku).lower()
        for file in os.listdir(folder):
            file_lower = file.lower()
            file_name_without_ext = os.path.splitext(file_lower)[0]
            if file_name_without_ext == sku_str or file_name_without_ext.startswith(sku_str):
                if any(file_lower.endswith(ext) for ext in extensions):
                    return os.path.join(folder, file)
    except (FileNotFoundError, PermissionError, OSError):
        return None

    return None


def find_design_file(sku: Union[str, pd.Series, None], designs_folder: Optional[str]) -> Optional[str]:
    """Find design file for a given SKU using multiple strategies."""
    logger = get_run_logger()

    if not designs_folder or not sku:
        logger.debug(
            "find_design_file: missing designs_folder or sku "
            "(designs_folder=%s, sku=%s)",
            designs_folder,
            sku,
        )
        return None

    sku_str = str(sku).strip()
    logger.debug(
        "find_design_file: starting search for sku=%s in designs_folder=%s",
        sku_str,
        designs_folder,
    )

    # Strategy 1: Extract design code and search by code
    design_code = extract_design_code(sku)
    if design_code:
        logger.debug(
            "find_design_file: trying design_code strategy with design_code=%s",
            design_code,
        )
        file_path = find_design_file_by_code(design_code, designs_folder)
        if file_path:
            logger.debug(
                "find_design_file: found file via design_code strategy -> %s",
                file_path,
            )
            return file_path

    # Strategy 2: Search by full SKU
    logger.debug("find_design_file: trying full SKU strategy for sku=%s", sku_str)
    file_path = find_design_file_by_sku(sku_str, designs_folder)
    if file_path:
        logger.debug(
            "find_design_file: found file via full SKU strategy -> %s",
            file_path,
        )
        return file_path

    # Strategy 3: Extract design code without size prefix and search
    if design_code:
        design_code_without_size = remove_apparel_size_prefix(design_code)
        if design_code_without_size and design_code_without_size != design_code:
            logger.debug(
                "find_design_file: trying design_code_without_size strategy "
                "with design_code_without_size=%s",
                design_code_without_size,
            )
            file_path = find_design_file_by_code(design_code_without_size, designs_folder)
            if file_path:
                logger.debug(
                    "find_design_file: found file via design_code_without_size strategy -> %s",
                    file_path,
                )
                return file_path

    logger.warning(
        "find_design_file: no design file found for sku=%s in designs_folder=%s "
        "(tried code, SKU, and code-without-size strategies)",
        sku_str,
        designs_folder,
    )
    return None

