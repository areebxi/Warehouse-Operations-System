"""Missed-order and label-error report PDF pages."""

from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.pdf.report_pages_text import (
    _error_reason_paragraph_text,
    _plain_cell_text,
)


def make_missed_orders_page_pdf(*, process_number: str, missed: list[tuple[str, str]]) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 720, f"Missed Orders (Process {process_number})")

    c.setFont("Helvetica", 11)
    y = 690
    for order_number, reason in missed[:60]:
        c.drawString(72, y, f"{order_number} — {reason}")
        y -= 14
        if y < 72:
            c.showPage()
            y = 720

    c.showPage()
    c.save()
    return buf.getvalue()


def make_combined_missed_orders_page_pdf(*, missed: list[tuple[str, str, str]]) -> bytes:
    """
    Create a single missed-orders page (or pages) for the combined PDF.

    Input tuples are: (process_number, order_number, reason)
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 720, "Missed Orders (All Processes)")

    c.setFont("Helvetica", 11)
    y = 690
    for process_number, order_number, reason in missed[:200]:
        c.drawString(72, y, f"Process {process_number} | {order_number} — {reason}")
        y -= 14
        if y < 72:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = 720

    c.showPage()
    c.save()
    return buf.getvalue()


def make_label_error_page_pdf(
    *,
    process_number: str,
    order_number: str,
    customer_name: str,
    error_reason: str,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MissedOrderTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=colors.HexColor("#cc0000"),
        alignment=1,  # center
        spaceAfter=18,
    )
    title = Paragraph("Missed Order Details", title_style)

    error_style = ParagraphStyle(
        "LabelErrorReason",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        alignment=0,
        # Helps break huge JSON-ish blobs that don't contain many whitespace breaks.
        wordWrap="CJK",
    )

    header = ["Customer Name", "Process #", "Order Number", "Error"]
    body = [
        _plain_cell_text(customer_name, max_chars=200),
        _plain_cell_text(process_number, max_chars=40),
        _plain_cell_text(order_number, max_chars=80),
        Paragraph(_error_reason_paragraph_text(error_reason), error_style),
    ]

    table = Table([header, body], colWidths=[1.6 * inch, 0.8 * inch, 1.6 * inch, 2.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cc0000")),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, 1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    table.hAlign = "CENTER"
    story = [Spacer(1, 0.4 * inch), title, table]
    doc.build(story)
    return buf.getvalue()
