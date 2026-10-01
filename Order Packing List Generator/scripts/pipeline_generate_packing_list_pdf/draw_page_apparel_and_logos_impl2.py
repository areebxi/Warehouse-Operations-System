from __future__ import annotations
import io
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple
from pipeline_generate_packing_list_pdf.back_print_hint import (
    next_logo_slot_index,
    slot_is_back_print,
)

def _draw_logo_cell_image(
    c,
    img_path: Path,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    *,
    slot_index: int,
    slot_label: str,
    proc: str,
    row_series,
    fbpi_slots: List[Tuple[Path, str]],
    position_code_to_draw: Optional[Dict[str, str]],
    default_position_code: str,
    safe_str: Callable[..., str],
    position_tokens: Callable[..., List[str]],
    logo_design_tokens: Callable[..., List[str]],
    back_print_image_path: Optional[Path],
    prepare_image: Callable[..., object],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]],
    pdf_page_index: int,
    use_split_fallback: bool,
    next_col_rect: Optional[Tuple[float, float, float, float]],
) -> None:
    show_back_hint = slot_is_back_print(
        slot_index,
        img_path,
        fbpi_slots=fbpi_slots,
        row_series=row_series,
        position_code_to_draw=position_code_to_draw,
        default_position_code=default_position_code,
        safe_str=safe_str,
        position_tokens=position_tokens,
        logo_design_tokens=logo_design_tokens,
    )

    if show_back_hint:
        ref_path = back_print_image_path
        has_ref_file = ref_path is not None and ref_path.is_file()

        if use_split_fallback:
            half_w = lw / 2
            prepared_logo = prepare_image(img_path, half_w, lh)
            _draw_prepared_image(c, prepared_logo, lx, ly, half_w, lh, image_reader_cls)
            _draw_red_margin(c, lx, ly, half_w, lh)
            if has_ref_file:
                _draw_back_print_reference(
                    c, ref_path, lx + half_w, ly, half_w, lh,
                    prepare_image=prepare_image, image_reader_cls=image_reader_cls,
                )
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                    f"back-print hint drawn (split cell fallback) | logo={img_path.name!r} | "
                    f"reference={ref_path.name!r}",
                )
            else:
                _pdf_asset_log_line(
                    pdf_asset_log,
                    f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                    f"back-print hint partial (split cell, logo only) | "
                    f"reference image missing | expected={ref_path!r}",
                )
            return

        prepared_logo = prepare_image(img_path, lw, lh)
        _draw_prepared_image(c, prepared_logo, lx, ly, lw, lh, image_reader_cls)
        _draw_red_margin(c, lx, ly, lw, lh)

        if next_col_rect is not None and has_ref_file:
            nx, ny, nw, nh = next_col_rect
            _draw_back_print_reference(
                c, ref_path, nx, ny, nw, nh,
                prepare_image=prepare_image, image_reader_cls=image_reader_cls,
            )
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                f"back-print hint drawn (next column) | logo={img_path.name!r} | "
                f"reference={ref_path.name!r}",
            )
        else:
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | {slot_label} | "
                f"back-print hint partial (logo only) | reference image missing | "
                f"expected={ref_path!r}",
            )
        return

    prepared = prepare_image(img_path, lw, lh)
    _draw_prepared_image(c, prepared, lx, ly, lw, lh, image_reader_cls)
def draw_apparel_square_impl(
    c,
    row_series,
    order_number_counts: dict,
    *,
    is_plain_order: bool,
    image_area_x_pt: float,
    s1_y_pt: float,
    col_w_pt: float,
    square_s_pt: float,
    font_size_banner: float,
    black,
    red,
    rect_at: Callable[..., tuple],
    get_field_value: Callable[..., str],
    safe_str: Callable[..., str],
    find_image: Callable[..., Optional[Path]],
    apparel_image_dir,
    apparel_stem_map,
    prepare_image: Callable[..., object],
    draw_text_in_box: Callable[..., None],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> tuple[float, float, float, float, bool]:
    had_missing_apparel = False
    ax, ay, aw, ah = rect_at(image_area_x_pt, s1_y_pt, col_w_pt, square_s_pt)
    apparel_text = get_field_value(row_series, "Apparel Image", order_number_counts)
    has_apparel_lookup = apparel_image_dir is not None or apparel_stem_map is not None
    apparel_img_path: Optional[Path] = None
    if has_apparel_lookup:
        for name in (apparel_text, safe_str(row_series.get("Picture Name", ""))):
            if not name:
                continue
            candidate = find_image(apparel_image_dir, name, apparel_stem_map, recursive=False)
            if candidate is not None:
                apparel_img_path = candidate
                break
    if apparel_img_path:
        prepared = prepare_image(apparel_img_path, aw, ah)
        proc = safe_str(row_series.get("Process and Item Number", ""))
        try:
            _draw_prepared_image(c, prepared, ax, ay, aw, ah, image_reader_cls)
        except Exception as exc:
            had_missing_apparel = True
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | APPAREL draw FAILED | "
                f"attempted file={apparel_img_path.name!r} | path={apparel_img_path} | error={exc!r}",
            )
            draw_text_in_box(c, ax, ay, aw, ah, apparel_text, False, black, "center")
        else:
            try:
                abs_path = str(apparel_img_path.resolve())
            except OSError:
                abs_path = str(apparel_img_path)
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | APPAREL drawn on PDF | "
                f"file_name={apparel_img_path.name!r} | full_path={abs_path}",
            )
    elif apparel_text:
        had_missing_apparel = True
        proc = safe_str(row_series.get("Process and Item Number", ""))
        _pdf_asset_log_line(
            pdf_asset_log,
            f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | APPAREL not drawn | "
            f"no image file resolved for tokens Apparel Image={apparel_text!r} "
            f"Picture Name={safe_str(row_series.get('Picture Name', ''))!r}",
        )
        draw_text_in_box(c, ax, ay, aw, ah, "A", True, red, "center", font_size=font_size_banner + 8)
    else:
        draw_text_in_box(c, ax, ay, aw, ah, apparel_text, False, black, "center")
    return ax, ay, aw, ah, had_missing_apparel
def _draw_red_margin(c, lx: float, ly: float, lw: float, lh: float) -> None:
    line_w = max(1.5, min(lw, lh) * 0.02)
    c.setStrokeColorRGB(1, 0, 0)
    c.setLineWidth(line_w)
    c.rect(lx, ly, lw, lh, fill=0, stroke=1)
