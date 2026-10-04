from __future__ import annotations
import os
from typing import List, Optional, Tuple, Union
from src.core.sku_position_hints import flags_for_position_token
from src.io.file_utilities import IMAGE_EXTENSIONS

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
def _search_single_variants(
    search_order: str,
    single_designs_folder: str,
    exclude_path: Optional[str]
) -> Tuple[Optional[str], bool, bool]:
    # Longer tokens first (S1/S2/SL/SR before S).
    png_variants = (
        ("-S1.png", False),
        ("-S2.png", False),
        ("-SL.png", False),
        ("-SR.png", False),
        ("-P.png", True),
        ("-S.png", False),
    )
    for suffix, is_pocket in png_variants:
        result = _check_exact_variant(
            single_designs_folder, search_order, suffix, is_pocket, exclude_path
        )
        if result:
            return result
    for suffix, is_pocket in png_variants:
        result = _check_case_insensitive_variant(
            single_designs_folder, search_order, suffix.lower(), is_pocket, exclude_path
        )
        if result:
            return result
    return _search_variants_in_directory(single_designs_folder, search_order, exclude_path)


def _search_variants_in_directory(
    single_designs_folder: str,
    search_order: str,
    exclude_path: Optional[str]
) -> Tuple[Optional[str], bool, bool]:
    search_order_lower = search_order.lower()
    # Longer sleeve tokens before plain -S so -S1/-SL are not missed.
    token_flags = (
        ("s1", False, True),
        ("s2", False, True),
        ("sl", False, True),
        ("sr", False, True),
        ("p", True, False),
        ("s", False, True),
    )
    for file in os.listdir(single_designs_folder):
        file_lower = file.lower()
        file_name_without_ext = os.path.splitext(file_lower)[0]
        file_path = os.path.join(single_designs_folder, file)
        if file_lower.endswith('.png') and file_path != exclude_path:
            for token, is_pocket, is_sleeve in token_flags:
                if file_name_without_ext == f"{search_order_lower}-{token}":
                    return file_path, is_pocket, is_sleeve
    return None, False, False


def resolve_sku_position_hint(
    order_number: Union[str, int],
    duplicate_index: int,
    item_sku: Optional[Union[str, int]],
    folder_path: Optional[str],
    exclude_path: Optional[str] = None,
) -> Tuple[Optional[str], bool, bool]:
    """First companion JPEG only. Does not return the JPEG path — do not queue it."""
    # Lazy import: impl1 imports this module at load time.
    from src.io.vba_file_search_core_impl1 import find_sku_position_variant_files

    companions = find_sku_position_variant_files(
        order_number, duplicate_index, item_sku, folder_path, exclude_path
    )
    if not companions:
        return None, False, False
    return flags_for_position_token(companions[0]["token"])


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
def _build_search_orders(
    order_str: str,
    order_str_with_suffix: str,
    duplicate_index: int
) -> List[str]:
    if duplicate_index > 0:
        return [order_str_with_suffix, order_str]
    return [order_str]
def _demo_design_fallback(kind: str, token: str):
    try:
        from shared.demo_images import demo_fallback_path

        path = demo_fallback_path(kind, token)
        return str(path) if path else None
    except ImportError:
        return None
def _sku_based_stem_prefix(order_str: str, duplicate_index: int) -> str:
    if duplicate_index > 0:
        return f"{order_str}-{duplicate_index}-"
    return f"{order_str}-"
def _normalize_sku_for_filename(item_sku: Union[str, int]) -> str:
    return str(item_sku).strip().replace("/", "-").replace("\\", "-")
