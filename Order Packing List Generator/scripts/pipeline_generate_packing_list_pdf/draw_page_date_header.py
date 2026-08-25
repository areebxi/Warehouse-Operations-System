from __future__ import annotations

from datetime import datetime

from reportlab.pdfgen import canvas

from scripts.pipeline_generate_packing_list_pdf import pdf_page_layout as L


def format_dispatch_date_header(date_dd_mm_yyyy: str) -> tuple[str, str]:
    normalized = date_dd_mm_yyyy.replace("/", "-").strip()
    dispatch_date = datetime.strptime(normalized, "%d-%m-%Y").date()
    return dispatch_date.strftime("%d-%m-%Y"), dispatch_date.strftime("%A")


def draw_page_date_header_impl(c: canvas.Canvas, date_label: str, day_name: str) -> None:
    c.setFont(L.FONT_NAME, L.DATE_HEADER_FONT_SIZE)
    c.setFillColorRGB(*L.BLACK)
    text = f"{date_label}  {day_name}"
    y = L.PAGE_HEIGHT - L.DATE_HEADER_TOP_OFFSET
    c.drawString(L.MARGIN_LR, y, text)
