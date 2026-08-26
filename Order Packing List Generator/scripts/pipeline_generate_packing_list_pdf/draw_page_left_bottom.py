import re
from typing import Callable, List, Optional, Tuple

from scripts.pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    _pdf_asset_log_line,
)
from scripts.pipeline_generate_packing_list_pdf import pdf_page_layout as L

_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def _url_from_gift_message(gift_message: str) -> str:
    if not gift_message:
        return ""
    match = _URL_PATTERN.search(gift_message.strip())
    if not match:
        return ""
    return match.group(0).rstrip(".,;)")


def _notes_from_buyer(row_series, safe_str: Callable[..., str]) -> str:
    note = safe_str(row_series.get("Notes From Buyer", ""))
    if note:
        return note
    return safe_str(row_series.get("Notes - From Buyer", ""))


def _wrap_preserving_newlines(
    text: str,
    max_width: float,
    font: str,
    font_size: float,
    string_width: Callable[[str, str, float], float],
) -> List[str]:
    """Wrap on spaces within each hard newline; do not collapse newlines via split()."""
    if not text:
        return []
    out: List[str] = []
    for paragraph in text.split("\n"):
        if not paragraph:
            out.append("")
            continue
        words = paragraph.split(" ")
        current = ""
        for word in words:
            candidate = word if not current else f"{current} {word}"
            if string_width(candidate, font, font_size) <= max_width or not current:
                current = candidate
            else:
                out.append(current)
                current = word
        if current or not words:
            out.append(current)
    return out


def _draw_buyer_note_band(
    c,
    note: str,
    *,
    x: float,
    y: float,
    w: float,
    cell_h: float,
) -> float:
    """
    Draw bold red note at the top of the left-bottom cell.
    Returns band height in page units (0 if note empty).
    """
    note = (note or "").strip()
    if not note:
        return 0.0

    font = L.FONT_BOLD
    font_size = float(L.NOTE_FROM_BUYER_FONT_SIZE)
    pad_x = L.pt_w(L.BOX_PAD_X_PT)
    pad_y = L.pt_h(L.BOX_PAD_Y_PT)
    max_h = min(L.pt_h(L.NOTE_FROM_BUYER_MAX_H_PT), cell_h)
    text_w = max(1.0, w - 2 * pad_x)
    line_height = font_size * 1.2
    max_lines_by_h = max(1, int((max_h - 2 * pad_y) // line_height))
    max_lines = min(L.NOTE_FROM_BUYER_MAX_LINES, max_lines_by_h)

    full = f"{L.NOTE_FROM_BUYER_PREFIX}{note}"
    lines = _wrap_preserving_newlines(
        full, text_w, font, font_size, c.stringWidth
    )
    truncated = len(lines) > max_lines
    lines = lines[:max_lines]
    if truncated and lines:
        last = lines[-1].rstrip()
        ellipsis = "..."
        while last and c.stringWidth(last + ellipsis, font, font_size) > text_w:
            last = last[:-1].rstrip()
        lines[-1] = (last + ellipsis) if last else ellipsis

    if not lines:
        return 0.0

    band_h = min(max_h, 2 * pad_y + line_height * len(lines))
    band_bottom = y + cell_h - band_h

    c.setFillColorRGB(*L.WHITE)
    c.rect(x, band_bottom, w, band_h, stroke=0, fill=1)
    c.setFillColorRGB(*L.RED)
    c.setFont(font, font_size)
    # Top-down: first line near top of band
    baseline = band_bottom + band_h - pad_y - font_size
    for i, line in enumerate(lines):
        c.drawString(x + pad_x, baseline - i * line_height, line)
    return band_h


def _item_image_url_candidates(row_series, safe_str: Callable[..., str]) -> List[Tuple[str, str]]:
    item_image_url = safe_str(row_series.get("Item Image URL", ""))
    gift_image_url = _url_from_gift_message(safe_str(row_series.get("Gift Message", "")))
    candidates: List[Tuple[str, str]] = []
    if item_image_url:
        candidates.append((item_image_url, "Item Image URL"))
    if gift_image_url and gift_image_url != item_image_url:
        candidates.append((gift_image_url, "Gift Message"))
    return candidates


def draw_left_bottom_item_image_impl(
    c,
    row_series,
    *,
    is_plain_order: bool,
    content_h_pt: float,
    s2_y_pt: float,
    left_w_pt: float,
    rect_at: Callable[..., tuple],
    safe_str: Callable[..., str],
    prepare_image_from_url: Callable[..., object],
    image_reader_cls,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    pdf_page_index: int = 0,
) -> None:
    pn_h = content_h_pt - s2_y_pt
    pnx, pny, pnw, pnh = rect_at(0, s2_y_pt, left_w_pt, pn_h)
    proc = str(row_series.get("Process and Item Number", "") or "").strip()

    note = _notes_from_buyer(row_series, safe_str)
    note_band_h = _draw_buyer_note_band(
        c, note, x=pnx, y=pny, w=pnw, cell_h=pnh
    )
    img_h = max(0.0, pnh - note_band_h)
    if is_plain_order or img_h <= 0:
        return

    for image_url, source in _item_image_url_candidates(row_series, safe_str):
        prepared_item_image = prepare_image_from_url(image_url, pnw, img_h)
        if prepared_item_image is None:
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | ITEM IMAGE URL not drawn | "
                f"prepare_image_from_url returned no bytes | source={source} | url={image_url!r}",
            )
            continue
        try:
            c.drawImage(
                image_reader_cls(prepared_item_image),
                pnx,
                pny,
                width=pnw,
                height=img_h,
                preserveAspectRatio=True,
                anchor="c",
                mask="auto",
            )
        except Exception as exc:
            _pdf_asset_log_line(
                pdf_asset_log,
                f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | ITEM IMAGE URL draw FAILED | "
                f"source={source} | url={image_url!r} | error={exc!r}",
            )
            continue

        _pdf_asset_log_line(
            pdf_asset_log,
            f"PDF generation | CSV row {pdf_page_index + 1} | {proc!r} | ITEM IMAGE URL drawn on PDF | "
            f"source={source} | url={image_url!r}",
        )
        return
