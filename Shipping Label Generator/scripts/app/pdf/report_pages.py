from __future__ import annotations

import io
from datetime import date
from datetime import datetime, timezone
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _truncate_text(s: str, *, max_chars: int) -> str:
    t = str(s or "")
    if max_chars <= 0:
        return ""
    if len(t) <= max_chars:
        return t
    suffix = "\n\n...(truncated)"
    if len(suffix) >= max_chars:
        return t[:max_chars]
    keep = max_chars - len(suffix)
    return t[:keep] + suffix


def _error_reason_paragraph_text(reason: str, *, max_chars: int = 1800) -> str:
    """
    ReportLab Paragraphs are XML-ish. Escape + convert newlines to <br/>.
    Also hard-truncate to avoid pathological layouts when ShipStation returns huge JSON bodies.
    """
    t = _truncate_text(reason, max_chars=max_chars)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = escape(t, {"\n": "<br/>"})
    return t.replace("\n", "<br/>")


def _plain_cell_text(s: str, *, max_chars: int) -> str:
    # Table cells use plain strings (not Paragraph). Keep them bounded too.
    return _truncate_text(s, max_chars=max_chars)


def _summary_process_font_size(process_number: str) -> int:
    """Scale the large process number so long values stay inside the summary table."""
    n = len(str(process_number).strip())
    if n <= 4:
        return 144
    if n <= 6:
        return 96
    if n <= 8:
        return 72
    if n <= 12:
        return 48
    return 36


def _create_summary_pdf(
    *,
    batch_number: str,
    process_number: str,
    batch_notes: str,
    processed_by: str,
    processed_date: str,
    ship_date: str,
    ship_from: str,
    label_count: int,
) -> bytes:
    buf = io.BytesIO()

    doc = SimpleDocTemplate(buf, pagesize=letter)

    # Table data (8 rows, 2 columns)
    data = [
        ["Batch#", str(batch_number)],
        ["Process Number", str(process_number)],
        ["Processed by", str(processed_by)],
        ["Processed Date", str(processed_date)],
        ["Ship Date", str(ship_date)],
        ["Ship From", str(ship_from)],
        ["# Labels", str(int(label_count))],
    ]

    table = Table(data, colWidths=[2 * inch, 4 * inch])
    process_font_size = _summary_process_font_size(process_number)
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                # Left column styling
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                # Right column default styling
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                # Special “big number” styling for Process Number value (row 1, col 1)
                ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (1, 1), (1, 1), process_font_size),
                ("ALIGN", (1, 1), (1, 1), "CENTER"),
            ]
        )
    )

    story = []
    # Render title using a one-cell table for consistent centering without Paragraph dependency.
    title_table = Table([["Batch Summary"]], colWidths=[6 * inch])
    title_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (0, 0), 24),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (0, 0), 30),
            ]
        )
    )
    story.append(title_table)

    # Add a small, plain-text process number line to make PDF text extraction reliable.
    # Some PDF text extractors can mis-map glyphs for the very large "Process Number" cell.
    pn_hint = Table([[f"Process Number {process_number}"]], colWidths=[6 * inch])
    pn_hint.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                ("FONTSIZE", (0, 0), (0, 0), 9),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#666666")),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (0, 0), 12),
            ]
        )
    )
    story.append(pn_hint)

    # Add a second, machine-friendly marker to make parsing even more robust.
    # This avoids relying on spacing/casing or layout artifacts.
    pn_marker = Table([[f"PROCESS_NUMBER={process_number}"]], colWidths=[6 * inch])
    pn_marker.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                ("FONTSIZE", (0, 0), (0, 0), 7),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor("#888888")),
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (0, 0), 18),
            ]
        )
    )
    story.append(pn_marker)

    story.append(Spacer(1, 0.5 * inch))
    story.append(table)

    doc.build(story)
    return buf.getvalue()


def make_summary_page_pdf(
    *,
    process_number: str,
    batch_number: str | None = None,
    batch_notes: str | None = None,
    processed_by: str | None = None,
    ship_from: str | None = None,
    label_count: int,
) -> bytes:
    # Backwards-compatible wrapper; prefer passing config-derived values.
    return _create_summary_pdf(
        batch_number=str(batch_number or "1"),
        process_number=str(process_number),
        batch_notes=str(batch_notes or ""),
        processed_by=str(processed_by or ""),
        processed_date=date.today().isoformat(),
        ship_date=date.today().isoformat(),
        ship_from=str(ship_from or ""),
        label_count=int(label_count),
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

    # Match the example layout: one compact table near the top.
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

    # Center the table block under the title.
    table.hAlign = "CENTER"
    story = [Spacer(1, 0.4 * inch), title, table]
    doc.build(story)
    return buf.getvalue()

