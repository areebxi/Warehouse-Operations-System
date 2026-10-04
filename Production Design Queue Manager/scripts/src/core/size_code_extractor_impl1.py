from __future__ import annotations
import pandas as pd
from typing import Optional, List, Set, Union, Dict, Tuple, Mapping
from src.io.file_handlers import extract_design_code, remove_apparel_size_prefix
from src.core.size_lookup_index import get_size_reference_index
from src.core.size_code_override import (
    PrintSizeOverrides,
    _as_override_map,
    _check_pocket_design,
    _detect_pocket_size_code,
    find_print_size_override,
)
from src.core.size_code_extractor_impl2 import (
    _bases_requiring_brackets,
    _extract_common_size_codes,
    _extract_pattern_based_codes,
    _find_bracket_match,
)
from src.core.size_code_extractor_impl3 import (
    _find_bare_base_match,
    _sku_hyphen_tokens,
)
from src.core.size_code_brackets import (
    _is_gender_garment_token,
    _leading_dash_size_parts,
    _strip_trailing_sku_flags,
)

def _search_reference_size_codes(sku_str: str, size_reference_df: pd.DataFrame) -> Optional[str]:
    """Search for size codes from reference file within SKU.

    Bracketed Size Reference rows (e.g. M261 (102722), M-T (B4A), M-T (-S))
    only match when both the base and the bracket apply to the SKU. Bases with
    brackets are skipped in the bare fallthrough so codes like A4 can still win.

    When both a bare base and a bracketed base match (e.g. 10AILG-M-T vs M-T (-L)),
    the longer base wins so design-specific rows beat short apparel templates.
    """
    index = get_size_reference_index(size_reference_df)
    bracket_required_bases = _bases_requiring_brackets(size_reference_df, index)

    unique_codes = (
        index.bases_longest_first
        if index is not None and index.bases_longest_first
        else None
    )
    if unique_codes is None:
        size_codes = size_reference_df['Merge_clean'].dropna().unique()
        valid_codes = []
        for code in size_codes:
            code_str = str(code).strip().upper()
            if code_str and code_str not in ('NAN', 'NONE'):
                valid_codes.append(code_str)

        seen = set()
        unique_codes = []
        for code in valid_codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)
        unique_codes.sort(key=len, reverse=True)

    bracket_hit = None
    if index is not None and index.brackets_by_base:
        tokens = _sku_hyphen_tokens(sku_str)
        token_set = set(tokens)
        bracket_hit = _find_bracket_match(sku_str, index, tokens, token_set)

    bare_hit = _find_bare_base_match(sku_str, unique_codes, bracket_required_bases)

    # When no bracket matched, allow bracket-required bases that still have a
    # dedicated bracket-free row (e.g. bare K-H alongside K-H (YS) (YXS)).
    bare_fallback = None
    if bare_hit is None and bracket_hit is None and index is not None:
        for code in unique_codes:
            if code not in bracket_required_bases:
                continue
            if code not in sku_str:
                continue
            if index.by_base.get(code) is None:
                continue
            bare_fallback = code
            break

    if bare_hit and bracket_hit:
        bracket_base = bracket_hit.split("|", 1)[0]
        if len(bare_hit) >= len(bracket_base):
            return bare_hit
        return bracket_hit
    if bracket_hit:
        return bracket_hit
    if bare_hit:
        return bare_hit
    if bare_fallback:
        return bare_fallback
    return None
def extract_size_code(
    sku: Union[str, pd.Series, None],
    size_reference_df: Optional[pd.DataFrame] = None,
    print_size_overrides: Optional[Union[PrintSizeOverrides, Set[str], Mapping]] = None,
) -> Optional[str]:
    """Extract size code from SKU by searching for known patterns.

    Override Print Size hits skip legacy F8 size-code derivation; dimensions are
    applied later via ``build_print_size_override_info``.
    """
    if not sku or pd.isna(sku):
        return None

    sku_str = str(sku).upper()
    overrides = _as_override_map(print_size_overrides)

    # New path: SKU Contain match — do not force F8; sizing comes from Width/Height
    if overrides and find_print_size_override(sku, overrides) is not None:
        pass
    elif isinstance(print_size_overrides, set) and print_size_overrides:
        # Legacy set-only pocket IDs still use F8 derivation
        design_id = extract_design_code(sku)
        if _check_pocket_design(design_id, print_size_overrides):
            pocket_code = _detect_pocket_size_code(sku_str)
            if pocket_code:
                return pocket_code

    parts = _sku_hyphen_tokens(sku_str)
    pattern_code = _extract_pattern_based_codes(parts)
    if pattern_code:
        return pattern_code

    common_code = _extract_common_size_codes(parts)
    if common_code:
        return common_code
    return None


def _bracket_matches_sku(bracket_code: str, tokens: List[str], token_set: Set[str]) -> bool:
    """Return True if a Size Reference bracket code applies to this SKU.

    Normal brackets (B4A, 102722, YS) must appear as a full hyphen token.
    Leading-dash apparel sizes (-S, -2XL, -1-2Y) match consecutive hyphen tokens
    anywhere in the SKU (not only the final token), ignoring trailing Yes/No
    flags. The gender letter in pairs like M-T / W-H is skipped so (-M) does
    not hit gender M. Multi-token ages like (-1-2Y) match SKU tails such as
    ``…-LPNK-1-2Y`` where ``1`` and ``2Y`` are separate tokens.
    """
    if not bracket_code:
        return False
    size_parts = _leading_dash_size_parts(bracket_code)
    if size_parts is not None:
        candidates = _strip_trailing_sku_flags(tokens)
        n = len(size_parts)
        if n > len(candidates):
            return False
        # Prefer the rightmost matching span (actual apparel size over earlier noise).
        for start in range(len(candidates) - n, -1, -1):
            if candidates[start : start + n] != size_parts:
                continue
            if n == 1 and _is_gender_garment_token(candidates, start):
                continue
            return True
        return False
    return bracket_code in token_set
