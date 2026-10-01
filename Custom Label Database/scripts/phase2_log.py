"""Changelog for phase2_cleanup."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def write_phase2_changelog(
    path: Path,
    *,
    backup_name: str,
    rows: int,
    all_counts: dict[str, dict[str, int]],
    qa: dict,
) -> None:
    def section(title: str, counts: dict[str, int]) -> str:
        if not counts:
            return f"### {title}\n\nNo changes.\n"
        lines = "\n".join(f"| `{k}` | {v:,} |" for k, v in counts.items())
        return f"### {title}\n\n| Change | Rows |\n|--------|-----:|\n{lines}\n"

    total_changed = sum(sum(d.values()) for d in all_counts.values())
    log = f"""# Phase 2 Changelog

**Executed:** {datetime.now().strftime('%d %B %Y')}  
**Supervisor approval:** A YES · B leave Navy/Royal · B+ abbrev YES · C words YES · D YES · E YES  
**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `{backup_name}`  
**Original archive:** `Custom Label Database.xlsx` (untouched)

---

## Summary

| Metric | Value |
|--------|------:|
| Rows (unchanged — no deletes) | {rows:,} |
| Mapping cells changed (sum of rule hits) | {total_changed:,} |

---

## Changes applied

{section("A — Colour typos", all_counts["A_colour_typos"])}
{section("B+ — Colour abbreviation expand (approved pairs only)", all_counts["Bplus_colour_abbrev"])}
**B — Navy / Royal families:** left unchanged (per approval).

{section("C — Size letter → word", all_counts["C_size_to_words"])}
Left unchanged: `2XL`, `3XL`, `4XL`, `5XL`, age bands, months, `A4`/`11Oz`/etc.

{section("D — Gender Apparel", all_counts["D_gender_apparel"])}
{section("E — Print Positions", all_counts["E_print_positions"])}

---

## QA after Phase 2

| Check | Count |
|-------|------:|
| Remaining `Fuschia` | {qa['remaining Fuschia']} |
| Remaining `Colbalt Blue` | {qa['remaining Colbalt Blue']} |
| Remaining `Sport Grey` | {qa['remaining Sport Grey']} |
| Remaining `Dark Heather` | {qa['remaining Dark Heather']} |
| Remaining exact `Azure` | {qa['remaining Azure (exact)']} |
| Remaining letter `S`/`M`/`L`/`XL`/`XS` | {qa['remaining letter S/M/L/XL/XS']} |
| Remaining `Men's` | {qa["remaining Men's"]} |
| Remaining double spaces in Gender Apparel | {qa['remaining double spaces in Gender Apparel']} |
| Remaining `Front Print` | {qa['remaining Front Print']} |
| `Royal` still present (expected) | {qa['Royal unchanged count']} |
| `Navy` still present (expected) | {qa['Navy unchanged count']} |

---

## Not in Phase 2

- Near-duplicate / conflict Custom Label merges → Phase 3
- ProductExport Category / image / supplier fills → Phase 4
- Full Print Positions taxonomy → Phase 5

---

*See: [PHASE_2_APPROVAL.md](PHASE_2_APPROVAL.md), [FINDINGS.md](FINDINGS.md)*
"""
    path.write_text(log, encoding="utf-8")
