"""
Phase 1 cleanup for Custom Label Database.xlsx
- Dirty text strip (_x000D_, CR/LF, trim)
- Age-band Size standardization
- Exact full-row duplicate removal
Writes: Custom Label Database_PHASE1.xlsx + docs/PHASE_1_CHANGELOG.md
Does NOT modify the original workbook.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scripts.phase1_cleanup_impl import standardize_age_size, clean_text

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database.xlsx"
OUT_XLSX = BASE / "Custom Label Database_PHASE1.xlsx"
OUT_LOG = BASE / "docs" / "PHASE_1_CHANGELOG.md"

AGE_BANDS = [
    "1-2",
    "2-3",
    "3-4",
    "4-5",
    "5-6",
    "7-8",
    "9-11",
    "12-13",
    "12-14",
    "14-15",
]

RE_X000D = re.compile(r"_x000D_", re.IGNORECASE)
RE_CRLF = re.compile(r"[\r\n]+")
RE_NY = re.compile(r"^(\d+)\s*[-–]\s*(\d+)\s*Y$", re.IGNORECASE)
RE_STUCK_YEARS = re.compile(r"^(\d+)\s*Years?$", re.IGNORECASE)
RE_STUCK_NO_SPACE = re.compile(r"^(\d+)Years$", re.IGNORECASE)
RE_BARE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
RE_YEARS_LOWER = re.compile(r"^(\d+)\s*[-–]\s*(\d+)\s+years\s*$", re.IGNORECASE)
RE_YEARS_TRAIL = re.compile(r"^(\d+)\s*[-–]\s*(\d+)\s+[Yy]ears\s+$")

def main() -> None:
    print("Loading source...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    rows_before = len(df)
    cols = list(df.columns)
    print(f"Loaded {rows_before} rows, {len(cols)} columns", flush=True)

    dirty_cells_before = 0
    dirty_by_col: dict[str, int] = {}
    for col in cols:
        as_str = df[col].fillna("").astype(str)
        cleaned = as_str.map(clean_text)
        changed = cleaned != as_str
        n = int(changed.sum())
        if n:
            dirty_by_col[col] = n
            dirty_cells_before += n
        df[col] = cleaned

    print(f"Dirty-text cells changed: {dirty_cells_before}", flush=True)
    for c, n in sorted(dirty_by_col.items(), key=lambda x: -x[1])[:15]:
        print(f"  {c}: {n}", flush=True)

    size_rules: dict[str, int] = {}
    size_examples: list[tuple[str, str, str]] = []
    new_sizes = []
    for v in df["Size"].tolist():
        nv, rule = standardize_age_size(v)
        new_sizes.append(nv)
        if rule:
            size_rules[rule] = size_rules.get(rule, 0) + 1
            if len(size_examples) < 40 and (v, nv, rule) not in size_examples:
                size_examples.append((v, nv, rule))
    df["Size"] = new_sizes
    size_changed = sum(size_rules.values())
    print(f"Size age-standardization cells changed: {size_changed}", flush=True)
    print(f"  by rule: {size_rules}", flush=True)

    dup_mask = df.duplicated(keep="first")
    dup_count = int(dup_mask.sum())
    df_clean = df.loc[~dup_mask].copy()
    rows_after = len(df_clean)
    print(f"Exact duplicates removed: {dup_count}", flush=True)
    print(f"Rows after: {rows_after}", flush=True)

    remaining_y = df_clean["Size"].str.match(r"^\d+-\d+Y$", case=False, na=False).sum()
    remaining_bare = df_clean["Size"].isin(AGE_BANDS).sum()
    remaining_x000d = (
        df_clean.astype(str)
        .apply(lambda s: s.str.contains(r"_x000D_", case=False, na=False))
        .any(axis=1)
        .sum()
    )
    print(f"QA remaining N-NY sizes: {remaining_y}", flush=True)
    print(f"QA remaining bare age bands: {remaining_bare}", flush=True)
    print(f"QA rows still with _x000D_: {remaining_x000d}", flush=True)

    print(f"Writing {OUT_XLSX} ...", flush=True)
    df_clean.to_excel(OUT_XLSX, sheet_name="Data", index=False)
    print("Excel written.", flush=True)

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

| Metric | Count |
|--------|------:|
| Rows before | {rows_before:,} |
| Rows after | {rows_after:,} |
| Exact full-row duplicates removed | {dup_count:,} |
| Dirty-text cells changed | {dirty_cells_before:,} |
| Size age-standardization cells changed | {size_changed:,} |
| Columns | {len(cols)} |

---

Actions: remove `_x000D_`, replace CR/LF with space, trim leading/trailing whitespace.

| Column | Cells changed |
|--------|--------------:|
{dirty_table if dirty_table else "| (none) | 0 |"}

| Check | Count |
|-------|------:|
| Rows still containing `_x000D_` | {remaining_x000d} |

---

| Rule | Cells |
|------|------:|
{rules_table if rules_table else "| (none) | 0 |"}

| Before | After | Rule |
|--------|-------|------|
{examples_table if examples_table else "| — | — | — |"}

| Check | Count |
|-------|------:|
| Remaining `N-NY` sizes | {remaining_y} |
| Remaining bare age-band sizes ({", ".join(AGE_BANDS)}) | {remaining_bare} |

**Not changed in Phase 1:** letter↔word sizes (`S`/`Small`), months, `A4`/`11Oz`/dimension sizes.

---

- Method: `duplicated(keep="first")` after cleanup + size standardization
- Removed: **{dup_count:,}** rows
- Near-duplicates and conflict Custom Labels **retained** for later phases

---

Await supervisor approval for **Phase 2** (colour spelling, Gender Apparel normalization, size letter/word policy).

See: `docs/FINDINGS.md`, `docs/PHASE_1_APPROVAL.md`
"""
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(log, encoding="utf-8")
    print(f"Changelog written: {OUT_LOG}", flush=True)
    print("Phase 1 complete.", flush=True)

if __name__ == "__main__":
    main()
