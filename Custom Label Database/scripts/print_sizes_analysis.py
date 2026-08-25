"""Deep analysis of print size fill strategy."""
import pandas as pd
import re
from pathlib import Path

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
print("4. Custom Label Database - print columns fill rates")
print("=" * 70)
df = pd.read_excel(UPDATED, usecols=lambda c: c in PRINT_COLS or c in [
    "Custom Label", "Supplier SKU", "Supplier Product Code", "Category", "Sub-Category",
    "Gender Apparel", "Size", "Colour"
])
print(f"Total rows: {len(df)}")
for col in PRINT_COLS:
    if col in df.columns:
        pct, n = fill_rate(df, col)
        print(f"  {col}: {pct:.1f}% ({n:,})")

# Print Positions analysis
if "Print Positions" in df.columns:
    pp = df["Print Positions"].fillna("").astype(str).str.strip()
    has_pp = pp != ""
    print(f"\nPrint Positions non-empty: {has_pp.sum():,}")
    # extract M codes
    m_codes = pp.str.findall(r"\(M(\d+)\)")
    all_codes = [c for codes in m_codes for c in codes]
    from collections import Counter
    code_counts = Counter(all_codes)
    print("Top (M###) codes in Print Positions:", code_counts.most_common(15))
    # positions without mm but with Print Positions
    w1 = df.get("Width 1 (mm)", pd.Series([""]*len(df)))
    has_w1 = w1.apply(nonempty)
    print(f"Rows with Print Positions but no Width 1: {(has_pp & ~has_w1).sum():,}")
    print(f"Rows with no Print Positions: {(~has_pp).sum():,}")

print("\n" + "=" * 70)
print("5. Join key overlap probes")
print("=" * 70)

# Load key reference tables for join analysis
m01_sheets = {s: pd.read_excel(M01, sheet_name=s) for s in xl_m01.sheet_names}

# Try to find size ref in config
size_ref = None
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

print_sizes_df = pd.read_excel(PRINT_SIZES, sheet_name=0)

print(f"\nSize ref sheet used: {size_ref_sheet if size_ref is not None else 'NOT FOUND'}")
if size_ref is not None:
    print("Size ref columns:", list(size_ref.columns))
    print("Size ref unique key candidates:")
    for c in size_ref.columns:
        u = size_ref[c].dropna().nunique()
        print(f"  {c}: {u} unique, sample: {size_ref[c].dropna().head(3).tolist()}")

print("\nPrint Sizes columns:", list(print_sizes_df.columns))
for c in print_sizes_df.columns:
    u = print_sizes_df[c].dropna().nunique()
    print(f"  {c}: {u} unique")

# Category overlap
if size_ref is not None and "Category" in df.columns:
    db_cats = set(df["Category"].dropna().astype(str).str.strip().unique())
    ref_cols = [c for c in size_ref.columns if "category" in c.lower() or "department" in c.lower() or "product" in c.lower()]
    for rc in ref_cols:
        ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
        overlap = db_cats & ref_vals
        print(f"\nDB Category vs SizeRef[{rc}]: DB={len(db_cats)}, Ref={len(ref_vals)}, overlap={len(overlap)}")
        if len(overlap) < 30:
            print("  Overlap:", sorted(overlap)[:20])
        missing = db_cats - ref_vals
        print(f"  DB categories not in ref: {len(missing)}")
        if missing and len(missing) <= 25:
            print("  ", sorted(missing))

# Sub-category
if size_ref is not None:
    ref_cols = [c for c in size_ref.columns if "sub" in c.lower()]
    for rc in ref_cols:
        if "Category" in df.columns:
            db_subs = set(df["Sub-Category"].dropna().astype(str).str.strip().unique())
            ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
            overlap = db_subs & ref_vals
            print(f"\nDB Sub-Category vs SizeRef[{rc}]: overlap={len(overlap)} / DB={len(db_subs)} / Ref={len(ref_vals)}")

# Gender Apparel
if size_ref is not None:
    ga_cols = [c for c in size_ref.columns if any(x in c.lower() for x in ["gender", "apparel", "style", "product"])]
    print("\nPotential product-type columns in size ref:", ga_cols)
    for rc in ga_cols[:5]:
        ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
        if "Gender Apparel" in df.columns:
            db_ga = set(df["Gender Apparel"].dropna().astype(str).str.strip().unique())
            overlap = db_ga & ref_vals
            print(f"  DB Gender Apparel vs [{rc}]: overlap={len(overlap)} / DB={len(db_ga)} / Ref={len(ref_vals)}")

# Print position name overlap
if size_ref is not None:
    pos_cols = [c for c in size_ref.columns if "position" in c.lower() or "print" in c.lower()]
    print("\nPosition-related columns in size ref:", pos_cols)
    if "Print Positions" in df.columns:
        db_pos = set()
        for val in df["Print Positions"].dropna():
            for part in re.split(r",\s*", str(val)):
                part = re.sub(r"\s*\(M\d+\)\s*$", "", part.strip())
                if part:
                    db_pos.add(part)
        for rc in pos_cols:
            ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
            overlap = db_pos & ref_vals
            print(f"  DB position segments vs [{rc}]: overlap={len(overlap)} / DB={len(db_pos)} / Ref={len(ref_vals)}")
            db_only = db_pos - ref_vals
            if db_only:
                print(f"    DB-only positions (sample): {sorted(db_only)[:15]}")

# Size column overlap (letter sizes)
if size_ref is not None and "Size" in df.columns:
    size_cols = [c for c in size_ref.columns if "size" in c.lower()]
    db_sizes = set(df["Size"].dropna().astype(str).str.strip().unique())
    print(f"\nDB has {len(db_sizes)} unique Size values")
    for rc in size_cols:
        ref_vals = set(size_ref[rc].dropna().astype(str).str.strip().unique())
        overlap = db_sizes & ref_vals
        print(f"  DB Size vs [{rc}]: overlap={len(overlap)} / Ref={len(ref_vals)}")

print("\n" + "=" * 70)
print("6. Simulate lookup dimensions")
print("=" * 70)

if size_ref is not None:
    # show numeric mm columns
    mm_cols = [c for c in size_ref.columns if "width" in c.lower() or "height" in c.lower() or "mm" in c.lower()]
    print("MM columns in size ref:", mm_cols)
    print_sizes_mm = [c for c in print_sizes_df.columns if "width" in c.lower() or "height" in c.lower() or "mm" in c.lower()]
    print("MM columns in Print Sizes:", print_sizes_mm)

# M01 mock code to dimensions
for sheet, sdf in m01_sheets.items():
    code_cols = [c for c in sdf.columns if "mock" in c.lower() or "code" in c.lower() or "m0" in str(c).lower()]
    mm_cols = [c for c in sdf.columns if "width" in c.lower() or "height" in c.lower()]
    if code_cols or mm_cols:
        print(f"\nM01 [{sheet}] code cols: {code_cols}, mm cols: {mm_cols}")
        if len(sdf) <= 30:
            print(sdf.to_string())

print("\nDONE")
