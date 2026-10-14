from __future__ import annotations

import io

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

# 4x6, same size as a live label page. Not a carrier label.
_PAGE = (6 * inch, 4 * inch)


def sample_label_pdf_bytes(*, process_number: str, order_number: str, customer_name: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=_PAGE)
    w, h = _PAGE
    c.setStrokeColorRGB(0.7, 0.1, 0.1)
    c.setLineWidth(3)
    c.rect(8, 8, w - 16, h - 16)
    c.setFillColorRGB(0.7, 0.1, 0.1)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(w / 2, h - 40, "SAMPLE")
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, h - 58, "NOT A SHIPPING LABEL")
    c.setFont("Helvetica", 12)
    y = h - 90
    for label, value in (
        ("Process", process_number),
        ("Order", order_number),
        ("Customer", customer_name or "-"),
    ):
        c.drawString(24, y, f"{label}: {str(value)[:48]}")
        y -= 20
    c.showPage()
    c.save()
    return buf.getvalue()
