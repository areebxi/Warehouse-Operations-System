"""
Core VBA logic file search utilities for finding design files using order numbers.
"""
import os
from typing import Optional, List, Tuple, Union

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


def _search_exact_png_stem(
    folder_path: str,
    expected_stem: str,
    exclude_path: Optional[str]
) -> Optional[str]:
    for candidate in (f"{expected_stem}.png", f"{expected_stem.lower()}.png"):
        file_path = os.path.join(folder_path, candidate)
        if os.path.exists(file_path) and file_path != exclude_path:
            return file_path

    expected_stem_lower = expected_stem.lower()
    for file in os.listdir(folder_path):
        file_lower = file.lower()
        file_stem = os.path.splitext(file_lower)[0]
        file_path = os.path.join(folder_path, file)
        if file_lower.endswith('.png') and file_stem == expected_stem_lower and file_path != exclude_path:
            return file_path
    return None


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
        sku_str = str(item_sku).strip().replace('/', '-').replace('\\', '-')
        expected_stem = f"{order_str}-{duplicate_index}-{sku_str}" if duplicate_index > 0 else f"{order_str}-{sku_str}"

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
    return None, None, False, False
