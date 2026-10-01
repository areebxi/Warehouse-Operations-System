"""
Size code extraction utilities for extracting size codes from SKUs.
"""
import pandas as pd
from typing import Optional, List, Set, Union, Dict, Tuple, Mapping
from src.io.file_handlers import extract_design_code, remove_apparel_size_prefix
from src.core.size_lookup_index import get_size_reference_index
from src.core.size_reference import _build_size_result
from src.core.size_code_extractor_impl1 import _search_reference_size_codes, extract_size_code, build_print_size_override_info, _bracket_matches_sku, hardcoded_pocket_dimensions_mm
from src.core.size_code_extractor_impl2 import _bases_requiring_brackets, _extract_pattern_based_codes, _detect_pocket_size_code, _as_override_map, _find_bracket_match, _extract_common_size_codes, find_print_size_override, _check_pocket_design, _is_gender_garment_token
from src.core.size_code_extractor_impl3 import _find_bare_base_match, _sku_hyphen_tokens, _leading_dash_size_parts, _strip_trailing_sku_flags

# SKU Contain token -> (width_mm, height_mm)
PrintSizeOverrides = Dict[str, Tuple[Optional[float], Optional[float]]]

OVERRIDE_MATCH_TYPE = "print_size_override"
OVERRIDE_FALLBACK_MATCH_TYPE = "print_size_override_fallback"


# Trailing customise / flag tokens that can follow apparel size (…-L-YES).
_TRAILING_SKU_FLAGS = frozenset({"YES", "Y", "NO", "N"})
# Gender + garment pairs (M-T, W-H, …) — gender token must not satisfy (-M).
_GENDER_TOKENS = frozenset({"M", "W", "K"})
_GARMENT_TOKENS = frozenset({"T", "H", "SS"})

