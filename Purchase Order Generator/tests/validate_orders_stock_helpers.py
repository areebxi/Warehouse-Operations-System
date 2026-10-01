"""Unit tests for stock validation, discount skipping, and issue CSV exports."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import app_paths  # noqa: F401 — configures import paths

from run_script import (  # noqa: E402
    STATUS_OUT_OF_STOCK,
    format_run_summary,
    is_discount_line_item,
    normalize_packing_rows,
    validate_orders_stock,
    write_stock_issues_csv,
)
from stock_resolver import (  # noqa: E402
    STATUS_CUSTOM_LABEL_MISSING_STOCK_ID,
    STATUS_NOT_IN_CUSTOM_LABEL_DB,
    STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS,
)


def _order(order_number: str, items: list[dict], name: str = "Test Customer") -> dict:
    return {
        "orderNumber": order_number,
        "shipTo": {"name": name},
        "items": items,
    }

__all__ = [
    "ROOT",
    "STATUS_OUT_OF_STOCK",
    "STATUS_CUSTOM_LABEL_MISSING_STOCK_ID",
    "STATUS_NOT_IN_CUSTOM_LABEL_DB",
    "STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS",
    "csv",
    "json",
    "tempfile",
    "unittest",
    "Path",
    "format_run_summary",
    "is_discount_line_item",
    "normalize_packing_rows",
    "validate_orders_stock",
    "write_stock_issues_csv",
    "_order",
]
