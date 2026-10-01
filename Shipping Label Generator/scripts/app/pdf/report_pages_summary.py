"""Batch summary report PDF page."""

from __future__ import annotations

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle

from app.pdf.report_pages_text import _summary_process_font_size


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
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 12),
                ("FONTNAME", (1, 1), (1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (1, 1), (1, 1), process_font_size),
                ("ALIGN", (1, 1), (1, 1), "CENTER"),
            ]
        )
    )

    story = []
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
