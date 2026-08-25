"""Quick scan of Updated workbook for Phase 2 mapping candidates."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

SRC = Path(r"D:\Custom Label Database\Custom Label Database_Updated.xlsx")
print("Loading...", flush=True)
df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
for c in df.columns:
    df[c] = df[c].fillna("").astype(str)

colours = df["Colour"]
print("\n=== Colour typo targets ===")
for v in ["Fuschia", "Colbalt Blue", "Sport Grey", "Light-Pink", "Fuchsia", "Cobalt Blue", "Sports Grey", "Light Pink"]:
    print(f"  {v!r}: {(colours == v).sum()}")

print("\n=== Possible abbrev pairs (short count / long count) ===")
# Find colours where X exists and "X Something" or longer form exists
uniq = colours[colours.ne("")].value_counts()
# Known proposed
pairs = [
    ("Dark Heather", "Dark Heather Grey"),
    ("Azure", "Azure Blue"),
    ("Royal", "Royal Blue"),  # B says leave navy/royal — do NOT apply unless only abbrev list
    ("Navy", "Navy Blue"),
]
for a, b in pairs:
    print(f"  {a!r}: {uniq.get(a, 0)}  |  {b!r}: {uniq.get(b, 0)}")

# Heuristic: single-word colour that is a prefix of another colour ending with that word's expansion
print("\n=== Short colours that are exact prefix of a longer colour (top) ===")
names = list(uniq.index)
shorts = [n for n in names if " " not in n and "-" not in n and "/" not in n]
hits = []
for s in shorts:
    longer = [n for n in names if n.startswith(s + " ") and n != s]
    if longer:
        hits.append((s, uniq[s], [(l, uniq[l]) for l in longer[:5]]))
hits.sort(key=lambda x: -x[1])
for s, cnt, longs in hits[:40]:
    print(f"  {s!r} ({cnt}) -> {longs}")

print("\n=== Size letter/word counts ===")
sizes = df["Size"]
for v in ["S", "M", "L", "XL", "XS", "Small", "Medium", "Large", "Extra Large", "Extra Small", "2XL", "3XL", "XXL"]:
    print(f"  {v!r}: {(sizes == v).sum()}")

print("\n=== Gender Apparel ===")
ga = df["Gender Apparel"]
print(f"  double-space patterns: {ga.str.contains(r'  +', regex=True).sum()}")
print("  Men's count:", ga.str.contains("Men's", regex=False).sum())
print("  Womens-Sweat-Shirt:", (ga == "Womens-Sweat-Shirt").sum())
print("  Front Print:", (df["Print Positions"] == "Front Print").sum())
print("Done.", flush=True)
