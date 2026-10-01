"""Draw the apparel square on a packing-list PDF page."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from pipeline_generate_packing_list_pdf.draw_page_image_primitives import (
    _draw_prepared_image,
    _pdf_asset_log_line,
)

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
