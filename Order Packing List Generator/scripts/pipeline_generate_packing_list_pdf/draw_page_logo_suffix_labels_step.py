"""Separate final step: suffix labels on black banner cells (Customise = Yes only).

Skipped when **Position** contains ``/`` (caller in ``draw_page_impl``); those rows
use raw Position text in the banners instead.

**Matching:** on each resolved file stem, side markers (``-f`` / ``-b`` / ``-p`` / ``-s``)
must appear **immediately after** the Logo/Design Image anchor for that slot (or the
first token for apparel). See ``label_from_stem_after_anchor`` in ``back_print_hint.py``.

**Where:** black banner cells — logo slots align with ``draw_position_banners_impl``
columns; apparel uses ``b0`` column 0 above the apparel cell.

Set ``LOGO_FILENAME_SUFFIX_LABEL_STEP_ENABLED`` to False to disable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

from scripts.pipeline_generate_packing_list_pdf.back_print_hint import (
    label_for_logo_slot,
    label_from_stem_after_anchor,
    resolve_apparel_logo_anchor,
)
from scripts.pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    _pdf_asset_log_line,
)

LOGO_FILENAME_SUFFIX_LABEL_STEP_ENABLED = True


def _banner_rect_apparel(
    *,
    image_area_x_pt: float,
    col_w_pt: float,
    b0_y_pt: float,
    banner_h_pt: float,
    rect_at: Callable[..., tuple],
) -> tuple[float, float, float, float]:
    """Black banner cell above the apparel column (b0, col 0)."""
    return rect_at(image_area_x_pt + 0 * col_w_pt, b0_y_pt, col_w_pt, banner_h_pt)


def _banner_rect_for_logo_slot(
    slot_index: int,
    *,
    image_area_x_pt: float,
    col_w_pt: float,
    b0_y_pt: float,
    b1_y_pt: float,
    banner_h_pt: float,
    rect_at: Callable[..., tuple],
) -> Optional[tuple[float, float, float, float]]:
    """Black banner cell above each logo column (matches draw_logo_square_rows / banners)."""
    if slot_index == 0:
        return rect_at(image_area_x_pt + 1 * col_w_pt, b0_y_pt, col_w_pt, banner_h_pt)
    if slot_index == 1:
        return rect_at(image_area_x_pt + 2 * col_w_pt, b0_y_pt, col_w_pt, banner_h_pt)
    if slot_index == 2:
        return rect_at(image_area_x_pt + 0 * col_w_pt, b1_y_pt, col_w_pt, banner_h_pt)
    if slot_index == 3:
        return rect_at(image_area_x_pt + 1 * col_w_pt, b1_y_pt, col_w_pt, banner_h_pt)
    if slot_index == 4:
        return rect_at(image_area_x_pt + 2 * col_w_pt, b1_y_pt, col_w_pt, banner_h_pt)
    return None


def run_logo_filename_suffix_label_step_impl(
    c,
    row_series,
    *,
    is_plain_order: bool,
    image_area_x_pt: float,
    col_w_pt: float,
    b0_y_pt: float,
    b1_y_pt: float,
    banner_h_pt: float,
    font_size_position: float,
    white,
    black,
    safe_str: Callable[[object], str],
    rect_at: Callable[..., tuple],
    draw_text_in_box: Callable[..., None],
    draw_rect: Callable[..., None],
    pt_h: Callable[[float], float],
    resolved_logo_path_for_slot: Callable[[int], Optional[Path]],
    logo_design_tokens: Callable[..., List[str]],
    fbpi_slots: List[Tuple[Path, str]],
    resolved_apparel_path: Optional[Path] = None,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> None:
    if not LOGO_FILENAME_SUFFIX_LABEL_STEP_ENABLED:
        return
    if is_plain_order:
        return
    if safe_str(row_series.get("Customise", "")).lower() != "yes":
        return

    proc = safe_str(row_series.get("Process and Item Number", ""))

    def _paint_banner_and_label(bx: float, by: float, bw: float, bh: float, label: str, where: str) -> None:
        draw_rect(c, bx, by, bw, bh, black)
        draw_text_in_box(
            c,
            bx,
            by,
            bw,
            bh,
            label,
            True,
            white,
            "center",
            font_size_position,
            vertical_nudge=pt_h(2),
            wrap=True,
        )
        _pdf_asset_log_line(
            pdf_asset_log,
            f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | suffix banner label | {where} | "
            f"text={label!r}",
        )

    apparel_anchor = resolve_apparel_logo_anchor(
        row_series,
        logo_design_tokens=logo_design_tokens,
    )
    if resolved_apparel_path is not None and apparel_anchor:
        alabel = label_from_stem_after_anchor(Path(resolved_apparel_path).stem, apparel_anchor)
        if alabel:
            ax, ay, aw, ah = _banner_rect_apparel(
                image_area_x_pt=image_area_x_pt,
                col_w_pt=col_w_pt,
                b0_y_pt=b0_y_pt,
                banner_h_pt=banner_h_pt,
                rect_at=rect_at,
            )
            _paint_banner_and_label(ax, ay, aw, ah, alabel, f"apparel file={resolved_apparel_path.name!r}")

    for slot_index in range(5):
        img_path = resolved_logo_path_for_slot(slot_index)
        if img_path is None:
            continue
        label = label_for_logo_slot(
            Path(img_path).stem,
            slot_index,
            row_series,
            fbpi_slots=fbpi_slots,
            logo_design_tokens=logo_design_tokens,
        )
        if not label:
            continue
        cell = _banner_rect_for_logo_slot(
            slot_index,
            image_area_x_pt=image_area_x_pt,
            col_w_pt=col_w_pt,
            b0_y_pt=b0_y_pt,
            b1_y_pt=b1_y_pt,
            banner_h_pt=banner_h_pt,
            rect_at=rect_at,
        )
        if cell is None:
            continue
        bx, by, bw, bh = cell
        _paint_banner_and_label(
            bx,
            by,
            bw,
            bh,
            label,
            f"logo slot {slot_index + 1} file={img_path.name!r}",
        )
