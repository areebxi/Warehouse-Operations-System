"""Changelog for phase3_cleanup."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def write_phase3_changelog(
    path: Path,
    *,
    backup_name: str,
    rows_before: int,
    rows_after: int,
    n_exact: int,
    size_counts: dict[str, int],
    d1_counts: dict[str, int],
    qa: dict,
) -> None:
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
    remaining_typos = qa["remaining size typos"]
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
**Backup:** `{backup_name}`  
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
| Remaining Navy/Royal colour-only conflict labels | {qa['remaining Navy/Royal colour-only conflict labels']} |
| Conflict labels remaining | {qa['conflict labels remaining']} |
| Same-core duplicate labels remaining | {qa['same-core duplicate labels remaining (3B skipped)']} |
| Exact full-row dups remaining | {qa['exact dups remaining']} |

---

## Next

Await supervisor direction for Phase 4 (ProductExport fills) and/or revisit 3B/D2/D3 if desired.

*See: [PHASE_3_APPROVAL.md](PHASE_3_APPROVAL.md)*
"""
    path.write_text(log, encoding="utf-8")
