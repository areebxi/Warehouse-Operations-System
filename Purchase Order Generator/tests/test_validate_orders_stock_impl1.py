"""TestIssueRowExports shell — methods live in mixin modules."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import app_paths  # noqa: F401 — configures import paths

from test_validate_orders_stock_impl1_mixin1 import TestIssueRowExportsMixin1
from test_validate_orders_stock_impl1_mixin2 import TestIssueRowExportsMixin2


class TestIssueRowExports(TestIssueRowExportsMixin1, TestIssueRowExportsMixin2, unittest.TestCase):
    pass
