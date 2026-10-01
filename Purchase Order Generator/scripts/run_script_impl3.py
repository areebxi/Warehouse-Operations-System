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

def write_edi_orders_csv(filename: str, in_stock_items, process_no) -> None:
    current_dt = datetime.now()
    date_part = current_dt.strftime("%d-%m-%Y")
    order_id_suffix = f"{date_part}-EDI-DaataaDirect"
    order_id_value = f"{process_no}-{order_id_suffix}" if process_no else order_id_suffix

    # Plain UTF-8 (no BOM): BTC's importer treats BOM as part of the first header
    # name ("\ufeffstock-id"), so stock-id is not recognized.
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "stock-id",
                "order-id",
                "quantity-purchased",
                "product-name",
                "recipient-name",
                "sku",
                "ship-address-1",
                "ship-address-2",
                "ship-address-3",
                "ship-city",
                "ship-state",
                "ship-postal-code",
                "ship-country",
                "collection",
                "plain-cover",
                "delivery-tracking-email",
                "delivery-tracking-sms",
                "line-note",
            ]
        )

        for item in in_stock_items:
            if len(item) == 8:
                _order_number, _recipient, quantity, sku, _tag, _level, pno, _marketplace = item
                component_list = []
            elif len(item) >= 10:
                (
                    _order_number,
                    _recipient,
                    quantity,
                    sku,
                    _pack_name,
                    _tag,
                    _level,
                    components_joined,
                    _colours,
                    pno,
                    *_rest,
                ) = item
                component_list = [c for c in (components_joined or "").split(",") if c]
            else:
                _order_number, _recipient, quantity, sku, _tag, _level, pno = item[:7]
                component_list = []

            target_skus = component_list if component_list else [sku]
            for target_sku in target_skus:
                if not target_sku:
                    continue
                writer.writerow(
                    [
                        target_sku,
                        order_id_value,
                        quantity,
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "",
                        "GB",
                        "1",
                        "",
                        "",
                        "",
                        "",
                    ]
                )
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
def is_discount_line_item(item) -> bool:
    """True for Etsy/marketplace discount adjustment lines (no stock check)."""
    return (item.get("name") or "").strip().casefold() == "discount"
