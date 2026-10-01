"""Draw one logo cell, including back-print hint layout."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from pipeline_generate_packing_list_pdf.back_print_hint import slot_is_back_print
from pipeline_generate_packing_list_pdf.draw_page_image_primitives import (
    _draw_back_print_reference,
    _draw_prepared_image,
    _draw_red_margin,
    _pdf_asset_log_line,
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

