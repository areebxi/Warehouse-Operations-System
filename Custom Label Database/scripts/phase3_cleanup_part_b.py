from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
import pandas as pd

def _main_part_b(ctx: dict):
    c = ctx['c']
    cl = ctx['cl']
    colour_only = ctx['colour_only']
    colours = ctx['colours']
    d1_counts = ctx['d1_counts']
    df = ctx['df']
    dst = ctx['dst']
    dup = ctx['dup']
    dup_labels = ctx['dup_labels']
    dup_mask = ctx['dup_mask']
    key = ctx['key']
    lab = ctx['lab']
    labels_touched = ctx['labels_touched']
    long = ctx['long']
    mask = ctx['mask']
    n = ctx['n']
    n_cells = ctx['n_cells']
    n_exact = ctx['n_exact']
    rows_after = ctx['rows_after']
    rows_before = ctx['rows_before']
    short = ctx['short']
    size_counts = ctx['size_counts']
    src = ctx['src']
    stats = ctx['stats']
    vc = ctx['vc']
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

