"""Size-reference bracket / bare-base matching for size codes."""
import pandas as pd
from typing import Optional, List, Set
from src.core.size_lookup_index import get_size_reference_index

def _bases_requiring_brackets(
    size_reference_df: pd.DataFrame,
    index,
) -> Set[str]:
    """Return Merge_clean bases that have bracket codes and must not match bare."""
    if index is not None and index.brackets_by_base is not None:
        return {
            base
            for base, brackets in index.brackets_by_base.items()
            if brackets
        }

    required: Set[str] = set()
    if 'Merge_brackets' not in size_reference_df.columns:
        return required

    for _, row in size_reference_df.iterrows():
        base = str(row.get('Merge_clean', '')).strip().upper()
        if not base or base in ('NAN', 'NONE'):
            continue
        brackets = row.get('Merge_brackets', [])
        if isinstance(brackets, list) and any(str(b).strip() for b in brackets if pd.notna(b)):
            required.add(base)
    return required


def _sku_hyphen_tokens(sku_str: str) -> List[str]:
    """Split a SKU into uppercase hyphen tokens (empty parts dropped).

    Trailing periods on tokens (e.g. ``YM..`` from Excel) are stripped so apparel
  bracket codes like ``-YM`` still match.
    """
    raw = [part.strip().upper() for part in sku_str.split("-") if part.strip()]
    # Excel can leave trailing periods on tokens (e.g. `YM..`). Strip those
    # so bracket codes like `-YM` still match size references.
    return [t.rstrip(".") for t in raw]


# Trailing customise / flag tokens that can follow apparel size (…-L-YES).
_TRAILING_SKU_FLAGS = frozenset({"YES", "Y", "NO", "N"})
# Gender + garment pairs (M-T, W-H, …) — gender token must not satisfy (-M).
_GENDER_TOKENS = frozenset({"M", "W", "K"})
_GARMENT_TOKENS = frozenset({"T", "H", "SS"})


def _strip_trailing_sku_flags(tokens: List[str]) -> List[str]:
    """Drop trailing Yes/No-style flags so apparel size is not forced to SKU end."""
    trimmed = list(tokens)
    while trimmed and trimmed[-1] in _TRAILING_SKU_FLAGS:
        trimmed.pop()
    return trimmed


def _is_gender_garment_token(tokens: List[str], index: int) -> bool:
    """True when tokens[index] is the gender in a Gender-Garment pair (e.g. M-T)."""
    if index < 0 or index + 1 >= len(tokens):
        return False
    return tokens[index] in _GENDER_TOKENS and tokens[index + 1] in _GARMENT_TOKENS


def _leading_dash_size_parts(bracket_code: str) -> Optional[List[str]]:
    """Split a leading-dash apparel bracket into hyphen tokens.

    ``-S`` → ``['S']``, ``-2XL`` → ``['2XL']``, ``-1-2Y`` → ``['1', '2Y']``.
    """
    if not bracket_code.startswith("-") or len(bracket_code) <= 1:
        return None
    parts = [p for p in bracket_code[1:].split("-") if p]
    return parts or None


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


def _find_bracket_match(
    sku_str: str,
    index,
    tokens: List[str],
    token_set: Set[str],
) -> Optional[str]:
    """Return BASE|BRACKET for the longest matching bracketed base."""
    for base_code in index.bases_longest_first:
        if base_code not in sku_str:
            continue
        # Longest bracket first so (-1-2Y) wins over a shorter (-1) if both exist.
        brackets = sorted(
            index.brackets_by_base.get(base_code, ()),
            key=len,
            reverse=True,
        )
        for bracket_code in brackets:
            if _bracket_matches_sku(bracket_code, tokens, token_set):
                return f"{base_code}|{bracket_code}"
    return None


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
