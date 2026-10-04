from typing import Callable, Dict, List, Optional, Tuple

from pipeline_generate_packing_list_pdf.back_print_hint import (
    BANNER_BLANK_LABELS,
    has_fbpi_side_files,
)
from pipeline_generate_packing_list_pdf.position_draw_mapping import (
    lookup_draw_for_position_code,
)


def draw_position_banners_impl(
    c,
    row_series,
    *,
    is_customised: bool,
    fbpi_slots: List[Tuple[object, str]],
    position_code_to_draw: Optional[Dict[str, str]],
    default_position_code: str,
    image_area_x_pt: float,
    col_w_pt: float,
    b0_y_pt: float,
    b1_y_pt: float,
    banner_h_pt: float,
    font_size_position: float,
    white,
    rect_at: Callable[..., tuple],
    draw_text_in_box: Callable[..., None],
    safe_str: Callable[..., str],
    position_tokens: Callable[..., List[str]],
    pt_h: Callable[[float], float],
) -> bool:
    raw_position_val = safe_str(row_series.get("Position", ""))
    position_has_slash = "/" in raw_position_val
    banner_source = raw_position_val
    if position_code_to_draw is not None and not position_has_slash:
        pos_code = safe_str(row_series.get("Position Code", ""))
        if pos_code == default_position_code:
            banner_source = ""
        elif pos_code:
            draw_val = safe_str(lookup_draw_for_position_code(position_code_to_draw, pos_code))
            if draw_val:
                banner_source = draw_val

    side_fbpi = has_fbpi_side_files(fbpi_slots)
    # Blank Position text when F/B/P/S side files drive logo slots (customise or normal).
    if banner_source and (not side_fbpi or position_has_slash):
        banner_tokens = position_tokens(banner_source)
        if banner_tokens:
            for i in range(2):
                if len(banner_tokens) > i:
                    col = i + 1
                    b0x, b0y, b0w, b0h = rect_at(image_area_x_pt + col * col_w_pt, b0_y_pt, col_w_pt, banner_h_pt)
                    draw_text_in_box(
                        c,
                        b0x,
                        b0y,
                        b0w,
                        b0h,
                        banner_tokens[i],
                        True,
                        white,
                        "center",
                        font_size_position,
                        vertical_nudge=pt_h(2),
                        wrap=True,
                    )
            for i in range(3):
                idx = i + 2
                if len(banner_tokens) > idx:
                    col = i
                    b1x, b1y, b1w, b1h = rect_at(image_area_x_pt + col * col_w_pt, b1_y_pt, col_w_pt, banner_h_pt)
                    draw_text_in_box(
                        c,
                        b1x,
                        b1y,
                        b1w,
                        b1h,
                        banner_tokens[idx],
                        True,
                        white,
                        "center",
                        font_size_position,
                        vertical_nudge=pt_h(2),
                        wrap=True,
                    )

    if not position_has_slash and fbpi_slots:
        # Customise keeps base in logo slot 0 → sides map to slots 1…; non-customise
        # sides-only fills from slot 0.
        slot_offset = 1 if is_customised else 0
        slot_to_banner: Dict[int, Tuple[int, float]] = {
            0: (1, b0_y_pt),
            1: (2, b0_y_pt),
            2: (0, b1_y_pt),
            3: (1, b1_y_pt),
            4: (2, b1_y_pt),
        }
        for idx, (_path, label) in enumerate(fbpi_slots):
            slot_index = idx + slot_offset
            banner_spec = slot_to_banner.get(slot_index)
            if banner_spec is None:
                continue
            col_idx, y_pt = banner_spec
            bx, by, bw, bh = rect_at(image_area_x_pt + col_idx * col_w_pt, y_pt, col_w_pt, banner_h_pt)
            draw_text_in_box(
                c,
                bx,
                by,
                bw,
                bh,
                "" if label in BANNER_BLANK_LABELS else label,
                True,
                white,
                "center",
                font_size_position,
                wrap=True,
            )

    return position_has_slash
