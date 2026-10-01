"""Size-reference search orchestration for size codes."""
import pandas as pd
from typing import Optional
from src.core.size_lookup_index import get_size_reference_index
from src.core.size_code_brackets import (
    _bases_requiring_brackets,
    _find_bare_base_match,
    _find_bracket_match,
    _sku_hyphen_tokens,
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
