"""Scan Custom Label Database_Updated.xlsx for Phase 3 duplicate/conflict profile."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

SRC = Path(r"D:\Custom Label Database\Custom Label Database_Updated.xlsx")
print("Loading...", flush=True)
df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
for c in df.columns:
    df[c] = df[c].fillna("").astype(str)
print(f"Rows: {len(df)}", flush=True)

cl = df["Custom Label"]
vc = cl.value_counts()
print(f"Unique labels: {len(vc)}")
print(f"Labels appear once: {(vc == 1).sum()}")
print(f"Labels appear 2+: {(vc > 1).sum()}")
print(f"Rows in duplicate labels: {int(vc[vc > 1].sum())}")
print(f"Exact full-row dups remaining: {int(df.duplicated().sum())}")

dup_labels = set(vc[vc > 1].index)
dup_df = df[cl.isin(dup_labels)].copy()
dup_df["_core"] = (
    dup_df["Gender Apparel"] + "||" + dup_df["Colour"] + "||" + dup_df["Size"]
)
n_core = dup_df.groupby("Custom Label")["_core"].nunique()
conflict = n_core[n_core > 1]
same = n_core[n_core == 1]
print(f"\nSame-core duplicate labels: {len(same)} (rows={int(cl.isin(same.index).sum())})")
print(f"Conflict duplicate labels: {len(conflict)} (rows={int(cl.isin(conflict.index).sum())})")

# For same-core: how many unique full rows per label
same_df = dup_df[dup_df["Custom Label"].isin(same.index)]
# exact identical within label vs differ non-core
n_full = same_df.groupby("Custom Label").apply(
    lambda g: g.drop(columns=["_core"]).drop_duplicates().shape[0],
    include_groups=False,
)
print(f"  fully identical within label: {(n_full == 1).sum()}")
print(f"  differ in non-core fields: {(n_full > 1).sum()}")

# Richness: which columns differ most within same-core groups
print("\n=== Columns that differ within same-core duplicate labels (sample 5000 labels) ===")
sample_labels = list(same.index[:5000])
sample = same_df[same_df["Custom Label"].isin(sample_labels)]
diff_cols = {}
for lab, g in sample.groupby("Custom Label"):
    u = g.drop(columns=["_core"]).drop_duplicates()
    if len(u) < 2:
        continue
    for col in u.columns:
        if u[col].nunique() > 1:
            diff_cols[col] = diff_cols.get(col, 0) + 1
for col, n in sorted(diff_cols.items(), key=lambda x: -x[1])[:20]:
    print(f"  {col}: differs in {n} labels")

print("\n=== Conflict samples (15) ===")
for lab in list(conflict.index[:15]):
    g = dup_df[dup_df["Custom Label"] == lab][
        ["Custom Label", "Gender Apparel", "Colour", "Size", "Supplier SKU", "Customise", "Print Positions"]
    ].drop_duplicates()
    print(f"\n{lab} ({len(dup_df[dup_df['Custom Label']==lab])} rows):")
    print(g.to_string(index=False))

# After Phase 2 colour expand, how many conflicts are only colour-related vs gender vs size
print("\n=== Conflict breakdown ===")
only_colour = only_gender = only_size = multi = 0
for lab in conflict.index:
    g = dup_df[dup_df["Custom Label"] == lab]
    gc = g["Gender Apparel"].nunique()
    cc = g["Colour"].nunique()
    sc = g["Size"].nunique()
    flags = (gc > 1, cc > 1, sc > 1)
    if flags == (False, True, False):
        only_colour += 1
    elif flags == (True, False, False):
        only_gender += 1
    elif flags == (False, False, True):
        only_size += 1
    else:
        multi += 1
print(f"conflict colour-only: {only_colour}")
print(f"conflict gender-only: {only_gender}")
print(f"conflict size-only: {only_size}")
print(f"conflict multi-field: {multi}")

# Colour-only conflict: are they now identical after considering one is subset? show top pairs
print("\n=== Colour-only conflict value pairs (top 20) ===")
from collections import Counter

pair_c = Counter()
for lab in conflict.index:
    g = dup_df[dup_df["Custom Label"] == lab]
    if g["Gender Apparel"].nunique() == 1 and g["Size"].nunique() == 1 and g["Colour"].nunique() > 1:
        cols = tuple(sorted(g["Colour"].unique()))
        pair_c[cols] += 1
for pair, n in pair_c.most_common(20):
    print(f"  {n}x {pair}")

print("\nDone.", flush=True)
