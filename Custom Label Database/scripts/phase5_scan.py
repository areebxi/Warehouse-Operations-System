"""Scan Updated workbook for Phase 5 remaining work."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SRC = Path(r"D:\Custom Label Database\Custom Label Database_Updated.xlsx")
print("Loading...", flush=True)
df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
for c in df.columns:
    df[c] = df[c].fillna("").astype(str).str.strip()
print(f"Rows: {len(df)}\n", flush=True)

print("=== FILL RATES ===")
for col in df.columns:
    n = int(df[col].ne("").sum())
    pct = 100 * n / len(df)
    print(f"{col}: {n}/{len(df)} ({pct:.1f}%)")

print("\n=== PRINT POSITIONS (all values) ===")
for v, c in df["Print Positions"].value_counts().items():
    print(f"  [{v!r}]: {c}")

print("\n=== PRINT POSITIONS patterns ===")
pp = df["Print Positions"]
print(f"  blank: {(pp=='').sum()}")
print(f"  contains kebab-case: {pp.str.contains(r'[a-z]+-[a-z]', regex=True, na=False).sum()}")
print(f"  contains (M###): {pp.str.contains(r'\\(M\\d+\\)', regex=True, na=False).sum()}")
print(f"  contains _x000D_: {pp.str.contains('_x000D_', na=False).sum()}")
print(f"  Front Center: {(pp=='Front Center').sum()}")
print(f"  Front Left Pocket: {pp.str.contains('Front Left Pocket', na=False).sum()}")

print("\n=== PACKAGE / WEIGHT / SERVICE / TAGS (nonzero vs zero vs blank) ===")
for col in ["Package Type", "Weight", "Service", "Tags", "Size (Dimensions)", "Dummy Stock", "Supplier Stock"]:
    s = df[col]
    print(f"\n{col}:")
    print(f"  blank: {(s=='').sum()}")
    print(f"  '0': {(s=='0').sum()}")
    print(f"  other: {((s!='') & (s!='0')).sum()}")
    if (s!='').sum() > 0:
        print(f"  top non-zero: {s[s.notna() & (s!='') & (s!='0')].value_counts().head(8).to_string()}")

print("\n=== EMPTY COLUMN GROUPS ===")
empty_cols = [c for c in df.columns if df[c].eq("").all()]
print(f"Fully empty ({len(empty_cols)}): {empty_cols}")

print("\n=== CUSTOMISE / AMAZON PRIME ===")
for col in ["Customise", "Amazon Prime"]:
    print(f"{col}: {df[col].value_counts().to_string()}")

print("\nDone.", flush=True)
