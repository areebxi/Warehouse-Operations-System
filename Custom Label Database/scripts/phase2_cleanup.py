"""
Phase 2 cleanup for Custom Label Database_Updated.xlsx

Approved choices:
  A  colour typos: YES
  B  navy/royal leave: YES (do not merge Royal/Navy families)
  B+ abbrev expand: YES — Dark Heather→Dark Heather Grey, Azure→Azure Blue only
  C  S↔Small: YES — prefer words (S→Small, M→Medium, L→Large, XL→Extra Large, XS→Extra Small)
  D  double-space + Womens-Sweat-Shirt: YES
  D  Men's→Mens: YES
  E  Front Print→Front Center: YES
"""
from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database_Updated.xlsx"
BACKUP = BASE / f"Custom Label Database_Updated_prePhase2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
OUT = SRC  # update working file in place after backup
LOG = BASE / "docs" / "PHASE_2_CHANGELOG.md"

COLOUR_TYPOS = {
    "Fuschia": "Fuchsia",
    "Colbalt Blue": "Cobalt Blue",
    "Sport Grey": "Sports Grey",
    "Light-Pink": "Light Pink",
}

# B+: only supervisor-approved abbreviation expansions (NOT Navy/Royal)
COLOUR_ABBREV = {
    "Dark Heather": "Dark Heather Grey",
    "Azure": "Azure Blue",
}

SIZE_TO_WORD = {
    "S": "Small",
    "M": "Medium",
    "L": "Large",
    "XL": "Extra Large",
    "XS": "Extra Small",
}


def apply_map(series: pd.Series, mapping: dict[str, str]) -> tuple[pd.Series, dict[str, int]]:
    counts: dict[str, int] = {}
    out = series.copy()
    for src, dst in mapping.items():
        mask = out == src
        n = int(mask.sum())
        if n:
            counts[f"{src} -> {dst}"] = n
            out = out.mask(mask, dst)
    return out, counts


def main() -> None:
    print(f"Backing up to {BACKUP.name} ...", flush=True)
    shutil.copy2(SRC, BACKUP)

    print("Loading working file...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    rows = len(df)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str)
    print(f"Rows: {rows}", flush=True)

    all_counts: dict[str, dict[str, int]] = {}

    # A + B+
    df["Colour"], c1 = apply_map(df["Colour"], COLOUR_TYPOS)
    df["Colour"], c2 = apply_map(df["Colour"], COLOUR_ABBREV)
    all_counts["A_colour_typos"] = c1
    all_counts["Bplus_colour_abbrev"] = c2
    print(f"A typos: {c1}", flush=True)
    print(f"B+ abbrev: {c2}", flush=True)

    # C sizes → words
    df["Size"], c3 = apply_map(df["Size"], SIZE_TO_WORD)
    all_counts["C_size_to_words"] = c3
    print(f"C sizes: {c3}", flush=True)

    # D Gender Apparel
    ga = df["Gender Apparel"]
    # double spaces → single (repeat until stable for 3+ spaces)
    ga2 = ga.str.replace(r" {2,}", " ", regex=True)
    n_space = int((ga2 != ga).sum())
    ga = ga2

    n_mens = int(ga.str.contains("Men's", regex=False).sum())
    ga = ga.str.replace("Men's", "Mens", regex=False)

    n_sweat = int((ga == "Womens-Sweat-Shirt").sum())
    ga = ga.mask(ga == "Womens-Sweat-Shirt", "Womens-Sweatshirt")

    df["Gender Apparel"] = ga
    all_counts["D_gender_apparel"] = {
        "collapse_double_spaces": n_space,
        "Men's -> Mens": n_mens,
        "Womens-Sweat-Shirt -> Womens-Sweatshirt": n_sweat,
    }
    print(f"D gender: {all_counts['D_gender_apparel']}", flush=True)

    # E Print Positions
    pp = df["Print Positions"]
    n_fp = int((pp == "Front Print").sum())
    pp = pp.mask(pp == "Front Print", "Front Center")
    df["Print Positions"] = pp
    all_counts["E_print_positions"] = {"Front Print -> Front Center": n_fp}
    print(f"E print: {all_counts['E_print_positions']}", flush=True)

    # QA
    qa = {
        "remaining Fuschia": int((df["Colour"] == "Fuschia").sum()),
        "remaining Colbalt Blue": int((df["Colour"] == "Colbalt Blue").sum()),
        "remaining Sport Grey": int((df["Colour"] == "Sport Grey").sum()),
        "remaining Dark Heather": int((df["Colour"] == "Dark Heather").sum()),
        "remaining Azure (exact)": int((df["Colour"] == "Azure").sum()),
        "remaining letter S/M/L/XL/XS": int(df["Size"].isin(SIZE_TO_WORD).sum()),
        "remaining Men's": int(df["Gender Apparel"].str.contains("Men's", regex=False).sum()),
        "remaining double spaces in Gender Apparel": int(
            df["Gender Apparel"].str.contains(r" {2,}", regex=True).sum()
        ),
        "remaining Front Print": int((df["Print Positions"] == "Front Print").sum()),
        "Royal unchanged count": int((df["Colour"] == "Royal").sum()),
        "Navy unchanged count": int((df["Colour"] == "Navy").sum()),
    }
    print(f"QA: {qa}", flush=True)

    print(f"Writing {OUT} ...", flush=True)
    df.to_excel(OUT, sheet_name="Data", index=False)
    print("Excel written.", flush=True)

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
**Backup:** `{BACKUP.name}`  
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
    LOG.write_text(log, encoding="utf-8")
    print(f"Changelog: {LOG}", flush=True)
    print("Phase 2 complete.", flush=True)


if __name__ == "__main__":
    main()
