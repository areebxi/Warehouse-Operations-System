"""
File handling utilities for finding, loading, and managing design files.

This module re-exports utilities from:
- `src/io/file_utilities.py`
- `src/io/file_search.py`
- `src/io/file_loaders.py`

Keeping these re-exports inside `src/io/` lets us delete the messy
top-level `src/file_handlers.py` wrapper later without breaking imports.
"""

# Re-export from file_utilities
from src.io.file_utilities import (
    IMAGE_EXTENSIONS,
    extract_design_code,
    remove_apparel_size_prefix,
    extract_text_after_des,
)

# Re-export from file_search
from src.io.file_search import (
    find_design_file_by_code,
    find_design_file_by_sku,
    find_design_file,
    find_design_file_vba_logic,
)

# Re-export from file_loaders
from src.io.file_loaders import (
    load_color_bar_from_app_dir,
    load_configuration_workbook,
    load_pocket_design_ids_database,
    load_print_size_overrides,
    load_size_reference_from_app_dir,
)

__all__ = [
    # Constants
    "IMAGE_EXTENSIONS",
    # Utility functions
    "extract_design_code",
    "remove_apparel_size_prefix",
    "extract_text_after_des",
    # File search functions
    "find_design_file_by_code",
    "find_design_file_by_sku",
    "find_design_file",
    "find_design_file_vba_logic",
    # File loader functions
    "load_color_bar_from_app_dir",
    "load_configuration_workbook",
    "load_pocket_design_ids_database",
    "load_print_size_overrides",
    "load_size_reference_from_app_dir",
]

