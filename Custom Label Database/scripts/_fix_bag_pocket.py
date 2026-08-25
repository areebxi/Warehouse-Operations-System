"""Rename Front Left Pocket -> Pocket on bag/backpack/keyring rows only (CSV)."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd

PATH = Path(r"D:\Custom Label Database\Custom Label Database.csv")

BAG_RE = re.compile(
    r"bag|backpack|keyring|tote|wristlet|china-bag|\bbg-bg\d|\bbg-china",
    re.I,
)
BAG_EXACT = {
    "BG-BG125",
    "BG-BG125J",
    "BG-China-Bag",
    "BAGBAS Junior Fashion Backpack",
    "BagBase Boutique Wristlet Keyring",
}
FLP = re.compile(r"Front\s+Left\s+Pocket", re.I)


def main() -> None:
    df = pd.read_csv(PATH, dtype=str, low_memory=False)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()

    ga = df["Gender Apparel"]
    is_bag = ga.str.contains(BAG_RE, regex=True) | ga.isin(BAG_EXACT)

    cols = ["Print Positions"] + [
        c for c in df.columns if c.startswith("Position") and "Name" in c
    ]

    counts: Counter[str] = Counter()
    changed_rows = 0
    for i in df.index[is_bag]:
        row_changed = False
        for c in cols:
            old = df.at[i, c]
            if not old or not FLP.search(old):
                continue
            new = FLP.sub("Pocket", old)
            if new != old:
                df.at[i, c] = new
                counts[c] += 1
                row_changed = True
        if row_changed:
            changed_rows += 1

    print("rows changed:", changed_rows)
    print("cell hits by column:")
    for c, n in counts.items():
        print(f"  {c}: {n}")

    left = 0
    for c in cols:
        left += int((is_bag & df[c].str.contains(FLP, regex=True)).sum())
    print("remaining FLP on bag rows:", left)

    sample = df.loc[
        is_bag & df["Print Positions"].str.contains(r"\bPocket\b", regex=True),
        ["Gender Apparel", "Print Positions", "Position 1 Name", "Position 2 Name"],
    ].head(8)
    print(sample.to_string(index=False))

    df.to_csv(PATH, index=False)
    print("wrote", PATH, "bytes", PATH.stat().st_size)


if __name__ == "__main__":
    main()
