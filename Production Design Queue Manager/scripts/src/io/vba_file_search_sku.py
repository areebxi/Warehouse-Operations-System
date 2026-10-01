"""SKU-named PNG stems + companion JPEG position-hint search."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple, Union

from src.core.sku_position_hints import (
    POSITION_HINT_EXTENSIONS,
    POSITION_HINT_TOKENS,
    flags_for_position_token,
)


def _normalize_sku_for_filename(item_sku: Union[str, int]) -> str:
    return str(item_sku).strip().replace("/", "-").replace("\\", "-")


def _sku_based_stem_prefix(order_str: str, duplicate_index: int) -> str:
    if duplicate_index > 0:
        return f"{order_str}-{duplicate_index}-"
    return f"{order_str}-"


def _search_exact_image_stem(
    folder_path: str,
    expected_stem: str,
    exclude_path: Optional[str],
    extensions: Tuple[str, ...],
) -> Optional[str]:
    exts = tuple(ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions)
    for ext in exts:
        for candidate in (f"{expected_stem}{ext}", f"{expected_stem.lower()}{ext}"):
            file_path = os.path.join(folder_path, candidate)
            if os.path.exists(file_path) and file_path != exclude_path:
                return file_path

    expected_stem_lower = expected_stem.lower()
    for file in os.listdir(folder_path):
        file_lower = file.lower()
        file_stem = os.path.splitext(file_lower)[0]
        file_path = os.path.join(folder_path, file)
        if (
            file_stem == expected_stem_lower
            and any(file_lower.endswith(ext) for ext in exts)
            and file_path != exclude_path
        ):
            return file_path
    return None


def _search_exact_png_stem(
    folder_path: str,
    expected_stem: str,
    exclude_path: Optional[str]
) -> Optional[str]:
    return _search_exact_image_stem(folder_path, expected_stem, exclude_path, (".png",))


def find_sku_position_variant_files(
    order_number: Union[str, int],
    duplicate_index: int,
    item_sku: Optional[Union[str, int]],
    folder_path: Optional[str],
    exclude_path: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Companion JPEGs next to a SKU-named PNG. Token order: P, S, S1, S2."""
    if not folder_path or not os.path.isdir(folder_path):
        return []
    if item_sku is None or not str(item_sku).strip():
        return []
    sku_str = _normalize_sku_for_filename(item_sku)
    prefix = _sku_based_stem_prefix(str(order_number).strip(), duplicate_index)
    found: List[Dict[str, str]] = []
    for token in POSITION_HINT_TOKENS:
        stem = f"{prefix}{token}-{sku_str}"
        path = _search_exact_image_stem(folder_path, stem, exclude_path, POSITION_HINT_EXTENSIONS)
        if path:
            found.append({"path": path, "token": token})
    return found


def resolve_sku_position_hint(
    order_number: Union[str, int],
    duplicate_index: int,
    item_sku: Optional[Union[str, int]],
    folder_path: Optional[str],
    exclude_path: Optional[str] = None,
) -> Tuple[Optional[str], bool, bool]:
    """First companion JPEG only. Does not return the JPEG path — do not queue it."""
    companions = find_sku_position_variant_files(
        order_number, duplicate_index, item_sku, folder_path, exclude_path
    )
    if not companions:
        return None, False, False
    return flags_for_position_token(companions[0]["token"])


def _demo_design_fallback(kind: str, token: str):
    try:
        from shared.demo_images import demo_fallback_path

        path = demo_fallback_path(kind, token)
        return str(path) if path else None
    except ImportError:
        return None
