from __future__ import annotations
import pandas as pd
from typing import Optional, List, Set, Union, Dict, Tuple, Mapping
from src.io.file_handlers import extract_design_code, remove_apparel_size_prefix
from src.core.size_lookup_index import get_size_reference_index
from src.core.size_reference import _build_size_result

def _find_bare_base_match(
    sku_str: str,
    unique_codes: List[str],
    bracket_required_bases: Set[str],
) -> Optional[str]:
    """Return longest bare Merge_clean present in the SKU."""
    for code in unique_codes:
        if code in bracket_required_bases:
            continue
        if code in sku_str:
            return code
    return None
def _sku_hyphen_tokens(sku_str: str) -> List[str]:
    """Split a SKU into uppercase hyphen tokens (empty parts dropped).

    Trailing periods on tokens (e.g. ``YM..`` from Excel) are stripped so apparel
  bracket codes like ``-YM`` still match.
    """
    raw = [part.strip().upper() for part in sku_str.split("-") if part.strip()]
    # Excel can leave trailing periods on tokens (e.g. `YM..`). Strip those
    # so bracket codes like `-YM` still match size references.
    return [t.rstrip(".") for t in raw]
def _leading_dash_size_parts(bracket_code: str) -> Optional[List[str]]:
    """Split a leading-dash apparel bracket into hyphen tokens.

    ``-S`` → ``['S']``, ``-2XL`` → ``['2XL']``, ``-1-2Y`` → ``['1', '2Y']``.
    """
    if not bracket_code.startswith("-") or len(bracket_code) <= 1:
        return None
    parts = [p for p in bracket_code[1:].split("-") if p]
    return parts or None
def _strip_trailing_sku_flags(tokens: List[str]) -> List[str]:
    """Drop trailing Yes/No-style flags so apparel size is not forced to SKU end."""
    trimmed = list(tokens)
    while trimmed and trimmed[-1] in _TRAILING_SKU_FLAGS:
        trimmed.pop()
    return trimmed
