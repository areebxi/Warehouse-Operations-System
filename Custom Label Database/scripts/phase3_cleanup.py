"""
Phase 3 cleanup — supervisor choices:
  3A exact dups: YES
  3B same-core keep richest: NO
  3C size typos: YES
  D1 Navy/Royal expand only inside colour-only conflicts: YES
  D2 gender-only prefer brand: NO
  D3 true conflicts report only: NO
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database_Updated.xlsx"
BACKUP = BASE / f"Custom Label Database_Updated_prePhase3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
OUT = SRC
LOG = BASE / "docs" / "PHASE_3_CHANGELOG.md"

SIZE_TYPOS = {
    "Meduim": "Medium",
    "ExtraSmall": "Extra Small",
    "Wodium": "Medium",
}

COLOUR_EXPAND_PAIRS = [
    ("Navy", "Navy Blue"),
    ("Royal", "Royal Blue"),
]


def main() -> None:
    print(f"Backing up to {BACKUP.name} ...", flush=True)
    shutil.copy2(SRC, BACKUP)

    print("Loading...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    rows_before = len(df)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)
    print(f"Rows before: {rows_before}", flush=True)

    # --- 3C size typos (global) ---
    size_counts: dict[str, int] = {}
    for src, dst in SIZE_TYPOS.items():
        mask = df["Size"] == src
        n = int(mask.sum())
        if n:
            size_counts[f"{src} -> {dst}"] = n
            df.loc[mask, "Size"] = dst
    print(f"3C size typos: {size_counts}", flush=True)

    # --- D1: colour expand only inside colour-only conflict labels ---
    cl = df["Custom Label"]
    vc = cl.value_counts()
    dup_labels = vc[vc > 1].index
    dup = df[cl.isin(dup_labels)].copy()

    # Per-label uniqueness
    stats = dup.groupby("Custom Label").agg(
        n_gender=("Gender Apparel", "nunique"),
        n_colour=("Colour", "nunique"),
        n_size=("Size", "nunique"),
    )
    colour_only = stats[
        (stats["n_gender"] == 1) & (stats["n_colour"] > 1) & (stats["n_size"] == 1)
    ].index

    d1_counts: dict[str, int] = {}
    labels_touched = 0
    for short, long in COLOUR_EXPAND_PAIRS:
        key = f"{short} -> {long} (colour-only conflicts)"
        n_cells = 0
        for lab in colour_only:
            colours = set(df.loc[df["Custom Label"] == lab, "Colour"].unique())
            # Only when the label's colours are exactly {short, long}
            if colours == {short, long}:
                mask = (df["Custom Label"] == lab) & (df["Colour"] == short)
                n = int(mask.sum())
                if n:
                    df.loc[mask, "Colour"] = long
                    n_cells += n
                    labels_touched += 1
        if n_cells:
            d1_counts[key] = n_cells
    print(f"D1 colour expand: {d1_counts} labels_touched~={labels_touched}", flush=True)

    # --- 3A exact full-row duplicates (after 3C/D1 so newly identical rows collapse) ---
    dup_mask = df.duplicated(keep="first")
    n_exact = int(dup_mask.sum())
    df = df.loc[~dup_mask].copy()
    rows_after = len(df)
    print(f"3A exact dups removed: {n_exact}", flush=True)
    print(f"Rows after: {rows_after}", flush=True)

    # QA
    remaining_typos = {
        k: int((df["Size"] == k).sum()) for k in SIZE_TYPOS
    }
    # Remaining colour-only Navy/Navy Blue or Royal/Royal Blue conflicts
    cl = df["Custom Label"]
    vc = cl.value_counts()
    dup = df[cl.isin(vc[vc > 1].index)]
    stats = dup.groupby("Custom Label").agg(
        n_gender=("Gender Apparel", "nunique"),
        n_colour=("Colour", "nunique"),
        n_size=("Size", "nunique"),
    )
    colour_only = stats[
        (stats["n_gender"] == 1) & (stats["n_colour"] > 1) & (stats["n_size"] == 1)
    ].index
    remaining_nr = 0
    for lab in colour_only:
        colours = set(df.loc[df["Custom Label"] == lab, "Colour"].unique())
        if colours in ({"Navy", "Navy Blue"}, {"Royal", "Royal Blue"}):
            remaining_nr += 1

    conflict_labels = int((stats["n_colour"].gt(0) & (
        (stats["n_gender"] > 1) | (stats["n_colour"] > 1) | (stats["n_size"] > 1)
    )).sum())
    # recount conflicts properly
    core = (
        dup["Gender Apparel"] + "||" + dup["Colour"] + "||" + dup["Size"]
    )
    n_core = dup.assign(_core=core).groupby("Custom Label")["_core"].nunique()
    n_conflict = int((n_core > 1).sum())
    n_same_core_dup_labels = int((n_core == 1).sum())

    qa = {
        "remaining size typos": remaining_typos,
        "remaining Navy/Royal colour-only conflict labels": remaining_nr,
        "conflict labels remaining": n_conflict,
        "same-core duplicate labels remaining (3B skipped)": n_same_core_dup_labels,
        "exact dups remaining": int(df.duplicated().sum()),
    }
    print(f"QA: {qa}", flush=True)

    print(f"Writing {OUT} ...", flush=True)
    df.to_excel(OUT, sheet_name="Data", index=False)
    print("Excel written.", flush=True)

    size_table = (
        "\n".join(f"| `{k}` | {v:,} |" for k, v in size_counts.items())
        if size_counts
        else "| (none) | 0 |"
    )
    d1_table = (
        "\n".join(f"| `{k}` | {v:,} |" for k, v in d1_counts.items())
        if d1_counts
        else "| (none) | 0 |"
    )

    log = f"""# Phase 3 Changelog

**Executed:** {datetime.now().strftime('%d %B %Y')}  
**Supervisor approval:**
- 3A exact dups: YES
- 3B same-core keep richest: **NO**
- 3C size typos: YES
- D1 Navy/Royal inside colour-only conflicts: YES
- D2 gender-only brand prefer: **NO**
- D3 conflict report: **NO**

**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `{BACKUP.name}`  
**Original archive:** `Custom Label Database.xlsx` (untouched)

---

## Summary

| Metric | Count |
|--------|------:|
| Rows before | {rows_before:,} |
| Rows after | {rows_after:,} |
| Exact full-row duplicates removed (3A) | {n_exact:,} |
| Size typo cells fixed (3C) | {sum(size_counts.values()):,} |
| Colour expand cells (D1) | {sum(d1_counts.values()):,} |

---

## 3C — Size typos

| Change | Cells |
|--------|------:|
{size_table}

---

## D1 — Colour expand (colour-only conflict labels only)

Only when a duplicate Custom Label differed solely in colour and the colour set was exactly `{{Navy, Navy Blue}}` or `{{Royal, Royal Blue}}`. Standalone Navy/Royal rows elsewhere were not changed. Black↔Navy / Black↔White left untouched.

| Change | Cells |
|--------|------:|
{d1_table}

---

## 3A — Exact full-row duplicates

Removed **{n_exact:,}** identical rows (keep first), after 3C/D1 so newly identical rows could collapse.

---

## Skipped (per approval)

| Item | Status |
|------|--------|
| 3B same-core richest-row merge | Skipped — ~same-core duplicate labels still present |
| D2 gender-only brand-style merge | Skipped |
| D3 PHASE_3_CONFLICTS.csv | Not written |

---

## QA after Phase 3

| Check | Value |
|-------|------:|
| Remaining Meduim / ExtraSmall / Wodium | {remaining_typos} |
| Remaining Navy/Royal colour-only conflict labels | {remaining_nr} |
| Conflict labels remaining | {n_conflict} |
| Same-core duplicate labels remaining | {n_same_core_dup_labels} |
| Exact full-row dups remaining | {int(df.duplicated().sum())} |

---

## Next

Await supervisor direction for Phase 4 (ProductExport fills) and/or revisit 3B/D2/D3 if desired.

*See: [PHASE_3_APPROVAL.md](PHASE_3_APPROVAL.md)*
"""
    LOG.write_text(log, encoding="utf-8")
    print(f"Changelog: {LOG}", flush=True)
    print("Phase 3 complete.", flush=True)


if __name__ == "__main__":
    main()
