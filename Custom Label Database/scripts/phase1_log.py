"""Changelog writer for phase1_cleanup."""
from __future__ import annotations

from pathlib import Path

from phase1_util import AGE_BANDS


def write_phase1_changelog(
    path: Path,
    *,
    rows_before: int,
    rows_after: int,
    dup_count: int,
    dirty_cells_before: int,
    dirty_by_col: dict[str, int],
    size_changed: int,
    size_rules: dict[str, int],
    size_examples: list[tuple[str, str, str]],
    cols: list[str],
    remaining_y: int,
    remaining_bare: int,
    remaining_x000d: int,
) -> None:
    dirty_table = "\n".join(
        f"| {c} | {n} |" for c, n in sorted(dirty_by_col.items(), key=lambda x: -x[1])
    )
    examples_table = "\n".join(
        f"| `{a}` | `{b}` | `{r}` |" for a, b, r in size_examples[:25]
    )
    rules_table = "\n".join(f"| `{k}` | {v} |" for k, v in sorted(size_rules.items()))

    log = f"""# Phase 1 Changelog

**Executed:** 15 August 2026  
**Supervisor approval:** Phase 1 approved (implement)  
**Source:** `Custom Label Database.xlsx`  
**Output:** `Custom Label Database_PHASE1.xlsx`  
**Original file:** untouched

---

## Summary

| Metric | Count |
|--------|------:|
| Rows before | {rows_before:,} |
| Rows after | {rows_after:,} |
| Exact full-row duplicates removed | {dup_count:,} |
| Dirty-text cells changed | {dirty_cells_before:,} |
| Size age-standardization cells changed | {size_changed:,} |
| Columns | {len(cols)} |

---

## 1. Dirty-text cleanup

Actions: remove `_x000D_`, replace CR/LF with space, trim leading/trailing whitespace.

### Cells changed by column

| Column | Cells changed |
|--------|--------------:|
{dirty_table if dirty_table else "| (none) | 0 |"}

### QA

| Check | Count |
|-------|------:|
| Rows still containing `_x000D_` | {remaining_x000d} |

---

## 2. Age-band Size standardization

### Changes by rule

| Rule | Cells |
|------|------:|
{rules_table if rules_table else "| (none) | 0 |"}

### Sample before → after

| Before | After | Rule |
|--------|-------|------|
{examples_table if examples_table else "| — | — | — |"}

### QA

| Check | Count |
|-------|------:|
| Remaining `N-NY` sizes | {remaining_y} |
| Remaining bare age-band sizes ({", ".join(AGE_BANDS)}) | {remaining_bare} |

**Not changed in Phase 1:** letter↔word sizes (`S`/`Small`), months, `A4`/`11Oz`/dimension sizes.

---

## 3. Exact full-row duplicates

- Method: `duplicated(keep="first")` after cleanup + size standardization
- Removed: **{dup_count:,}** rows
- Near-duplicates and conflict Custom Labels **retained** for later phases

---

## Next

Await supervisor approval for **Phase 2** (colour spelling, Gender Apparel normalization, size letter/word policy).

See: `docs/FINDINGS.md`, `docs/PHASE_1_APPROVAL.md`
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(log, encoding="utf-8")
