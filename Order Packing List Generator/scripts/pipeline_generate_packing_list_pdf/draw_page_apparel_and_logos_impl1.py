from __future__ import annotations
import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple
from pipeline_generate_packing_list_pdf.back_print_hint import (
    next_logo_slot_index,
    slot_is_back_print,
)

def draw_logo_square_rows_impl(
    c,
    row_series,
    order_number_counts: dict,
    *,
    is_plain_order: bool,
    image_area_x_pt: float,
    col_w_pt: float,
    s1_y_pt: float,
    s2_y_pt: float,
    square_s_pt: float,
    s2_square_h_pt: float,
    font_size_banner: float,
    black,
    red,
    rect_at: Callable[..., tuple],
    get_field_value: Callable[..., str],
    logo_image_for_slot: Callable[[int], Optional[Path]],
    prepare_image: Callable[..., object],
    draw_text_in_box: Callable[..., None],
    image_reader_cls,
    fbpi_slots: Optional[List[Tuple[Path, str]]] = None,
    position_code_to_draw: Optional[Dict[str, str]] = None,
    default_position_code: str = "X",
    position_tokens: Optional[Callable[..., List[str]]] = None,
    safe_str: Optional[Callable[..., str]] = None,
    back_print_image_path: Optional[Path] = None,
    logo_design_tokens: Optional[Callable[..., List[str]]] = None,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> bool:
    had_missing_logo = False
    proc = str(row_series.get("Process and Item Number", "") or "").strip()
    fbpi_slots = fbpi_slots or []
    _safe_str = safe_str or (lambda v: str(v or "").strip())
    _position_tokens = position_tokens or (lambda _v: [])
    _logo_design_tokens = logo_design_tokens or (lambda _v: [])

    slot_grid = [
        (1, 0, s1_y_pt, square_s_pt),
        (2, 1, s1_y_pt, square_s_pt),
        (0, 2, s2_y_pt, s2_square_h_pt),
        (1, 3, s2_y_pt, s2_square_h_pt),
        (2, 4, s2_y_pt, s2_square_h_pt),
    ]

    split_fallback_slots: Set[int] = set()
    back_ref_only_slots: Set[int] = set()
    if not is_plain_order:
        split_fallback_slots, back_ref_only_slots = _compute_back_print_layout(
            row_series,
            order_number_counts,
            logo_image_for_slot=logo_image_for_slot,
            get_field_value=get_field_value,
            fbpi_slots=fbpi_slots,
            logo_design_tokens=_logo_design_tokens,
            position_code_to_draw=position_code_to_draw,
            default_position_code=default_position_code,
            safe_str=_safe_str,
            position_tokens=_position_tokens,
        )

    def _cell_rect(col: int, y_pt: float, h_pt: float) -> Tuple[float, float, float, float]:
        return rect_at(image_area_x_pt + col * col_w_pt, y_pt, col_w_pt, h_pt)

    def _draw_slot(col: int, idx: int, y_pt: float, h_pt: float) -> None:
        nonlocal had_missing_logo
        lx, ly, lw, lh = _cell_rect(col, y_pt, h_pt)
        slot_label = _SLOT_LABELS[idx]
        logo_field = _LOGO_FIELDS[idx]

        if is_plain_order:
            if idx == 0 and y_pt == s1_y_pt:
                draw_text_in_box(c, lx, ly, lw, lh, "Plain Order", True, red, "center", font_size=font_size_banner)
            else:
                draw_text_in_box(c, lx, ly, lw, lh, "", False, black, "center")
            return

        if idx in back_ref_only_slots:
            return

        logo_val = get_field_value(row_series, logo_field, order_number_counts)
        img_path = logo_image_for_slot(idx)
        if img_path:
            next_col_rect: Optional[Tuple[float, float, float, float]] = None
            if idx not in split_fallback_slots:
                next_slot = next_logo_slot_index(idx)
                if next_slot is not None and next_slot in back_ref_only_slots:
                    ncol, _nidx, ny_pt, nh_pt = slot_grid[next_slot]
                    next_col_rect = _cell_rect(ncol, ny_pt, nh_pt)

            try:
                _draw_logo_cell_image(
                    c,
                    img_path,
                    lx,
                    ly,
                    lw,
                    lh,
                    slot_index=idx,
                    slot_label=slot_label,
                    proc=proc,
                    row_series=row_series,
                    fbpi_slots=fbpi_slots,
                    position_code_to_draw=position_code_to_draw,
                    default_position_code=default_position_code,
                    safe_str=_safe_str,
                    position_tokens=_position_tokens,
                    logo_design_tokens=_logo_design_tokens,
                    back_print_image_path=back_print_image_path,
                    prepare_image=prepare_image,
                    image_reader_cls=image_reader_cls,
                    pdf_asset_log=pdf_asset_log,
                    pdf_page_index=pdf_page_index,
                    use_split_fallback=idx in split_fallback_slots,
                    next_col_rect=next_col_rect,
                )
            except Exception as e:
                had_missing_logo = True
                print(f"Logo draw failed: {e!r} path={img_path}", file=sys.stderr)
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} draw FAILED | "
                    f"attempted file={img_path.name!r} | path={img_path} | error={e!r}",
                )
                draw_text_in_box(c, lx, ly, lw, lh, "L", True, red, "center", font_size=font_size_banner + 8)
            else:
                try:
                    abs_p = str(img_path.resolve())
                except OSError:
                    abs_p = str(img_path)
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label.upper()} drawn on PDF | "
                    f"file_name={img_path.name!r} | full_path={abs_p}",
                )
        elif logo_val:
            had_missing_logo = True
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} not drawn | "
                f"no file for field value={logo_val!r}",
            )
            draw_text_in_box(c, lx, ly, lw, lh, "L", True, red, "center", font_size=font_size_banner + 8)
        else:
            draw_text_in_box(c, lx, ly, lw, lh, "", False, black, "center")

    for col, idx, y_pt, h_pt in slot_grid:
        _draw_slot(col, idx, y_pt, h_pt)

    return had_missing_logo
def _draw_back_print_reference(
    c,
    ref_path: Path,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    *,
    prepare_image: Callable[..., object],
    image_reader_cls,
) -> None:
    prepared_ref = prepare_image(ref_path, lw, lh)
    _draw_prepared_image(c, prepared_ref, lx, ly, lw, lh, image_reader_cls)
    _draw_red_margin(c, lx, ly, lw, lh)
def _pdf_asset_log_line(log: Optional[Callable[[str], None]], line: str) -> None:
    if not log:
        return
    try:
        log(line)
    except Exception:
        pass
