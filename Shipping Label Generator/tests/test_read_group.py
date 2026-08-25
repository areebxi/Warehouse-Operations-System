from __future__ import annotations

from pathlib import Path

from scripts.app.flows.print_labels.read_group import read_and_group_orders
from scripts.app.flows.print_labels.run import _extract_process_number_from_summary_page
from scripts.app.pdf.report_pages import _summary_process_font_size, make_summary_page_pdf


def test_read_group_strips_process_prefix_from_manual_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "Process Number,Order Number,Customer Name\n"
        "Process 5502,205-123-456,Alice\n"
        "5503,205-987-654,Bob\n",
        encoding="utf-8",
    )

    groups = read_and_group_orders(csv_path)
    by_process = {g.process_number: g for g in groups}

    assert by_process["5502"].order_numbers == ["205-123-456"]
    assert by_process["5503"].order_numbers == ["205-987-654"]


def test_read_group_dedupes_duplicate_rows_with_same_order(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    csv_path.write_text(
        "Process Number,Order Number,Customer Name\n"
        "50,026-9777146-507751,Sue Nicholson\n"
        "50,026-9777146-507751,Sue Nicholson\n"
        "50,026-9777146-507751,Sue Nicholson\n"
        "50,026-1111111-222222,Someone Else\n"
        "50,026-1111111-222222,Someone Else\n",
        encoding="utf-8",
    )

    groups = read_and_group_orders(csv_path)
    assert len(groups) == 1
    assert groups[0].process_number == "50"
    assert groups[0].order_numbers == ["026-9777146-507751", "026-1111111-222222"]
    assert groups[0].orders[0].customer_name == "Sue Nicholson"


def test_extract_process_number_reads_marker_with_non_digit_values() -> None:
    text = "Batch Summary\nProcess Number 5502\nPROCESS_NUMBER=5502\n"
    assert _extract_process_number_from_summary_page(text) == "5502"


def test_summary_process_font_size_scales_for_long_values() -> None:
    assert _summary_process_font_size("5502") == 144
    assert _summary_process_font_size("Process 5502") == 48
    assert _summary_process_font_size("123456789012") == 48


def test_make_summary_page_pdf_accepts_clean_process_number() -> None:
    pdf = make_summary_page_pdf(process_number="5502", label_count=1)
    assert pdf.startswith(b"%PDF")
