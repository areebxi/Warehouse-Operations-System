"""
Simple script to run the ShipStation orders fetcher.

ShipStation credentials: config/ShipStation/.env (REAL_API_*).
BTC FTP settings remain in this app's config.py.
"""

import app_paths  # noqa: F401 — configures import paths before other local imports

from stock_resolver import (
    NOT_FOUND_STATUSES,
    STATUS_NOT_FOUND,
    load_custom_label_stock_map,
    not_found_status,
    resolve_stock_level,
)
from run_stock_validate import validate_orders_stock
from run_ftp_download import download_ftp_file, _download_sftp_file, _log_cached_stock_file
from run_ftp_settings import (
    _ftp_settings,
    _stock_file_paths,
    _ftp_probe_tcp,
    _stock_transfer_protocol,
    _stock_transfer_blocked_message,
)
from run_packing_rows import normalize_packing_rows, rows_for_pdf_slips, write_packing_list_csv
from run_packs import load_packs_database, load_pack_names, _pack_key, basic_sku
from run_edi import write_edi_orders_csv
from run_stock_issues import write_stock_issues_csv, _unique_complete_skus, format_run_summary
from run_stock_issue_rows import is_discount_line_item, build_issue_row, _issue_item_sku
from run_stock_levels import load_stock_levels
from run_tags import get_process_no_for_tag, pdf_filename_for_tag

STATUS_OUT_OF_STOCK = "Out of Stock"

from run_script_main import main

if __name__ == "__main__":
    main()
