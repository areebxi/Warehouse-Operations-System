"""
Core VBA logic file search utilities for finding design files using order numbers.
"""
import os
from typing import Dict, List, Optional, Tuple, Union

from src.core.sku_position_hints import POSITION_HINT_EXTENSIONS, POSITION_HINT_TOKENS, flags_for_position_token
from src.io.file_utilities import IMAGE_EXTENSIONS
from src.io.vba_file_search_core_impl1 import find_design_file_vba_logic, _search_single_design_folder, _search_exact_image_stem, find_sku_position_variant_files, _search_exact_png_stem
from src.io.vba_file_search_core_impl2 import _search_single_regular, _search_double_design, _search_single_variants, _search_variants_in_directory, resolve_sku_position_hint, _search_double_design_folder, _check_exact_variant, _check_case_insensitive_variant, _build_search_orders, _demo_design_fallback, _sku_based_stem_prefix, _normalize_sku_for_filename


