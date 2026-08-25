from __future__ import annotations

import io

from PyPDF2 import PdfReader

from scripts.app.pdf.report_pages import make_label_error_page_pdf


def test_make_label_error_page_pdf_handles_huge_error_reason() -> None:
    huge = (
        '{"status":500,"body":"'
        + ("x" * 250_000)
        + '","note":"also <tag> & stuff \\u2028"}'
        + ("\nline " * 5000)
    )

    pdf_bytes = make_label_error_page_pdf(
        process_number="12",
        order_number="ORDER-123",
        customer_name="Test Customer",
        error_reason=huge,
    )

    assert pdf_bytes.startswith(b"%PDF")

    r = PdfReader(io.BytesIO(pdf_bytes))
    assert len(r.pages) >= 1
