"""Tests for ShipStation detailed CSV export (one row per line item)."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import app_paths  # noqa: F401 — configures import paths

from shipstation_orders import ShipStationAPI, item_fields_for_csv  # noqa: E402


class TestItemFieldsForCsv(unittest.TestCase):
    def test_empty_item(self):
        fields = item_fields_for_csv(None)
        self.assertEqual(fields["items 0 sku"], "")
        self.assertEqual(fields["basic sku"], "")

    def test_sku_and_options(self):
        fields = item_fields_for_csv(
            {
                "sku": "200661",
                "quantity": 1,
                "name": "Tee",
                "options": [{"name": "Colour", "value": "Blue"}],
            }
        )
        self.assertEqual(fields["items 0 sku"], "200661")
        self.assertEqual(fields["basic sku"], "200661")
        self.assertEqual(fields["items 0 quantity"], 1)
        self.assertEqual(fields["item 0 option 0 name"], "Colour")
        self.assertEqual(fields["item 0 option 0 value"], "Blue")
        self.assertEqual(fields["item 0 option 1 name"], "")


class TestExportOneRowPerItem(unittest.TestCase):
    def test_multi_sku_order_writes_one_row_per_item(self):
        order = {
            "orderNumber": "193757",
            "orderId": 452273860,
            "amountPaid": 34.63,
            "shipTo": {"name": "Arian Powderhill"},
            "items": [
                {"sku": "200661", "quantity": 1, "name": "FOTL Tee"},
                {"sku": "193876", "quantity": 10, "name": "Cotton Shopper"},
                {"sku": "126056", "quantity": 5, "name": "Canvas Case"},
                {"sku": "CR1500-30-S", "quantity": 5, "name": "Ringspun Tee"},
            ],
        }
        api = object.__new__(ShipStationAPI)
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "tag_detailed.csv")
            api.export_orders_to_csv([order], path)
            with open(path, encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 4)
        self.assertEqual([row["items 0 sku"] for row in rows], [
            "200661",
            "193876",
            "126056",
            "CR1500-30-S",
        ])
        self.assertEqual({row["orderNumber"] for row in rows}, {"193757"})
        self.assertEqual(rows[1]["items 0 quantity"], "10")
        self.assertEqual(rows[1]["basic sku"], "193876")

    def test_order_with_no_items_writes_one_row(self):
        order = {"orderNumber": "1", "items": []}
        api = object.__new__(ShipStationAPI)
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "empty.csv")
            api.export_orders_to_csv([order], path)
            with open(path, encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["orderNumber"], "1")
        self.assertEqual(rows[0]["items 0 sku"], "")


if __name__ == "__main__":
    unittest.main()
