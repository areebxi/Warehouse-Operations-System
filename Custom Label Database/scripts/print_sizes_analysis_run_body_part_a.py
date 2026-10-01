from __future__ import annotations

def _run_part_a():
    BASE = Path(r"d:\Custom Label Database")
    UPDATED = BASE / "Custom Label Database_Updated.xlsx"
    M01 = BASE / "M01_print_config_20260814_103010.xlsx"
    PRINT_SIZES = BASE / "Print Sizes.xlsx"
    CONFIG = BASE / "Configuration Workbook.xlsx"

    PRINT_COLS = [
        "Print Position Code", "Print Positions",
        "Position 1 Name", "Position 2 Name", "Position 3 Name", "Position 4 Name",
        "Print Size 1", "Print Size 2", "Print Size 3", "Print Size 4",
        "Width 1 (mm)", "Height 1 (mm)", "Width 2 (mm)", "Height 2 (mm)",
        "Width 3 (mm)", "Height 3 (mm)", "Width 4 (mm)", "Height 4 (mm)",
        "Printing Type", "Design Type",
    ]

    def nonempty(s):
        if pd.isna(s):
            return False
        t = str(s).strip()
        return t != "" and t.lower() != "nan"

    def fill_rate(df, col):
        if col not in df.columns:
            return -1, 0
        n = df[col].apply(nonempty).sum()
        return 100 * n / len(df), n

    print("=" * 70)
    print("1. M01_print_config sheets and structure")
    print("=" * 70)
    xl_m01 = pd.ExcelFile(M01)
    print("Sheets:", xl_m01.sheet_names)
    for sheet in xl_m01.sheet_names:
        df = pd.read_excel(M01, sheet_name=sheet)
        print(f"\n--- {sheet} --- rows={len(df)}, cols={len(df.columns)}")
        print("Columns:", list(df.columns))
        print(df.head(8).to_string())
        if len(df) > 8:
            print("...")

    print("\n" + "=" * 70)
    print("2. Print Sizes.xlsx")
    print("=" * 70)
    xl_ps = pd.ExcelFile(PRINT_SIZES)
    print("Sheets:", xl_ps.sheet_names)
    for sheet in xl_ps.sheet_names:
        df = pd.read_excel(PRINT_SIZES, sheet_name=sheet)
        print(f"\n--- {sheet} --- rows={len(df)}, cols={len(df.columns)}")
        print("Columns:", list(df.columns))
        print(df.head(15).to_string())
        if len(df) > 15:
            print(f"... ({len(df)-15} more rows)")

    print("\n" + "=" * 70)
    print("3. Configuration Workbook - Size References")
    print("=" * 70)
    xl_cfg = pd.ExcelFile(CONFIG)
    print("Sheets:", xl_cfg.sheet_names)
    # find size reference sheet
    size_sheets = [s for s in xl_cfg.sheet_names if "size" in s.lower() or "reference" in s.lower()]
    print("Size-related sheets:", size_sheets)
    for sheet in xl_cfg.sheet_names:
        if "size" in sheet.lower() or "reference" in sheet.lower() or "print" in sheet.lower():
            df = pd.read_excel(CONFIG, sheet_name=sheet)
            print(f"\n--- {sheet} --- rows={len(df)}, cols={len(df.columns)}")
            print("Columns:", list(df.columns))
            print(df.head(12).to_string())
            if len(df) > 12:
                print(f"... ({len(df)-12} more rows)")

    print("\n" + "=" * 70)

    return {"BASE": BASE, "CONFIG": CONFIG, "M01": M01, "PRINT_COLS": PRINT_COLS, "PRINT_SIZES": PRINT_SIZES, "UPDATED": UPDATED, "col": col, "df": df, "n": n, "s": s, "sheet": sheet, "size_sheets": size_sheets, "t": t, "xl_cfg": xl_cfg, "xl_m01": xl_m01, "xl_ps": xl_ps}
