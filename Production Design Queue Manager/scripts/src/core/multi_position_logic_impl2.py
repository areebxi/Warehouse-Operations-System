from __future__ import annotations
from typing import Any, Dict, List, Optional
import pandas as pd
from src.core.size_reference import (
    _find_matching_row,
    _find_dimension_value,
    _build_size_result,
)
from src.core.size_lookup_index import get_size_reference_index

def _clean_str(value: Any) -> Optional[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    return text if text else None
