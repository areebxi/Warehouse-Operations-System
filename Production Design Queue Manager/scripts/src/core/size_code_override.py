"""Override Print Size + legacy pocket helpers for size codes."""
import pandas as pd
from typing import Optional, Set, Union, Dict, Tuple, Mapping
from src.io.file_handlers import remove_apparel_size_prefix
from src.core.size_reference import _build_size_result

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
