"""VBA-style single/double folder file search helpers."""

from __future__ import annotations

import os
from typing import List, Optional, Tuple

from src.io.file_utilities import IMAGE_EXTENSIONS


def _check_exact_variant(
    single_designs_folder: str,
    search_order: str,
    variant_suffix: str,
    is_pocket: bool,
    exclude_path: Optional[str]
) -> Optional[Tuple[str, bool, bool]]:
    file_path = os.path.join(single_designs_folder, f"{search_order}{variant_suffix}")
    if os.path.exists(file_path) and file_path != exclude_path:
        is_sleeve = not is_pocket
        return file_path, is_pocket, is_sleeve
    return None


def _check_case_insensitive_variant(
    single_designs_folder: str,
    search_order: str,
    variant_suffix: str,
    is_pocket: bool,
    exclude_path: Optional[str]
) -> Optional[Tuple[str, bool, bool]]:
    file_path = os.path.join(single_designs_folder, f"{search_order.lower()}{variant_suffix}")
    if os.path.exists(file_path) and file_path != exclude_path:
        is_sleeve = not is_pocket
        return file_path, is_pocket, is_sleeve
    return None


def _search_variants_in_directory(
    single_designs_folder: str,
    search_order: str,
    exclude_path: Optional[str]
) -> Tuple[Optional[str], bool, bool]:
    search_order_lower = search_order.lower()
    for file in os.listdir(single_designs_folder):
        file_lower = file.lower()
        file_name_without_ext = os.path.splitext(file_lower)[0]
        file_path = os.path.join(single_designs_folder, file)
        if file_lower.endswith('.png') and file_path != exclude_path:
            if file_name_without_ext == f"{search_order_lower}-p":
                return file_path, True, False
            if file_name_without_ext == f"{search_order_lower}-s":
                return file_path, False, True
    return None, False, False


def _search_single_variants(
    search_order: str,
    single_designs_folder: str,
    exclude_path: Optional[str]
) -> Tuple[Optional[str], bool, bool]:
    result = _check_exact_variant(single_designs_folder, search_order, "-P.png", True, exclude_path)
    if result:
        return result
    result = _check_exact_variant(single_designs_folder, search_order, "-S.png", False, exclude_path)
    if result:
        return result
    result = _check_case_insensitive_variant(single_designs_folder, search_order, "-p.png", True, exclude_path)
    if result:
        return result
    result = _check_case_insensitive_variant(single_designs_folder, search_order, "-s.png", False, exclude_path)
    if result:
        return result
    return _search_variants_in_directory(single_designs_folder, search_order, exclude_path)


def _search_single_regular(
    search_order: str,
    single_designs_folder: str,
    exclude_path: Optional[str]
) -> Optional[str]:
    for ext in IMAGE_EXTENSIONS:
        file_path = os.path.join(single_designs_folder, f"{search_order}{ext}")
        if os.path.exists(file_path) and file_path != exclude_path:
            return file_path

    search_order_lower = search_order.lower()
    for file in os.listdir(single_designs_folder):
        file_lower = file.lower()
        file_name_without_ext = os.path.splitext(file_lower)[0]
        file_path = os.path.join(single_designs_folder, file)
        if file_name_without_ext == search_order_lower:
            if any(file_lower.endswith(ext) for ext in IMAGE_EXTENSIONS) and file_path != exclude_path:
                return file_path
    return None


def _build_search_orders(
    order_str: str,
    order_str_with_suffix: str,
    duplicate_index: int
) -> List[str]:
    if duplicate_index > 0:
        return [order_str_with_suffix, order_str]
    return [order_str]


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


def _search_double_design(
    search_order: str,
    double_designs_folder: str,
    exclude_path: Optional[str]
) -> Optional[str]:
    for ext in IMAGE_EXTENSIONS:
        file_path = os.path.join(double_designs_folder, f"{search_order}{ext}")
        if os.path.exists(file_path) and file_path != exclude_path:
            return file_path

    search_order_lower = search_order.lower()
    for file in os.listdir(double_designs_folder):
        file_lower = file.lower()
        file_name_without_ext = os.path.splitext(file_lower)[0]
        file_path = os.path.join(double_designs_folder, file)
        if file_name_without_ext == search_order_lower:
            if any(file_lower.endswith(ext) for ext in IMAGE_EXTENSIONS) and file_path != exclude_path:
                return file_path
    return None


def _search_double_design_folder(
    order_str: str,
    order_str_with_suffix: str,
    duplicate_index: int,
    double_designs_folder: str,
    exclude_path: Optional[str]
) -> Tuple[Optional[str], Optional[str], bool, bool]:
    search_orders = _build_search_orders(order_str, order_str_with_suffix, duplicate_index)
    for search_order in search_orders:
        file_path = _search_double_design(search_order, double_designs_folder, exclude_path)
        if file_path:
            return file_path, 'double', False, False
    return None, None, False, False
