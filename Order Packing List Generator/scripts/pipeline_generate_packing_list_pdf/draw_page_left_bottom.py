import re
from typing import Callable, List, Optional, Tuple

from scripts.pipeline_generate_packing_list_pdf.draw_page_apparel_and_logos import (
    _pdf_asset_log_line,
)

_URL_PATTERN = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)


def _url_from_gift_message(gift_message: str) -> str:
    if not gift_message:
        return ""
    match = _URL_PATTERN.search(gift_message.strip())
    if not match:
        return ""
    return match.group(0).rstrip(".,;)")


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
    if is_plain_order:
        return

    for image_url, source in _item_image_url_candidates(row_series, safe_str):
        prepared_item_image = prepare_image_from_url(image_url, pnw, pnh)
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
                height=pnh,
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
