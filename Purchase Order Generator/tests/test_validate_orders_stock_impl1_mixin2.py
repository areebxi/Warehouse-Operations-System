from __future__ import annotations
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
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

class TestIssueRowExportsMixin2:
    def test_not_found_custom_label_missing_stock_id(self):
        complete = "176505LG-C800T-BLK-3-6M"
        orders = [_order("4117710140", [{"sku": complete, "quantity": 1, "name": "Item"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "30886",
            "3100",
            {},
            {},
            {},
            {},
            log=lambda _msg: None,
            labels_missing_stock_id={"c800t-blk-3-6m"},
        )
        self.assertEqual(out_of_stock, [])
        self.assertEqual(len(not_found), 1)
        self.assertEqual(not_found[0][9], STATUS_CUSTOM_LABEL_MISSING_STOCK_ID)

    def test_format_run_summary_all_clear(self):
        text = format_run_summary(
            tag_label="007",
            orders_processed=10,
            in_stock_items=[[1]] * 10,
            out_of_stock_items=[],
            not_found_items=[],
        )
        self.assertIn("All orders found and in stock.", text)

