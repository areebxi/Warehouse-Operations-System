"""Shared helpers for print_sizes_analysis."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE = Path(r"d:\Custom Label Database")
UPDATED = BASE / "Custom Label Database_Updated.xlsx"
M01 = BASE / "M01_print_config_20260814_103010.xlsx"
PRINT_SIZES = BASE / "Print Sizes.xlsx"
CONFIG = BASE / "Configuration Workbook.xlsx"

PRINT_COLS = [
    "Print Position Code",
    "Print Positions",
    "Position 1 Name",
    "Position 2 Name",
    "Position 3 Name",
    "Position 4 Name",
    "Print Size 1",
    "Print Size 2",
    "Print Size 3",
    "Print Size 4",
    "Width 1 (mm)",
    "Height 1 (mm)",
    "Width 2 (mm)",
    "Height 2 (mm)",
    "Width 3 (mm)",
    "Height 3 (mm)",
    "Width 4 (mm)",
    "Height 4 (mm)",
    "Printing Type",
    "Design Type",
]


def nonempty(s) -> bool:
    if pd.isna(s):
        return False
    t = str(s).strip()
    return t != "" and t.lower() != "nan"


def fill_rate(df, col) -> tuple[float, int]:
    if col not in df.columns:
        return -1, 0
    n = df[col].apply(nonempty).sum()
    return 100 * n / len(df), n


def dump_workbook(path: Path, *, head: int = 8) -> None:
    xl = pd.ExcelFile(path)
    print("Sheets:", xl.sheet_names)
    for sheet in xl.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet)
        print(f"\n--- {sheet} --- rows={len(df)}, cols={len(df.columns)}")
        print("Columns:", list(df.columns))
        print(df.head(head).to_string())
        if len(df) > head:
            print(f"... ({len(df) - head} more rows)" if head != 8 else "...")


def load_size_ref(xl_cfg: pd.ExcelFile):
    size_ref = None
    size_ref_sheet = None
    for sheet in xl_cfg.sheet_names:
        if "size" in sheet.lower() and "reference" in sheet.lower():
            size_ref = pd.read_excel(CONFIG, sheet_name=sheet)
            size_ref_sheet = sheet
            break
    if size_ref is None:
        for sheet in xl_cfg.sheet_names:
            if "reference" in sheet.lower():
                size_ref = pd.read_excel(CONFIG, sheet_name=sheet)
                size_ref_sheet = sheet
                break
    return size_ref, size_ref_sheet
