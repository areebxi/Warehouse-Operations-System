from __future__ import annotations
import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple
from pipeline_generate_packing_list_pdf.draw_page_overlays_impl_part_a import _draw_logo_overlays_impl_part_a
from pipeline_generate_packing_list_pdf.draw_page_overlays_impl_part_b import _draw_logo_overlays_impl_part_b

def draw_logo_overlays_impl(c, row_series, *, is_plain_order: bool, has_explicit_fbpi_logo: bool, position_has_slash: bool, position_code_to_draw: Optional[Dict[str, str]], ax: float, ay: float, aw: float, ah: float, logo_image_for_slot: Callable[[int], object], logo_design_tokens: Callable[..., List[str]], safe_str: Callable[..., str], normalize_lower: Callable[..., str], prepare_image: Callable[..., object], image_reader_cls, pdf_asset_log: Optional[Callable[[str], None]]=None, pdf_page_index: int=0):
    ctx = _draw_logo_overlays_impl_part_a(c, row_series)
    return _draw_logo_overlays_impl_part_b(ctx)
