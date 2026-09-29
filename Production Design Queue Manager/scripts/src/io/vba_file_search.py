"""Backward-compatible public wrapper for VBA search logic."""

from src.io.vba_file_search_core import (
    find_design_file_vba_logic,
    find_sku_position_variant_files,
    resolve_sku_position_hint,
)

__all__ = [
    "find_design_file_vba_logic",
    "find_sku_position_variant_files",
    "resolve_sku_position_hint",
]

