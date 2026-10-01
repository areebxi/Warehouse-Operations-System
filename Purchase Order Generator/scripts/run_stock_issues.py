"""Stock-issues CSV export and run-summary text."""
from __future__ import annotations

import csv
import os

from stock_resolver import STATUS_NOT_FOUND

STATUS_OUT_OF_STOCK = "Out of Stock"


def write_stock_issues_csv(filename: str, out_of_stock_items, not_found_items) -> None:
    """Write one combined CSV with specific Not Found reasons or Out of Stock."""
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Order",
                "Recipient",
                "Quantity",
                "Item SKU",
                "Complete SKU",
                "Stock ID",
                "Tag",
                "Stock Level",
                "Process No",
                "Status",
            ]
        )
        for row in not_found_items or []:
            status = STATUS_NOT_FOUND
            if len(row) >= 10 and row[9]:
                status = row[9]
                row = row[:9]
            (
                order_number,
                recipient_name,
                quantity,
                item_sku,
                complete_sku,
                stock_id,
                tag_id,
                _stock_level,
                process_no,
            ) = row
            writer.writerow(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    item_sku,
                    complete_sku,
                    stock_id,
                    tag_id,
                    "N/A",
                    process_no,
                    status,
                ]
            )
        for row in out_of_stock_items or []:
            if len(row) >= 10:
                row = row[:9]
            (
                order_number,
                recipient_name,
                quantity,
                item_sku,
                complete_sku,
                stock_id,
                tag_id,
                stock_level,
                process_no,
            ) = row
            writer.writerow(
                [
                    order_number,
                    recipient_name,
                    quantity,
                    item_sku,
                    complete_sku,
                    stock_id,
                    tag_id,
                    stock_level,
                    process_no,
                    STATUS_OUT_OF_STOCK,
                ]
            )


def _unique_complete_skus(issue_rows) -> list[str]:
    seen = set()
    ordered: list[str] = []
    for row in issue_rows or []:
        if len(row) < 5:
            continue
        sku = str(row[4] or "").strip()
        if not sku or sku in seen:
            continue
        seen.add(sku)
        ordered.append(sku)
    return ordered


def format_run_summary(
    tag_label: str,
    orders_processed: int,
    in_stock_items,
    out_of_stock_items,
    not_found_items,
    issues_filename: str | None = None,
) -> str:
    """Build the end-of-run summary text for GUI log / CLI."""
    not_found_skus = _unique_complete_skus(not_found_items)
    out_of_stock_skus = _unique_complete_skus(out_of_stock_items)
    in_count = len(in_stock_items or [])
    lines = [
        "========== RUN SUMMARY ==========",
        f"Tag: {tag_label}",
        f"Orders processed: {orders_processed}",
    ]
    if not not_found_skus and not out_of_stock_skus:
        lines.append("All orders found and in stock.")
    else:
        lines.append(f"In stock: {in_count} order line(s)")
        lines.append(f"Not found: {len(not_found_skus)} SKU(s)")
        for sku in not_found_skus:
            lines.append(f"  - {sku}")
        lines.append(f"Out of stock: {len(out_of_stock_skus)} SKU(s)")
        for sku in out_of_stock_skus:
            lines.append(f"  - {sku}")
        if issues_filename:
            lines.append(f"Stock issues file: {os.path.basename(issues_filename)}")
    lines.append("=================================")
    return "\n".join(lines)
