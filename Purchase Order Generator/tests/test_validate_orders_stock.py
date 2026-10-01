"""Unit tests for stock validation, discount skipping, and issue CSV exports."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import app_paths  # noqa: F401 — configures import paths

from test_validate_orders_stock_impl1 import TestIssueRowExports  # noqa: E402
from test_validate_orders_stock_impl2 import (  # noqa: E402
    TestDiscountSkipping,
    TestNormalizePackingRows,
)
from test_validate_orders_stock_impl3 import TestRealTagJsonFixture  # noqa: E402

__all__ = [
    "TestIssueRowExports",
    "TestDiscountSkipping",
    "TestNormalizePackingRows",
    "TestRealTagJsonFixture",
]


if __name__ == "__main__":
    unittest.main()
