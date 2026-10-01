"""Unit tests for stock validation, discount skipping, and issue CSV exports."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import app_paths  # noqa: F401 — configures import paths

from validate_orders_stock_discount import TestDiscountSkipping  # noqa: E402
from validate_orders_stock_fixture import TestRealTagJsonFixture  # noqa: E402
from validate_orders_stock_issues import TestIssueRowExports  # noqa: E402
from validate_orders_stock_normalize import TestNormalizePackingRows  # noqa: E402

__all__ = [
    "TestIssueRowExports",
    "TestDiscountSkipping",
    "TestNormalizePackingRows",
    "TestRealTagJsonFixture",
]


if __name__ == "__main__":
    unittest.main()
