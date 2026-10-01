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

def _ftp_settings():
    """Resolve FTP settings from config.py with safe defaults."""
    defaults = {
        "FTP_HOST": "ftpdata.btcactivewear.co.uk",
        "FTP_USER": "daa0001",
        "FTP_PASS": "#T/Yn7pePnPC",
        "FTP_PORT": 21,
        "FTP_PROTOCOL": "ftp",
        "FTP_REMOTE_FILE": "WebData/stock_levels_stock_id_fully_quoted.csv",
        "FTP_LOCAL_FILE": "stock_levels_stock_id_fully_quoted.csv",
        "FTP_TIMEOUT_SECONDS": 30,
        "FTP_PROBE_TIMEOUT_SECONDS": 5,
        "FTP_PASSIVE_MODE": True,
        "FTP_MAX_RETRIES": 3,
    }
    try:
        import config as app_config

        for key, default in defaults.items():
            defaults[key] = getattr(app_config, key, default)
    except Exception:
        pass
    return defaults
def write_packing_list_csv(filename: str, in_stock_items) -> None:
    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Order",
                "Recipient",
                "Quantity",
                "Item SKU",
                "Pack Name",
                "Tag",
                "Stock Level",
                "Components",
                "Component Colours",
                "Process No",
                "Marketplace SKU",
            ]
        )
        writer.writerows(normalize_packing_rows(in_stock_items))
def _stock_transfer_blocked_message(host: str, port: int, protocol: str) -> str:
    _, local_path, local_name = _stock_file_paths()
    manual_hint = (
        f"or manually download {local_name} into the data/ folder "
        f"(set FTP_LOCAL_FILE in config.py)."
    )
    if protocol == "sftp":
        return (
            f"[ERROR] Cannot reach {host}:{port} (timed out). "
            f"Your network or firewall is blocking outbound SFTP (TCP port {port}). "
            f"Ask IT to allow port {port} to {host}, use a BTC-approved VPN, "
            f"{manual_hint}"
        )
    return (
        f"[ERROR] Cannot reach {host}:{port} (timed out). "
        f"Your network or firewall is blocking outbound FTP (TCP port {port}). "
        f"Ask IT to allow port {port} to {host}, use a BTC-approved VPN, "
        f"{manual_hint}"
    )
def _ftp_probe_tcp(host: str, port: int, timeout_seconds: int) -> bool:
    """Quick TCP check before full FTP attempts."""
    try:
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False
def _stock_transfer_protocol(settings: dict, ftp_port: int) -> str:
    protocol = str(settings.get("FTP_PROTOCOL", "ftp")).strip().lower()
    if protocol in ("ftp", "sftp"):
        return protocol
    if ftp_port in (22, 2022):
        return "sftp"
    return "ftp"
def pdf_filename_for_tag(tag_id: str, process_no: str | None = None) -> str:
    if process_no is None:
        process_no = get_process_no_for_tag(tag_id)
    if process_no:
        return f"{process_no}.pdf"
    return f"Tag_{tag_id}.pdf"
def _issue_item_sku(effective: str, used_fallback: bool) -> str:
    """Display Item SKU only for a real primary stock-id hit."""
    if used_fallback:
        return ""
    return effective or ""
def basic_sku(original_sku: str) -> str:
    """Marketplace prefix: part before the first dash."""
    return _pack_key(original_sku)
