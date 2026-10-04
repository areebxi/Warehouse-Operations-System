from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

from pipeline_generate_packing_list_pdf.back_print_hint_labels import (
    fbpi_side_label_for_slot,
    logo_filename_indicates_back,
    resolve_logo_anchor_for_slot,
)
from pipeline_generate_packing_list_pdf.core_helpers import classify_position_token_impl


def slot_is_back_print(
    slot_index: int,
    img_path: Optional[Path],
    *,
    fbpi_slots: List[Tuple[Path, str]],
    row_series,
    position_code_to_draw: Optional[dict[str, str]],
    default_position_code: str,
    safe_str: Callable[[object], str],
    position_tokens: Callable[..., List[str]],
    logo_design_tokens: Callable[..., List[str]],
) -> bool:
    """True when a resolved logo cell should show the back-print grid hint."""
    if img_path is None:
        return False

    anchor = resolve_logo_anchor_for_slot(
        slot_index,
        row_series,
        fbpi_slots=fbpi_slots,
        logo_design_tokens=logo_design_tokens,
    )
    fbpi_label = fbpi_side_label_for_slot(
        slot_index,
        fbpi_slots,
        sides_start_at_zero=bool(fbpi_slots)
        and safe_str(row_series.get("Customise", "")).lower() != "yes",
    )
    if logo_filename_indicates_back(img_path, anchor, fbpi_side_label=fbpi_label):
        return True

    raw_position_val = safe_str(row_series.get("Position", ""))
    if "/" not in raw_position_val:
        tokens = resolve_position_tokens_for_row(
            row_series,
            position_code_to_draw,
            default_position_code,
            safe_str=safe_str,
            position_tokens=position_tokens,
        )
        if slot_index < len(tokens):
            _has_front, _has_pocket, has_back = classify_position_token_impl(
                tokens[slot_index],
                safe_str=safe_str,
            )
            if has_back:
                return True

    return False


def resolve_position_tokens_for_row(
    row_series,
    position_code_to_draw: Optional[dict[str, str]],
    default_position_code: str,
    *,
    safe_str: Callable[[object], str],
    position_tokens: Callable[..., List[str]],
) -> List[str]:
    """Mirror banner position source from draw_page_banners_impl."""
    raw_position_val = safe_str(row_series.get("Position", ""))
    banner_source = raw_position_val
    if position_code_to_draw is not None and "/" not in raw_position_val:
        pos_code = safe_str(row_series.get("Position Code", ""))
        if pos_code == default_position_code:
            banner_source = ""
        elif pos_code:
            draw_val = safe_str(position_code_to_draw.get(pos_code, ""))
            if draw_val:
                banner_source = draw_val
    if not banner_source:
        return []
    return position_tokens(banner_source)


def next_logo_slot_index(slot_index: int) -> Optional[int]:
    """Logo slot index to the right in the same grid row, if any."""
    return {0: 1, 2: 3, 3: 4}.get(slot_index)
