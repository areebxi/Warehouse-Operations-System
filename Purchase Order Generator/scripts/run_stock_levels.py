"""Load cached BTC free-stock CSV into a stock_id → quantity map."""
from __future__ import annotations

import csv

from run_ftp_settings import _stock_file_paths


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
        log(
            f"[SUCCESS] Loaded stock levels for {len(stock_levels)} items "
            f"from {stock_file_name}"
        )
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
