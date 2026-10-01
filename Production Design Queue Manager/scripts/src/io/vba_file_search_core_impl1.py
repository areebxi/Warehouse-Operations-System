from __future__ import annotations
import os
from typing import Dict, List, Optional, Tuple, Union
from src.core.sku_position_hints import POSITION_HINT_EXTENSIONS, POSITION_HINT_TOKENS, flags_for_position_token
from src.io.file_utilities import IMAGE_EXTENSIONS

def find_design_file_vba_logic(
    order_number: Union[str, int],
    duplicate_index: int,
    single_designs_folder: Optional[str] = None,
    double_designs_folder: Optional[str] = None,
    folder_type: Optional[str] = None,
    exclude_path: Optional[str] = None,
    item_sku: Optional[Union[str, int]] = None,
    is_duplicate_order: bool = False
) -> Tuple[Optional[str], Optional[str], bool, bool]:
    if not single_designs_folder and not double_designs_folder:
        return None, None, False, False

    order_str = str(order_number).strip()

    if is_duplicate_order and item_sku is not None and str(item_sku).strip():
        sku_str = _normalize_sku_for_filename(item_sku)
        expected_stem = f"{_sku_based_stem_prefix(order_str, duplicate_index)}{sku_str}"

        if single_designs_folder and (folder_type is None or folder_type == 'single'):
            file_path = _search_exact_png_stem(single_designs_folder, expected_stem, exclude_path)
            if file_path:
                return file_path, 'single', False, False
        if double_designs_folder and (folder_type is None or folder_type == 'double'):
            file_path = _search_exact_png_stem(double_designs_folder, expected_stem, exclude_path)
            if file_path:
                return file_path, 'double', False, False

        fallback_stems: List[str] = []
        if duplicate_index > 0:
            fallback_stems.append(f"{order_str}-{duplicate_index}")
        fallback_stems.append(order_str)

        if single_designs_folder and (folder_type is None or folder_type == 'single'):
            for stem in fallback_stems:
                file_path = _search_exact_png_stem(single_designs_folder, stem, exclude_path)
                if file_path:
                    return file_path, 'single', False, False
        if double_designs_folder and (folder_type is None or folder_type == 'double'):
            for stem in fallback_stems:
                file_path = _search_exact_png_stem(double_designs_folder, stem, exclude_path)
                if file_path:
                    return file_path, 'double', False, False
        return None, None, False, False

    order_str_with_suffix = f"{order_str}-{duplicate_index}" if duplicate_index > 0 else order_str

    if duplicate_index == 0:
        if single_designs_folder and (folder_type is None or folder_type == 'single'):
            result = _search_single_design_folder(
                order_str, order_str_with_suffix, duplicate_index, single_designs_folder, exclude_path, folder_type
            )
            if result[0]:
                return result
        if double_designs_folder and (folder_type is None or folder_type == 'double'):
            result = _search_double_design_folder(
                order_str, order_str_with_suffix, duplicate_index, double_designs_folder, exclude_path
            )
            if result[0]:
                return result
        return None, None, False, False

    def _search_single_for_order(search_order: str):
        if not single_designs_folder or (folder_type is not None and folder_type != 'single'):
            return None, None, False, False
        file_path, is_pocket, is_sleeve = _search_single_variants(search_order, single_designs_folder, exclude_path)
        if file_path:
            return file_path, 'single', is_pocket, is_sleeve
        file_path = _search_single_regular(search_order, single_designs_folder, exclude_path)
        if file_path:
            return file_path, 'single', False, False
        return None, None, False, False

    def _search_double_for_order(search_order: str):
        if not double_designs_folder or (folder_type is not None and folder_type != 'double'):
            return None, None, False, False
        file_path = _search_double_design(search_order, double_designs_folder, exclude_path)
        if file_path:
            return file_path, 'double', False, False
        return None, None, False, False

    result = _search_single_for_order(order_str_with_suffix)
    if result[0]:
        return result
    result = _search_double_for_order(order_str_with_suffix)
    if result[0]:
        return result
    result = _search_single_for_order(order_str)
    if result[0]:
        return result
    result = _search_double_for_order(order_str)
    if result[0]:
        return result

    fb = _demo_design_fallback("custom", order_str)
    if fb:
        return fb, "single", False, False
    fb = _demo_design_fallback("custom_double", order_str)
    if fb:
        return fb, "double", False, False
    return None, None, False, False
def _search_single_design_folder(
    order_str: str,
    order_str_with_suffix: str,
    duplicate_index: int,
    single_designs_folder: str,
    exclude_path: Optional[str],
    folder_type: Optional[str]
) -> Tuple[Optional[str], Optional[str], bool, bool]:
    search_orders = _build_search_orders(order_str, order_str_with_suffix, duplicate_index)
    for search_order in search_orders:
        file_path, is_pocket, is_sleeve = _search_single_variants(
            search_order, single_designs_folder, exclude_path
        )
        if file_path:
            return file_path, 'single', is_pocket, is_sleeve
    for search_order in search_orders:
        file_path = _search_single_regular(search_order, single_designs_folder, exclude_path)
        if file_path:
            return file_path, 'single', False, False
    if folder_type == 'single':
        return None, None, False, False
    return None, None, False, False
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
        if file_stem == expected_stem_lower and any(file_lower.endswith(ext) for ext in exts) and file_path != exclude_path:
            return file_path
    return None
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
def _search_exact_png_stem(
    folder_path: str,
    expected_stem: str,
    exclude_path: Optional[str]
) -> Optional[str]:
    return _search_exact_image_stem(folder_path, expected_stem, exclude_path, (".png",))
