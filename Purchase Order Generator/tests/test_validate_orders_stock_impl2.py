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
def _order(order_number: str, items: list[dict], name: str = "Test Customer") -> dict:
    return {
        "orderNumber": order_number,
        "shipTo": {"name": name},
        "items": items,
    }
