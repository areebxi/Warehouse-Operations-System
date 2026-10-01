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

class TestRealTagJsonFixture(unittest.TestCase):
    """Regression against saved 2026-06-29 tag output."""

    @classmethod
    def setUpClass(cls):
        json_path = (
            ROOT
            / "output"
            / "2026-06-29"
            / "Tag_013-P-04-Odd_Items-7000_Orders_20260629_072238"
            / "tag_013-P-04-Odd_Items-7000_awaiting_orders_20260629_072238.json"
        )
        if not json_path.exists():
            cls.orders = None
            return
        with open(json_path, encoding="utf-8") as handle:
            cls.orders = json.load(handle)

        from stock_resolver import load_custom_label_stock_map  # noqa: E402
        import sys
        from pathlib import Path

        _wh = Path(__file__).resolve().parents[2]
        if str(_wh) not in sys.path:
            sys.path.insert(0, str(_wh))
        from shared import paths as wh  # noqa: E402

        cls.stock_levels = {}
        stock_path = wh.po_stock_csv_path()
        if stock_path.exists():
            with open(stock_path, encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    cls.stock_levels[row["stock_id"].strip()] = int(row["free_stock"])
        cls.custom_label_map, cls.labels_missing_stock_id = load_custom_label_stock_map(
            log=lambda _msg: None
        )

    def test_no_discount_or_blank_complete_sku_in_issue_exports(self):
        if self.orders is None:
            self.skipTest("Saved tag JSON fixture not available")
        _, out_of_stock, not_found = validate_orders_stock(
            self.orders,
            "30890",
            "013",
            self.stock_levels,
            {},
            {},
            self.custom_label_map,
            log=lambda _msg: None,
            labels_missing_stock_id=self.labels_missing_stock_id,
        )
        discount_lines = sum(
            1
            for order in self.orders
            for item in (order.get("items") or [])
            if is_discount_line_item(item)
        )
        self.assertGreaterEqual(discount_lines, 10)
        # Same not-found line must not also appear under out-of-stock
        not_found_keys = {(r[0], r[4]) for r in not_found}
        oos_keys = {(r[0], r[4]) for r in out_of_stock}
        self.assertTrue(not_found_keys.isdisjoint(oos_keys))
        for row in not_found + out_of_stock:
            self.assertNotEqual(row[4], "")  # Complete SKU always present
        self.assertLess(len(not_found), 36)

    def test_sample_order_resolved_via_custom_label(self):
        if self.orders is None:
            self.skipTest("Saved tag JSON fixture not available")
        in_stock, _, not_found = validate_orders_stock(
            self.orders,
            "30890",
            "013",
            self.stock_levels,
            {},
            {},
            self.custom_label_map,
            log=lambda _msg: None,
            labels_missing_stock_id=self.labels_missing_stock_id,
        )
        sample_nf = [r for r in not_found if r[0] == "4102711607"]
        self.assertEqual(sample_nf, [])
        sample = [r for r in in_stock if r[0] == "4102711607"]
        self.assertEqual(len(sample), 1)
        self.assertEqual(sample[0][7], "46139LG-TPC001-NAT-O/S-Yes")
