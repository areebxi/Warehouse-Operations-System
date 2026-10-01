from __future__ import annotations
import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple
from pipeline_generate_packing_list_pdf.back_print_hint import (
    next_logo_slot_index,
    slot_is_back_print,
)

def _compute_back_print_layout(
    row_series,
    order_number_counts: dict,
    *,
    logo_image_for_slot: Callable[[int], Optional[Path]],
    get_field_value: Callable[..., str],
    fbpi_slots: List[Tuple[Path, str]],
    logo_design_tokens: Callable[..., List[str]],
    position_code_to_draw: Optional[Dict[str, str]],
    default_position_code: str,
    safe_str: Callable[..., str],
    position_tokens: Callable[..., List[str]],
) -> Tuple[Set[int], Set[int]]:
    """Return (slots_using_split_fallback, slots_reserved_for_back_reference_only)."""
    split_fallback: Set[int] = set()
    ref_only_slots: Set[int] = set()

    def _slot_has_own_logo(slot_index: int) -> bool:
        if logo_image_for_slot(slot_index) is not None:
            return True
        return bool(get_field_value(row_series, _LOGO_FIELDS[slot_index], order_number_counts))

    for slot_index in range(5):
        img_path = logo_image_for_slot(slot_index)
        if not slot_is_back_print(
            slot_index,
            img_path,
            fbpi_slots=fbpi_slots,
            row_series=row_series,
            position_code_to_draw=position_code_to_draw,
            default_position_code=default_position_code,
            safe_str=safe_str,
            position_tokens=position_tokens,
            logo_design_tokens=logo_design_tokens,
        ):
            continue

        next_slot = next_logo_slot_index(slot_index)
        if next_slot is not None and not _slot_has_own_logo(next_slot):
            ref_only_slots.add(next_slot)
        else:
            split_fallback.add(slot_index)

    return split_fallback, ref_only_slots
def _draw_prepared_image(
    c,
    prepared: object,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    image_reader_cls,
) -> None:
    if isinstance(prepared, io.BytesIO):
        c.drawImage(
            image_reader_cls(prepared),
            lx,
            ly,
            width=lw,
            height=lh,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )
    else:
        c.drawImage(
            str(prepared),
            lx,
            ly,
            width=lw,
            height=lh,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )
