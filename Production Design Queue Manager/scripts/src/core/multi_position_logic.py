"""
Helpers for position-based multi design resolution across modes.
"""
from typing import Any, Dict, List, Optional

import pandas as pd

from src.core.size_reference import (
    _find_matching_row,
    _find_dimension_value,
    _build_size_result,
)
from src.core.size_lookup_index import get_size_reference_index
from src.core.multi_position_logic_impl1 import get_position_size_entries, _extract_size_info, build_positioned_stems, _to_int, _row_design_count, _row_suffix
from src.core.multi_position_logic_impl2 import _clean_str

