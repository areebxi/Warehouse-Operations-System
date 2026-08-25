"""
Size code extraction utilities for extracting size codes from SKUs.
"""
import pandas as pd
from typing import Optional, List, Set, Union, Dict, Tuple, Mapping
from src.io.file_handlers import extract_design_code, remove_apparel_size_prefix
from src.core.size_lookup_index import get_size_reference_index
from src.core.size_reference import _build_size_result

# SKU Contain token -> (width_mm, height_mm)
PrintSizeOverrides = Dict[str, Tuple[Optional[float], Optional[float]]]

OVERRIDE_MATCH_TYPE = "print_size_override"
OVERRIDE_FALLBACK_MATCH_TYPE = "print_size_override_fallback"


def _as_override_map(
    print_size_overrides: Optional[Union[PrintSizeOverrides, Set[str], Mapping]],
) -> PrintSizeOverrides:
    """Normalize legacy set or new dict into a contain->dims map."""
    if not print_size_overrides:
        return {}
    if isinstance(print_size_overrides, set):
        return {str(token).strip(): (None, None) for token in print_size_overrides if str(token).strip()}
    result: PrintSizeOverrides = {}
    for token, dims in print_size_overrides.items():
        key = str(token).strip()
        if not key:
            continue
        if dims is None:
            result[key] = (None, None)
        elif isinstance(dims, tuple) and len(dims) == 2:
            result[key] = (dims[0], dims[1])
        else:
            result[key] = (None, None)
    return result


def find_print_size_override(
    sku: Union[str, pd.Series, None],
    print_size_overrides: Optional[Union[PrintSizeOverrides, Set[str], Mapping]] = None,
) -> Optional[Tuple[str, Optional[float], Optional[float]]]:
    """Return longest SKU Contain match: (token, width_mm, height_mm)."""
    overrides = _as_override_map(print_size_overrides)
    if not overrides or sku is None or (isinstance(sku, float) and pd.isna(sku)):
        return None

    sku_str = str(sku).upper()
    best: Optional[Tuple[str, Optional[float], Optional[float]]] = None
    best_len = -1
    for token, dims in overrides.items():
        token_upper = token.upper()
        if token_upper and token_upper in sku_str and len(token_upper) > best_len:
            best = (token, dims[0], dims[1])
            best_len = len(token_upper)
    return best


def hardcoded_pocket_dimensions_mm(sku: Union[str, pd.Series, None]) -> Tuple[float, float]:
    """Legacy pocket fallback: 65x80 kids, otherwise 80x100."""
    sku_str = str(sku).upper() if sku is not None and not (isinstance(sku, float) and pd.isna(sku)) else ""
    if "-K-" in sku_str:
        return 65.0, 80.0
    return 80.0, 100.0


def build_print_size_override_info(
    sku: Union[str, pd.Series, None],
    print_size_overrides: Optional[Union[PrintSizeOverrides, Set[str], Mapping]],
    mm_to_pixel_factor: float,
) -> Optional[Dict[str, float]]:
    """Build size_info from Override Print Size, or hardcoded dims when Width/Height blank."""
    hit = find_print_size_override(sku, print_size_overrides)
    if hit is None:
        return None

    token, width_mm, height_mm = hit
    if width_mm is not None and height_mm is not None:
        return _build_size_result(
            float(width_mm),
            float(height_mm),
            mm_to_pixel_factor,
            token,
            f"Override Print Size: {token}",
            OVERRIDE_MATCH_TYPE,
            "Width",
            "Height",
        )

    fb_w, fb_h = hardcoded_pocket_dimensions_mm(sku)
    return _build_size_result(
        fb_w,
        fb_h,
        mm_to_pixel_factor,
        token,
        f"Override Print Size: {token} (fallback)",
        OVERRIDE_FALLBACK_MATCH_TYPE,
        "hardcoded_width",
        "hardcoded_height",
    )


def _check_pocket_design(design_id: Optional[str], pocket_design_ids_set: Set[str]) -> bool:
    """Legacy exact design-ID membership check (with/without apparel prefix)."""
    if not design_id:
        return False

    if design_id in pocket_design_ids_set:
        return True

    design_id_no_prefix = remove_apparel_size_prefix(design_id)
    if design_id_no_prefix and design_id_no_prefix in pocket_design_ids_set:
        return True

    return False


def _detect_pocket_size_code(sku_str: str) -> Optional[str]:
    """Detect F8-based size code for pocket designs from SKU (legacy)."""
    gender = None
    garment_type = None

    if '-M-' in sku_str:
        gender = 'M'
    elif '-W-' in sku_str:
        gender = 'W'
    elif '-K-' in sku_str:
        gender = 'K'

    if '-T-' in sku_str:
        garment_type = 'T'
    elif '-H-' in sku_str:
        garment_type = 'H'

    if gender and garment_type:
        return f"F8-{gender}-{garment_type}"

    return None


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

def _extract_pattern_based_codes(parts: List[str]) -> Optional[str]:
    """Extract size codes using pattern matching (single letter pairs)."""
    potential_codes = []
    for i in range(len(parts) - 1):
        part1 = parts[i].strip()
        part2 = parts[i + 1].strip()

        if (
            len(part1) == 1
            and len(part2) == 1
            and part1.isalpha()
            and part2.isalpha()
        ):
            potential_codes.append((f"{part1}-{part2}", i))

    for code, _ in potential_codes:
        if code.endswith('-T'):
            return code

    if potential_codes:
        return potential_codes[-1][0]

    return None


def _extract_common_size_codes(parts: List[str]) -> Optional[str]:
    """Extract common size codes (A4, A5, BS, etc.) from SKU parts."""
    for part in parts:
        part_clean = part.strip()
        if len(part_clean) >= 2 and len(part_clean) <= 4:
            if part_clean in ['A4', 'A5', 'A6', 'A3', 'BS', 'BG', 'QD', 'SH', 'W', 'C']:
                return part_clean

            if (
                2 <= len(part_clean) <= 4
                and any(c.isalpha() for c in part_clean)
                and part_clean
                not in [
                    'BLK', 'RED', 'NVY', 'WHI', 'PRP', 'RBL', 'BGNDY',
                    'M', 'L', 'XL', '2XL', '4XL', 'YS', 'YM', 'YL',
                ]
            ):
                return part_clean

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

    if size_reference_df is not None and 'Merge_clean' in size_reference_df.columns:
        if len(size_reference_df) > 0:
            ref = _search_reference_size_codes(sku_str, size_reference_df)
            if ref:
                return ref

    parts = _sku_hyphen_tokens(sku_str)
    bracket_required = set()
    if size_reference_df is not None and 'Merge_clean' in size_reference_df.columns:
        bracket_required = _bases_requiring_brackets(
            size_reference_df, get_size_reference_index(size_reference_df)
        )

    pattern_code = _extract_pattern_based_codes(parts)
    if pattern_code and pattern_code not in bracket_required:
        return pattern_code

    common_code = _extract_common_size_codes(parts)
    if common_code and common_code not in bracket_required:
        return common_code
    return None
