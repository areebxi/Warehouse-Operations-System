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


class TestDiscountSkipping(unittest.TestCase):
    def test_is_discount_line_item(self):
        self.assertTrue(is_discount_line_item({"name": "Discount", "sku": ""}))
        self.assertTrue(is_discount_line_item({"name": " discount ", "sku": ""}))
        self.assertTrue(is_discount_line_item({"name": "Seller discount", "sku": "", "adjustment": True}))
        self.assertTrue(is_discount_line_item({"name": "Platform discount", "sku": ""}))
        self.assertTrue(is_discount_line_item({"name": "Fee", "sku": "", "adjustment": True}))
        self.assertFalse(is_discount_line_item({"name": "Product", "sku": "ABC-123"}))
        self.assertFalse(is_discount_line_item({"name": "Product", "sku": "ABC-123", "adjustment": False}))

    def test_discount_line_skipped(self):
        orders = [
            _order(
                "1001",
                [
                    {"sku": "KNOWN-SUFFIX", "quantity": 1, "name": "Tote"},
                    {"sku": "", "quantity": 1, "name": "Discount"},
                ],
            )
        ]
        stock_levels = {"KNOWN": 5}
        in_stock, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            stock_levels,
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(len(in_stock), 1)
        self.assertEqual(out_of_stock, [])
        self.assertEqual(not_found, [])

    def test_tiktok_seller_platform_discount_skipped(self):
        """Regression: Tag_007 Plain-2100 TikTok lines must not fail the order."""
        orders = [
            _order(
                "576934506417003497",
                [
                    {"sku": "137941", "quantity": 1, "name": "Tee", "adjustment": False},
                    {"sku": "120860", "quantity": 1, "name": "Tee", "adjustment": False},
                    {"sku": "", "quantity": 1, "name": "Seller discount", "adjustment": True},
                    {"sku": "", "quantity": 1, "name": "Platform discount", "adjustment": True},
                ],
                name="Sukhwinder Singh",
            )
        ]
        stock_levels = {"137941": 726, "120860": 255}
        in_stock, out_of_stock, not_found = validate_orders_stock(
            orders,
            "34627",
            "2100",
            stock_levels,
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(not_found, [])
        self.assertEqual(out_of_stock, [])
        self.assertEqual(len(in_stock), 2)
        self.assertEqual({r[3] for r in in_stock}, {"137941", "120860"})

    def test_multi_sku_order_one_packing_row_per_item(self):
        orders = [
            _order(
                "193757",
                [
                    {"sku": "200661", "quantity": 1, "name": "Tee"},
                    {"sku": "126056", "quantity": 5, "name": "Case"},
                    {"sku": "44129", "quantity": 2, "name": "Hoodie"},
                    {"sku": "44130", "quantity": 1, "name": "Joggers"},
                ],
            )
        ]
        stock_levels = {"200661": 18, "126056": 161, "44129": 4, "44130": 15}
        in_stock, out_of_stock, not_found = validate_orders_stock(
            orders,
            "34627",
            "2100",
            stock_levels,
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(out_of_stock, [])
        self.assertEqual(not_found, [])
        self.assertEqual(len(in_stock), 4)
        self.assertEqual([r[3] for r in in_stock], ["200661", "126056", "44129", "44130"])

    def test_discount_only_order_has_no_items(self):
        orders = [_order("1002", [{"sku": "", "quantity": 1, "name": "Discount"}])]
        in_stock, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            {},
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(len(in_stock), 1)
        self.assertEqual(in_stock[0][0], "1002")
        self.assertEqual(in_stock[0][3], "")
        self.assertEqual(out_of_stock, [])
        self.assertEqual(not_found, [])


class TestIssueRowExports(unittest.TestCase):
    def test_not_found_blank_item_sku_and_not_in_oos(self):
        complete = "46139LG-TPC001-NAT-O/S-Yes"
        orders = [_order("4102711607", [{"sku": complete, "quantity": 1, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "30890",
            "013",
            {},
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(len(not_found), 1)
        row = not_found[0]
        self.assertEqual(row[3], "")  # Item SKU blank — prefix is not a real stock id
        self.assertEqual(row[4], complete)
        self.assertEqual(row[5], "")
        self.assertEqual(row[7], -1)
        self.assertEqual(row[9], STATUS_NOT_IN_CUSTOM_LABEL_DB)
        self.assertEqual(out_of_stock, [])

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

    def test_not_found_stock_id_not_in_stock_levels(self):
        complete = "46139LG-TPC001-NAT-O/S-Yes"
        custom_label_map = {"tpc001-nat-o/s-yes": "7299"}
        orders = [_order("1005", [{"sku": complete, "quantity": 1, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            {},
            {},
            {},
            custom_label_map,
            log=lambda _msg: None,
        )
        self.assertEqual(out_of_stock, [])
        self.assertEqual(len(not_found), 1)
        row = not_found[0]
        self.assertEqual(row[5], "7299")
        self.assertEqual(row[9], STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS)

    def test_out_of_stock_blank_item_sku_when_fallback(self):
        complete = "46139LG-TPC001-NAT-O/S-Yes"
        custom_label_map = {"tpc001-nat-o/s-yes": "7299"}
        stock_levels = {"7299": 0}
        orders = [_order("1003", [{"sku": complete, "quantity": 1, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            stock_levels,
            {},
            {},
            custom_label_map,
            log=lambda _msg: None,
        )
        self.assertEqual(not_found, [])
        self.assertEqual(len(out_of_stock), 1)
        row = out_of_stock[0]
        self.assertEqual(row[3], "")  # fallback — do not show fake prefix as Item SKU
        self.assertEqual(row[4], complete)
        self.assertEqual(row[5], "7299")
        self.assertEqual(row[7], 0)

    def test_out_of_stock_primary_keeps_item_sku(self):
        complete = "KNOWN-SUFFIX"
        stock_levels = {"KNOWN": 0}
        orders = [_order("1004", [{"sku": complete, "quantity": 2, "name": "Tote"}])]
        _, out_of_stock, not_found = validate_orders_stock(
            orders,
            "tag1",
            "P01",
            stock_levels,
            {},
            {},
            {},
            log=lambda _msg: None,
        )
        self.assertEqual(not_found, [])
        self.assertEqual(len(out_of_stock), 1)
        row = out_of_stock[0]
        self.assertEqual(row[3], "KNOWN")
        self.assertEqual(row[4], complete)
        self.assertEqual(row[5], "KNOWN")

    def test_write_stock_issues_csv_headers_and_status(self):
        not_found_row = [
            "1001",
            "Alice",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "",
            "30890",
            -1,
            "013",
            STATUS_NOT_IN_CUSTOM_LABEL_DB,
        ]
        oos_row = [
            "1002",
            "Bob",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "7299",
            "30890",
            0,
            "013",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            issues_path = Path(tmp) / "stock_issues.csv"
            write_stock_issues_csv(str(issues_path), [oos_row], [not_found_row])

            with open(issues_path, encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))

        self.assertEqual(
            rows[0],
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
            ],
        )
        self.assertEqual(rows[1][9], STATUS_NOT_IN_CUSTOM_LABEL_DB)
        self.assertEqual(rows[1][3], "")
        self.assertEqual(rows[1][4], "46139LG-TPC001-NAT-O/S-Yes")
        self.assertEqual(rows[1][7], "N/A")
        self.assertEqual(rows[2][9], STATUS_OUT_OF_STOCK)
        self.assertEqual(rows[2][5], "7299")

    def test_format_run_summary_lists_marketplace_skus(self):
        not_found = [
            ["1", "A", 1, "", "SKU-A-FULL", "", "t", -1, "01"],
            ["2", "B", 1, "", "SKU-A-FULL", "", "t", -1, "01"],
        ]
        oos = [["3", "C", 1, "", "SKU-B-FULL", "99", "t", 0, "01"]]
        text = format_run_summary(
            tag_label="013-P-04-Odd Items-7000",
            orders_processed=48,
            in_stock_items=[[] for _ in range(45)],
            out_of_stock_items=oos,
            not_found_items=not_found,
            issues_filename="stock_issues_tag_x_20260716_130000.csv",
        )
        self.assertIn("Not found: 1 SKU(s)", text)
        self.assertIn("  - SKU-A-FULL", text)
        self.assertIn("Out of stock: 1 SKU(s)", text)
        self.assertIn("  - SKU-B-FULL", text)
        self.assertIn("stock_issues_tag_x_20260716_130000.csv", text)

    def test_format_run_summary_all_clear(self):
        text = format_run_summary(
            tag_label="007",
            orders_processed=10,
            in_stock_items=[[1]] * 10,
            out_of_stock_items=[],
            not_found_items=[],
        )
        self.assertIn("All orders found and in stock.", text)


class TestNormalizePackingRows(unittest.TestCase):
    def test_len_9_issue_row_maps_to_packing_format(self):
        issue_row = [
            "1001",
            "Alice",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "7299",
            "30890",
            0,
            "013",
        ]
        normalized = normalize_packing_rows([issue_row])
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0][3], "7299")
        self.assertEqual(normalized[0][10], "46139LG-TPC001-NAT-O/S-Yes")

    def test_len_9_without_stock_id_blank_item_sku(self):
        issue_row = [
            "1001",
            "Alice",
            1,
            "",
            "46139LG-TPC001-NAT-O/S-Yes",
            "",
            "30890",
            -1,
            "013",
        ]
        normalized = normalize_packing_rows([issue_row])
        self.assertEqual(normalized[0][3], "")
        self.assertEqual(normalized[0][10], "46139LG-TPC001-NAT-O/S-Yes")


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

        cls.stock_levels = {}
        stock_path = ROOT / "data" / "stock_levels_stock_id_fully_quoted.csv"
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


if __name__ == "__main__":
    unittest.main()
