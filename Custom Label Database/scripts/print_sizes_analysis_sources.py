"""Dump M01 / Print Sizes / Configuration Workbook structure for print-size analysis."""
from __future__ import annotations

import pandas as pd

from print_sizes_analysis_util import CONFIG, M01, PRINT_SIZES, dump_workbook


def run_sources() -> None:
    print("=" * 70)
    print("1. M01_print_config sheets and structure")
    print("=" * 70)
    dump_workbook(M01, head=8)

    print("\n" + "=" * 70)
    print("2. Print Sizes.xlsx")
    print("=" * 70)
    dump_workbook(PRINT_SIZES, head=15)

    print("\n" + "=" * 70)
    print("3. Configuration Workbook - Size References")
    print("=" * 70)
    xl_cfg = pd.ExcelFile(CONFIG)
    print("Sheets:", xl_cfg.sheet_names)
    size_sheets = [
        s for s in xl_cfg.sheet_names if "size" in s.lower() or "reference" in s.lower()
    ]
    print("Size-related sheets:", size_sheets)
    for sheet in xl_cfg.sheet_names:
        if (
            "size" in sheet.lower()
            or "reference" in sheet.lower()
            or "print" in sheet.lower()
        ):
            df = pd.read_excel(CONFIG, sheet_name=sheet)
            print(f"\n--- {sheet} --- rows={len(df)}, cols={len(df.columns)}")
            print("Columns:", list(df.columns))
            print(df.head(12).to_string())
            if len(df) > 12:
                print(f"... ({len(df)-12} more rows)")

    print("\n" + "=" * 70)
