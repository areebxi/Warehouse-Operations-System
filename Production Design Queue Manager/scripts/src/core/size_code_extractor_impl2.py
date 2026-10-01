from __future__ import annotations
import pandas as pd
from typing import Optional, List, Set, Union, Dict, Tuple, Mapping
from src.io.file_handlers import extract_design_code, remove_apparel_size_prefix
from src.core.size_lookup_index import get_size_reference_index
from src.core.size_reference import _build_size_result

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
def _is_gender_garment_token(tokens: List[str], index: int) -> bool:
    """True when tokens[index] is the gender in a Gender-Garment pair (e.g. M-T)."""
    if index < 0 or index + 1 >= len(tokens):
        return False
    return tokens[index] in _GENDER_TOKENS and tokens[index + 1] in _GARMENT_TOKENS
