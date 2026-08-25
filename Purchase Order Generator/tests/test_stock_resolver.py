"""Unit tests for Custom Label → BTC Stock ID resolution."""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import app_paths  # noqa: F401

from stock_resolver import (  # noqa: E402
    STATUS_CUSTOM_LABEL_MISSING_STOCK_ID,
    STATUS_NOT_IN_CUSTOM_LABEL_DB,
    STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS,
    _norm_label,
    load_custom_label_stock_map,
    not_found_status,
    resolve_stock_level,
)


class TestResolveStockLevel(unittest.TestCase):
    def test_mixed_case_sku_suffix_matches_casefolded_map_key(self):
        custom_label_map = {_norm_label("TPC001-NAT-O/S-Yes"): "7299"}
        stock_levels = {"7299": 5}
        sku = "46139LG-TPC001-NAT-O/S-Yes"

        level, effective, marketplace, used_fallback = resolve_stock_level(
            sku, stock_levels, custom_label_map
        )

        self.assertEqual(level, 5)
        self.assertEqual(effective, "7299")
        self.assertEqual(marketplace, sku)
        self.assertTrue(used_fallback)

    def test_lowercase_map_key_matches_uppercase_sku_suffix(self):
        custom_label_map = {_norm_label("tpc001-nat-o/s-yes"): "7299"}
        stock_levels = {"7299": 0}
        sku = "46139LG-TPC001-NAT-O/S-YES"

        level, effective, _, used_fallback = resolve_stock_level(
            sku, stock_levels, custom_label_map
        )

        self.assertEqual(level, 0)
        self.assertEqual(effective, "7299")
        self.assertTrue(used_fallback)


class TestLoadCustomLabelStockMap(unittest.TestCase):
    def test_first_wins_for_case_only_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "labels.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["Custom Label", "BTC Stock ID"]
                )
                writer.writeheader()
                writer.writerow(
                    {"Custom Label": "TPC001-NAT-O/S-Yes", "BTC Stock ID": "1111"}
                )
                writer.writerow(
                    {"Custom Label": "tpc001-nat-o/s-yes", "BTC Stock ID": "2222"}
                )

            mapping, empty_ids = load_custom_label_stock_map(
                path=csv_path, log=lambda _msg: None
            )

        self.assertEqual(mapping, {_norm_label("TPC001-NAT-O/S-Yes"): "1111"})
        self.assertEqual(empty_ids, set())

    def test_tracks_labels_with_blank_btc_stock_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "labels.csv"
            with open(csv_path, "w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=["Custom Label", "BTC Stock ID"]
                )
                writer.writeheader()
                writer.writerow(
                    {"Custom Label": "C800T-BLK-3-6M", "BTC Stock ID": ""}
                )
                writer.writerow(
                    {"Custom Label": "TPC001-NAT-O/S-Yes", "BTC Stock ID": "7299"}
                )

            mapping, empty_ids = load_custom_label_stock_map(
                path=csv_path, log=lambda _msg: None
            )

        self.assertEqual(mapping, {_norm_label("TPC001-NAT-O/S-Yes"): "7299"})
        self.assertEqual(empty_ids, {_norm_label("C800T-BLK-3-6M")})


class TestNotFoundStatus(unittest.TestCase):
    def test_not_in_custom_label_db(self):
        status = not_found_status(
            "176505LG-C800T-RED-18-24M",
            {},
            set(),
            used_fallback=False,
        )
        self.assertEqual(status, STATUS_NOT_IN_CUSTOM_LABEL_DB)

    def test_custom_label_missing_stock_id(self):
        status = not_found_status(
            "176505LG-C800T-BLK-3-6M",
            {},
            {_norm_label("C800T-BLK-3-6M")},
            used_fallback=False,
        )
        self.assertEqual(status, STATUS_CUSTOM_LABEL_MISSING_STOCK_ID)

    def test_stock_id_not_in_stock_levels(self):
        status = not_found_status(
            "46139LG-TPC001-NAT-O/S-Yes",
            {_norm_label("TPC001-NAT-O/S-Yes"): "7299"},
            set(),
            used_fallback=True,
        )
        self.assertEqual(status, STATUS_STOCK_ID_NOT_IN_STOCK_LEVELS)


if __name__ == "__main__":
    unittest.main()
