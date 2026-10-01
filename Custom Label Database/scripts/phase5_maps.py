"""Paths, constants, and size-band maps for phase5_print_sizes (legacy one-shot)."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database_Updated.xlsx"
PE_PATH = BASE / "ProductExport.xlsx"
CONFIG = BASE / "Configuration Workbook.xlsx"
PRINT_SIZES_PATH = BASE / "Print Sizes.xlsx"
BACKUP = BASE / (
    f"Custom Label Database_Updated_prePhase5Print_"
    f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
)
OUT = SRC
LOG = BASE / "docs" / "PHASE_5_CHANGELOG.md"

POCKET_WH = (80, 100)
MAX_SLOTS = 4

RE_MOCK = re.compile(r"\(M(\d+)\)", re.I)
RE_UID = re.compile(r"-(\d+)$")
RE_CRLF = re.compile(r"[\r\n]+")

AGE_TO_PRINT = {
    "1-2 Years": "1-2Y",
    "1-2Y": "1-2Y",
    "2-3 Years": "2-3Y",
    "2-3Y": "2-3Y",
    "3-4 Years": "3-4Y/YXS",
    "3-4Y": "3-4Y/YXS",
    "3-4Y/YXS": "3-4Y/YXS",
    "YXS": "3-4Y/YXS",
    "5-6 Years": "5-6Y/YS",
    "5-6Y": "5-6Y/YS",
    "5-6Y/YS": "5-6Y/YS",
    "YS": "5-6Y/YS",
    "7-8 Years": "7-8Y/YM",
    "7-8Y": "7-8Y/YM",
    "7-8Y/YM": "7-8Y/YM",
    "YM": "7-8Y/YM",
    "9-11 Years": "9-11Y/YL",
    "9-11Y": "9-11Y/YL",
    "9-11Y/YL": "9-11Y/YL",
    "YL": "9-11Y/YL",
    "12-13 Years": "12-13Y/YXL",
    "12-13Y": "12-13Y/YXL",
    "12-13Y/YXL": "12-13Y/YXL",
    "YXL": "12-13Y/YXL",
}

AGE_TO_SR = {
    "1-2 Years": "1-2Y",
    "1-2Y": "1-2Y",
    "2-3 Years": "2-3Y",
    "2-3Y": "2-3Y",
    "3-4 Years": "3-4Y",
    "3-4Y": "3-4Y",
    "5-6 Years": "5-6Y",
    "5-6Y": "5-6Y",
    "7-8 Years": "7-8Y",
    "7-8Y": "7-8Y",
    "9-11 Years": "9-11Y",
    "9-11Y": "9-11Y",
    "12-13 Years": "12-13Y",
    "12-13Y": "12-13Y",
    "12-14 Years": "14-15Y",
    "14-15 Years": "14-15Y",
    "14-15Y": "14-15Y",
}

LETTER_TO_SR = {
    "Extra Small": "XS",
    "XS": "XS",
    "Small": "Small",
    "S": "Small",
    "Medium": "Medium",
    "M": "Medium",
    "Large": "Large",
    "L": "Large",
    "Extra Large": "XL",
    "XL": "XL",
    "2XL": "2XL",
    "XXL": "2XL",
    "3XL": "3XL",
    "4XL": "4XL",
    "5XL": "5XL",
}

LETTER_TO_MEN_PRINT = {
    "Extra Small": "Men Small",
    "XS": "Men Small",
    "Small": "Men Small",
    "S": "Men Small",
    "Medium": "Men Medium",
    "M": "Men Medium",
    "Large": "Men Large",
    "L": "Men Large",
    "Extra Large": "Men XL",
    "XL": "Men XL",
    "2XL": "Men 2XL",
    "XXL": "Men 2XL",
    "3XL": "Men 3XL",
    "4XL": "Men 4XL",
    "5XL": "Men 5XL",
}

PE_AGE = {
    "1-2": "1-2Y",
    "2-3": "2-3Y",
    "3-4": "3-4Y",
    "5-6": "5-6Y",
    "7-8": "7-8Y",
    "9-11": "9-11Y",
    "12-13": "12-13Y",
    "14-15": "14-15Y",
}

SUFFIX_TO_NAME = {
    "P": "Front Left Pocket",
    "F": "Front Center",
    "B": "Back Center",
    "S": "Sleeve",
    "S-1": "Sleeve",
}

KNOWN_HUMAN = {
    "front center",
    "back center",
    "front left pocket",
    "front right pocket",
    "front bottom left corner",
    "front bottom right corner",
    "right sleeve",
    "sleeve",
    "inside",
}
