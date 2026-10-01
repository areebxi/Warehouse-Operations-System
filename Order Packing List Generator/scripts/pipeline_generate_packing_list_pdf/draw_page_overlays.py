"""Logo overlays on packing-list apparel mockup — stable façade."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

from pipeline_generate_packing_list_pdf.draw_page_overlays_geom import (
    geometry_keys_from_draw_tokens,
    overlay_slot_geometry,
)
from pipeline_generate_packing_list_pdf.draw_page_overlays_place import place_logo_overlays
from pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)


def draw_logo_overlays_impl(
    c,
    row_series,
    *,
    is_plain_order: bool,
    has_explicit_fbpi_logo: bool,
    position_has_slash: bool,
    position_code_to_draw: Optional[Dict[str, str]],
    ax: float,
    ay: float,
    aw: float,
    ah: float,
    logo_image_for_slot: Callable[[int], object],
    logo_design_tokens: Callable[..., List[str]],
    safe_str: Callable[..., str],
    normalize_lower: Callable[..., str],
    prepare_image: Callable[..., object],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> None:
    if is_plain_order or has_explicit_fbpi_logo:
        return

    proc = str(row_series.get("Process and Item Number", "") or "").strip()
    logo_tokens = logo_design_tokens(row_series.get("Logo/Design Image"))
    geometry_by_key = overlay_slot_geometry(ax, ay, aw, ah)

    draw_tokens: List[str] = []
    if position_code_to_draw is not None and not position_has_slash:
        position_code = safe_str(row_series.get("Position Code", ""))
        if position_code:
            raw_draw = lookup_draw_for_position_code(position_code_to_draw, position_code)
            if raw_draw:
                draw_tokens = [t.strip() for t in str(raw_draw).split(",") if t.strip()][:5]

    geometry_keys = geometry_keys_from_draw_tokens(
        draw_tokens, normalize_lower=normalize_lower
    )
    place_logo_overlays(
        c,
        proc=proc,
        logo_tokens=logo_tokens,
        geometry_keys=geometry_keys,
        geometry_by_key=geometry_by_key,
        logo_image_for_slot=logo_image_for_slot,
        prepare_image=prepare_image,
        image_reader_cls=image_reader_cls,
        pdf_asset_log=pdf_asset_log,
        pdf_page_index=pdf_page_index,
    )


draw_logo_overlays = draw_logo_overlays_impl
