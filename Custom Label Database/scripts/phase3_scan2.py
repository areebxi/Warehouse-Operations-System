"""Faster Phase 3 conflict breakdown on Updated workbook."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

SRC = Path(r"D:\Custom Label Database\Custom Label Database_Updated.xlsx")
print("Loading...", flush=True)
df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
for c in df.columns:
    df[c] = df[c].fillna("").astype(str)

cl = df["Custom Label"]
vc = cl.value_counts()
dup_labels = vc[vc > 1].index
dup = df[cl.isin(dup_labels)].copy()
dup["_core"] = dup["Gender Apparel"] + "||" + dup["Colour"] + "||" + dup["Size"]

# Pre-aggregate uniqueness per label
agg = dup.groupby("Custom Label").agg(
    n_rows=("Custom Label", "size"),
    n_core=("_core", "nunique"),
    n_gender=("Gender Apparel", "nunique"),
    n_colour=("Colour", "nunique"),
    n_size=("Size", "nunique"),
    n_supplier_sku=("Supplier SKU", "nunique"),
    n_customise=("Customise", "nunique"),
    n_print=("Print Positions", "nunique"),
    n_pkg=("Package Type", "nunique"),
    n_image=("Apparel Image", "nunique"),
    n_supplier_name=("Supplier Name", "nunique"),
)
conflict = agg[agg["n_core"] > 1]
same = agg[agg["n_core"] == 1]
print(f"same-core labels: {len(same)} rows={int(same['n_rows'].sum())}")
print(f"conflict labels: {len(conflict)} rows={int(conflict['n_rows'].sum())}")
print(f"exact full-row dups: {int(df.duplicated().sum())}")

only_colour = conflict[(conflict.n_gender == 1) & (conflict.n_colour > 1) & (conflict.n_size == 1)]
only_gender = conflict[(conflict.n_gender > 1) & (conflict.n_colour == 1) & (conflict.n_size == 1)]
only_size = conflict[(conflict.n_gender == 1) & (conflict.n_colour == 1) & (conflict.n_size > 1)]
multi = conflict[~conflict.index.isin(only_colour.index.union(only_gender.index).union(only_size.index))]
print(f"conflict colour-only: {len(only_colour)}")
print(f"conflict gender-only: {len(only_gender)}")
print(f"conflict size-only: {len(only_size)}")
print(f"conflict multi-field: {len(multi)}")

# Colour-only pairs
pair_c = Counter()
for lab in only_colour.index:
    cols = tuple(sorted(dup.loc[dup["Custom Label"] == lab, "Colour"].unique()))
    pair_c[cols] += 1
print("\nColour-only conflict pairs:")
for pair, n in pair_c.most_common(25):
    print(f"  {n}x {pair}")

# Gender-only pairs
pair_g = Counter()
for lab in only_gender.index:
    vals = tuple(sorted(dup.loc[dup["Custom Label"] == lab, "Gender Apparel"].unique()))
    pair_g[vals] += 1
print("\nGender-only conflict pairs (top 20):")
for pair, n in pair_g.most_common(20):
    print(f"  {n}x {pair}")

# Size-only
pair_s = Counter()
for lab in only_size.index:
    vals = tuple(sorted(dup.loc[dup["Custom Label"] == lab, "Size"].unique()))
    pair_s[vals] += 1
print("\nSize-only conflict pairs:")
for pair, n in pair_s.most_common(20):
    print(f"  {n}x {pair}")

# Same-core: which non-core cols differ — vectorized via nunique from a wider agg
print("\nSame-core labels where non-core fields differ (nunique>1):")
for col, key in [
    ("Supplier SKU", "n_supplier_sku"),
    ("Customise", "n_customise"),
    ("Print Positions", "n_print"),
    ("Package Type", "n_pkg"),
    ("Apparel Image", "n_image"),
    ("Supplier Name", "n_supplier_name"),
]:
    print(f"  {col}: {(same[key] > 1).sum()} labels")

# Estimate rows removable if keep-one richest per same-core label
extra_same = int(same["n_rows"].sum() - len(same))
print(f"\nIf keep 1 row per same-core duplicate label, rows removed: {extra_same}")
print(f"If also drop remaining exact dups among uniques: {int(df.duplicated().sum())}")

# Multi conflict samples
print("\nMulti-field conflict samples (10 labels):")
for lab in list(multi.index[:10]):
    g = dup[dup["Custom Label"] == lab][
        ["Gender Apparel", "Colour", "Size", "Supplier SKU", "Customise"]
    ].drop_duplicates()
    print(f"\n{lab}:")
    print(g.to_string(index=False))

print("\nDone.", flush=True)
