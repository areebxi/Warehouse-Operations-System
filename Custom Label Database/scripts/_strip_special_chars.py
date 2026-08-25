"""Scan / strip special characters from seed columns."""
from __future__ import annotations

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(r"d:\Custom Label Database")
DB = BASE / "Custom Label Database.xlsx"
SHEET = "Data"
SEED = [
    "Custom Label",
    "Gender Apparel",
    "Colour",
    "Size",
    "Apparel Image",
    "Print Positions",
]

# Allow letters, digits, space, dash, comma, parentheses, slash, period, plus, hash.
# Strip trademark, ampersand, apostrophe, and other symbols.
ALLOWED_RE = re.compile(r"[^A-Za-z0-9 ,\-/().+#]")


def strip_special(text: str) -> str:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    s = str(text)
    # Readable replacements before deleting leftover symbols
    s = s.replace("&", " and ")
    s = s.replace("*", " x ")
    s = ALLOWED_RE.sub("", s)
    s = re.sub(r" {2,}", " ", s).strip()
    s = re.sub(r"-{2,}", "-", s)
    return s.strip(" -")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print("Loading...", flush=True)
    df = pd.read_excel(DB, sheet_name=SHEET, dtype=str)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)

    print("=== Before ===", flush=True)
    for c in SEED:
        if c not in df.columns:
            continue
        bad_mask = df[c].ne("") & df[c].map(lambda x: bool(ALLOWED_RE.search(x)))
        n = int(bad_mask.sum())
        print(f"  {c}: {n}", flush=True)
        if n:
            chars: set[str] = set()
            for v in df.loc[bad_mask, c].unique()[:5000]:
                chars.update(ALLOWED_RE.findall(v))
            print(f"    chars: {sorted(chars)!r}", flush=True)
            print(df.loc[bad_mask, c].value_counts().head(8).to_string(), flush=True)

    changed = 0
    samples = []
    for c in SEED:
        if c not in df.columns:
            continue
        before = df[c].copy()
        after = before.map(strip_special)
        mask = before != after
        n = int(mask.sum())
        changed += n
        if n:
            for i in before[mask].head(3).index:
                samples.append((c, before.at[i], after.at[i]))
        df[c] = after

    print(f"\nCells that would change: {changed:,}", flush=True)
    for c, b, a in samples[:12]:
        print(f"  [{c}] {b!r} -> {a!r}", flush=True)

    if args.dry_run:
        print("Dry-run: not writing.", flush=True)
        return

    bak_dir = BASE / "support" / "backups"
    bak_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = bak_dir / f"Custom Label Database_preStripSpecial_{stamp}.xlsx"
    print(f"Backup -> {bak}", flush=True)
    shutil.copy2(DB, bak)
    print(f"Writing {DB} ...", flush=True)
    df.to_excel(DB, sheet_name=SHEET, index=False)
    print("Done.", flush=True)


if __name__ == "__main__":
    main()
