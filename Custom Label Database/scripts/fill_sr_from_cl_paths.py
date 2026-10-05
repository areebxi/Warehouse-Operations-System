"""Paths and column constants for fill_size_references_from_cl."""
from __future__ import annotations

import re
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_APP_ROOT = _SCRIPT_DIR.parent
_WAREHOUSE_ROOT = _APP_ROOT.parent
if str(_WAREHOUSE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE_ROOT))
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from shared.paths import (  # noqa: E402
    cl_csv_path,
    custom_label_support_dir,
    mocks_database_csv_path,
    size_references_backups_dir,
    warehouse_root_from,
)

_ROOT = warehouse_root_from(_SCRIPT_DIR)
_SUPPORT = custom_label_support_dir(_ROOT)
_LEGACY_SUPPORT = _APP_ROOT / "support"

DEFAULT_DB = cl_csv_path(_ROOT)
DEFAULT_SR = _SUPPORT / "Size References.csv"
if not DEFAULT_SR.is_file():
    DEFAULT_SR = _LEGACY_SUPPORT / "Size References.csv"
DEFAULT_MOCKS = mocks_database_csv_path(_ROOT)
if not DEFAULT_MOCKS.is_file():
    DEFAULT_MOCKS = _LEGACY_SUPPORT / "Mocks Database.csv"
BACKUPS = size_references_backups_dir(_ROOT)

# Supervisor removed SKU Value 2 / SKU Value 3 (2026-09-25) — not needed.
SR_COLS = [
    "SKU Value",
    "Number of Designs",
    "Size Width",
    "Size Height",
    "Suffix",
    "Gender",
    "Size",
    "Printing Position",
    "Product Code",
    "Printing Size",
]

RE_MOCK_UID = re.compile(r"^(M\d+)-(\d+)$", re.I)
RE_SR_KEY = re.compile(r"^(M\d+)\s*\((\d+)\)\s*$", re.I)
RE_LETTER_SIZE = re.compile(r"^(?:[2-5])?XL$|^XXL$|^XS$|^S$|^M$|^L$", re.I)

BLANK_FILL_COLS = (
    "Suffix",
    "Gender",
    "Size",
    "Printing Position",
    "Product Code",
    "Printing Size",
    "Size Width",
    "Size Height",
)
