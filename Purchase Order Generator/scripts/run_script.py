"""
Simple script to run the ShipStation orders fetcher.

ShipStation credentials: config/ShipStation/.env (REAL_API_*).
BTC FTP settings remain in this app's config.py.
"""

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
from run_stock_validate import validate_orders_stock
from run_script_impl2 import download_ftp_file, normalize_packing_rows, _pack_key
from run_script_impl3 import write_edi_orders_csv, write_stock_issues_csv, _unique_complete_skus, is_discount_line_item
from run_script_impl4 import load_packs_database, _download_sftp_file, load_pack_names, _log_cached_stock_file
from run_script_impl5 import rows_for_pdf_slips, build_issue_row, format_run_summary, get_process_no_for_tag, load_stock_levels, _stock_file_paths
from run_script_impl6 import _ftp_settings, write_packing_list_csv, _stock_transfer_blocked_message, _ftp_probe_tcp, _stock_transfer_protocol, pdf_filename_for_tag, _issue_item_sku, basic_sku


# --- FTP Configuration ---

STATUS_OUT_OF_STOCK = "Out of Stock"

from run_script_main import main

if __name__ == "__main__":
    main()

