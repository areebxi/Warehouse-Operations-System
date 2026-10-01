from __future__ import annotations
import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    _pdf_asset_log_line,
)
from pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)

def _draw_logo_overlays_impl_part_a(c, row_series, *, is_plain_order: bool, has_explicit_fbpi_logo: bool, position_has_slash: bool, position_code_to_draw: Optional[Dict[str, str]], ax: float, ay: float, aw: float, ah: float, logo_image_for_slot: Callable[[int], object], logo_design_tokens: Callable[..., List[str]], safe_str: Callable[..., str], normalize_lower: Callable[..., str], prepare_image: Callable[..., object], image_reader_cls, pdf_asset_log: Optional[Callable[[str], None]]=None, pdf_page_index: int=0):
    if is_plain_order or has_explicit_fbpi_logo:
        return

    proc = str(row_series.get("Process and Item Number", "") or "").strip()

    logo_tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
    front_chest_scale = 2.5
    front_w = aw / front_chest_scale
    front_h = ah / front_chest_scale
    front_lx = ax + aw * 0.3
    front_ly = ay + ah * 0.4

    pocket_scale = 6.0
    pocket_w = aw / pocket_scale
    pocket_h = ah / pocket_scale
    pocket_lx = ax + aw * 0.555
    pocket_ly = ay + ah * 0.675

    left_forearm_scale = 6.0
    left_forearm_w = aw / left_forearm_scale
    left_forearm_h = ah / left_forearm_scale
    left_forearm_lx = ax + aw * 0.735
    left_forearm_ly = ay + ah * 0.185

    right_forearm_scale = left_forearm_scale
    right_forearm_w = aw / right_forearm_scale

    return {"c": c, "front_chest_scale": front_chest_scale, "front_h": front_h, "front_lx": front_lx, "front_ly": front_ly, "front_w": front_w, "left_forearm_h": left_forearm_h, "left_forearm_lx": left_forearm_lx, "left_forearm_ly": left_forearm_ly, "left_forearm_scale": left_forearm_scale, "left_forearm_w": left_forearm_w, "logo_tokens": logo_tokens, "pocket_h": pocket_h, "pocket_lx": pocket_lx, "pocket_ly": pocket_ly, "pocket_scale": pocket_scale, "pocket_w": pocket_w, "proc": proc, "right_forearm_scale": right_forearm_scale, "right_forearm_w": right_forearm_w, "row_series": row_series}
