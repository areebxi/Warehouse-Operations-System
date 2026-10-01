from __future__ import annotations
import app_paths  # noqa: F401 — configures import paths before other local imports
from shipstation_orders import ShipStationAPI, ShipStationError
from pdf_generator import generate_packing_slips_for_tag
import sys
import os
import csv
import json
import socket
from datetime import datetime
from ftplib import FTP, error_perm, error_temp, error_reply
from app_paths import data_path, packs_database_path, shipstation_tags_path, tag_output_dir
from stock_resolver import (
    NOT_FOUND_STATUSES,
    STATUS_NOT_FOUND,
    load_custom_label_stock_map,
    not_found_status,
    resolve_stock_level,
)

def rows_for_pdf_slips(
    in_stock_items,
    out_of_stock_items=None,
    not_found_items=None,
    packs_map=None,
    pack_names_map=None,
):
    """Packing-slip PDF rows for EDI-eligible (in-stock) orders.

    Callers should pass only in_stock_items (same set as the EDI file).
    Optional OOS / not-found args are kept for compatibility but are unused when
    empty. Pack Components are rehydrated from Packs Database when missing.
    """
    issue_rows = list(out_of_stock_items or []) + list(not_found_items or [])
    rows = normalize_packing_rows((in_stock_items or []) + issue_rows)
    if not packs_map:
        return rows

    enriched = []
    for row in rows:
        if len(row) < 11:
            enriched.append(row)
            continue
        row = list(row)
        components_val = str(row[7] or "").strip()
        if not components_val:
            pack_key = _pack_key(str(row[3] or ""))
            comps = packs_map.get(pack_key) or []
            if comps:
                row[7] = ",".join(str(c.get("sku", "") or "") for c in comps)
                row[8] = ",".join(str(c.get("colour", "") or "") for c in comps)
                if not str(row[4] or "").strip() and pack_names_map:
                    row[4] = pack_names_map.get(pack_key, "") or ""
        enriched.append(row)
    return enriched
def build_issue_row(
    order_number,
    recipient_name,
    quantity,
    original_sku,
    tag_id,
    stock_level,
    process_no,
    *,
    item_sku="",
    stock_id="",
    status="",
) -> list:
    """Internal row for stock-issue exports (9 fields, or 10 when status set).

    Item SKU is blank when the before-dash prefix was not a real stock hit
    (custom-label / after-dash path, or not found). Complete SKU is always
    the full marketplace / ShipStation SKU. Status is set for not-found rows so
    the CSV can distinguish custom-label vs stock-levels misses.
    """
    row = [
        order_number,
        recipient_name,
        quantity,
        item_sku or "",
        (original_sku or "").strip(),
        stock_id or "",
        tag_id,
        stock_level,
        process_no,
    ]
    if status:
        row.append(status)
    return row
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
def get_process_no_for_tag(tag_id: str):
    """Read Process No from ShipStation Tags.xlsx (C: Tag ID, D: Process No)."""
    try:
        try:
            import openpyxl
        except Exception:
            print("[WARNING] openpyxl not available to read ShipStation Tags.xlsx")
            return None

        xlsx_path = str(shipstation_tags_path())
        if not os.path.exists(xlsx_path):
            print(f"[WARNING] ShipStation Tags.xlsx not found at: {xlsx_path}")
            return None

        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        ws = wb.active

        search_value = str(tag_id).strip()
        for row in ws.iter_rows(min_row=1):
            tag_cell = row[2]  # Column C (0-based index 2)
            process_cell = row[3]  # Column D (0-based index 3)
            tag_val = "" if tag_cell.value is None else str(tag_cell.value).strip()
            if tag_val == search_value:
                process_val = None if process_cell.value is None else str(process_cell.value).strip()
                return process_val or None
        return None
    except Exception as e:
        print(f"[WARNING] Failed to read Process No from ShipStation Tags.xlsx: {e}")
        return None
def load_stock_levels(log=print) -> dict[str, int]:
    """Load stock levels CSV into a stock_id → quantity map."""
    remote_file, stock_path, stock_file_name = _stock_file_paths()
    stock_levels: dict[str, int] = {}
    log(
        f"[STOCK] Loading stock levels from {stock_file_name} "
        f"(local: {stock_path}, remote: {remote_file})"
    )
    try:
        with open(stock_path, "r", encoding="utf-8") as stock_file:
            stock_reader = csv.DictReader(stock_file)
            for row in stock_reader:
                stock_id = row.get("stock_id", "").strip()
                free_stock = int(row.get("free_stock", 0))
                stock_levels[stock_id] = free_stock
        log(f"[SUCCESS] Loaded stock levels for {len(stock_levels)} items from {stock_file_name}")
    except FileNotFoundError:
        log(
            f"[WARNING] {stock_file_name} not found at {stock_path}. "
            "Proceeding without stock checks. "
            "Set FTP_LOCAL_FILE in config.py or place the file in data/."
        )
    except Exception as e:
        log(
            f"[WARNING] Error reading {stock_file_name} at {stock_path}: {e}. "
            "Proceeding without stock checks."
        )
    return stock_levels
def _stock_file_paths(settings=None):
    """Remote path on BTC server, local path under data/, and local filename."""
    settings = settings or _ftp_settings()
    remote_file = settings["FTP_REMOTE_FILE"]
    local_basename = os.path.basename(settings["FTP_LOCAL_FILE"])
    local_path = settings["FTP_LOCAL_FILE"]
    if not os.path.isabs(local_path):
        local_path = str(data_path(local_basename))
    return remote_file, local_path, local_basename
