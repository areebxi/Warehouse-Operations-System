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

# Compiled patterns
RE_X000D = re.compile(r"_x000D_", re.IGNORECASE)
RE_CRLF = re.compile(r"[\r\n]+")
RE_NY = re.compile(r"^(\d+)\s*[-–]\s*(\d+)\s*Y$", re.IGNORECASE)
RE_STUCK_YEARS = re.compile(r"^(\d+)\s*Years?$", re.IGNORECASE)
RE_STUCK_NO_SPACE = re.compile(r"^(\d+)Years$", re.IGNORECASE)
RE_BARE = re.compile(r"^(\d+)\s*[-–]\s*(\d+)$")
RE_YEARS_LOWER = re.compile(r"^(\d+)\s*[-–]\s*(\d+)\s+years\s*$", re.IGNORECASE)
RE_YEARS_TRAIL = re.compile(r"^(\d+)\s*[-–]\s*(\d+)\s+[Yy]ears\s+$")


def clean_text(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val)
    s = RE_X000D.sub("", s)
    s = RE_CRLF.sub(" ", s)
    s = s.strip()
    return s


def standardize_age_size(val: str) -> tuple[str, str | None]:
    """Return (new_value, rule_name_or_None)."""
    if not val:
        return val, None

    original = val

    # Already canonical "N-N Years"
    m = re.match(r"^(\d+)-(\d+) Years$", val)
    if m:
        return val, None

    # "N-N years" / mixed case / extra spaces
    m = re.match(r"^(\d+)\s*[-–]\s*(\d+)\s+[Yy]ears\s*$", val)
    if m:
        canon = f"{m.group(1)}-{m.group(2)} Years"
        if canon != original:
            return canon, "years_casing_or_spacing"
        return val, None

    # N-NY / N-Ny
    m = RE_NY.match(val)
    if m:
        return f"{m.group(1)}-{m.group(2)} Years", "short_Y"

    # Stuck "5Years"
    m = RE_STUCK_NO_SPACE.match(val)
    if m:
        return f"{m.group(1)} Years", "stuck_Years"

    # Single "5 years" / "5 Years " etc. (not age-band)
    m = re.match(r"^(\d+)\s*[Yy]ears\s*$", val)
    if m:
        canon = f"{m.group(1)} Years"
        if canon != original:
            return canon, "single_years_casing"
        return val, None

    # Bare N-N for known kids age bands only
    m = RE_BARE.match(val)
    if m:
        bare = f"{m.group(1)}-{m.group(2)}"
        if bare in AGE_BANDS:
            return f"{bare} Years", "bare_age_band"

    return original, None


def main() -> None:
    print("Loading source...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    rows_before = len(df)
    cols = list(df.columns)
    print(f"Loaded {rows_before} rows, {len(cols)} columns", flush=True)

    # --- 1. Dirty text cleanup ---
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

    # --- 2. Age size standardization ---
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

    # --- 3. Exact full-row duplicates ---
    dup_mask = df.duplicated(keep="first")
    dup_count = int(dup_mask.sum())
    df_clean = df.loc[~dup_mask].copy()
    rows_after = len(df_clean)
    print(f"Exact duplicates removed: {dup_count}", flush=True)
    print(f"Rows after: {rows_after}", flush=True)

    # Spot-check remaining short-Y
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

    # Changelog
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
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text(log, encoding="utf-8")
    print(f"Changelog written: {OUT_LOG}", flush=True)
    print("Phase 1 complete.", flush=True)


if __name__ == "__main__":
    main()
