"""
Phase 4 — ProductExport fills + Apparel Image slug.

Supervisor choices:
  4A Category from Department: YES
  4B Sub-Category from Sub Department: YES
  4C Apparel Image = Gender Apparel + Colour slug (not PE URL)
  4D Supplier Name -> BTC Activewear (matched blanks): YES
  4E Supplier Product Code from SPC: YES
  4F suffix join: F1
  4G department text: G1 (title case)
"""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE = Path(r"D:\Custom Label Database")
SRC = BASE / "Custom Label Database_Updated.xlsx"
PE_PATH = BASE / "ProductExport.xlsx"
BACKUP = BASE / f"Custom Label Database_Updated_prePhase4_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
OUT = SRC
LOG = BASE / "docs" / "PHASE_4_CHANGELOG.md"

BTC_SUPPLIER = "BTC Activewear"


def g1_format(text: str) -> str:
    """Title-case PE department strings, preserving hyphenated parts."""
    if not text:
        return text
    words = text.split()
    out: list[str] = []
    for word in words:
        if "-" in word:
            out.append("-".join(part.capitalize() for part in word.split("-")))
        else:
            out.append(word.capitalize())
    return " ".join(out)


def apparel_image_slug(gender_apparel: str, colour: str) -> str:
    """Gender Apparel + Colour with spaces as dashes, no double dashes."""
    combined = f"{gender_apparel} {colour}".strip()
    if not combined:
        return ""
    slug = re.sub(r"\s+", "-", combined)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def load_pe() -> pd.DataFrame:
    pe = pd.read_excel(PE_PATH, sheet_name="staff", dtype=str)
    if str(pe.iloc[0].get("UID", "")).startswith("["):
        pe = pe.iloc[1:].reset_index(drop=True)
    for c in pe.columns:
        pe[c] = pe[c].fillna("").astype(str).str.strip()
    return pe.drop_duplicates("UID").set_index("UID", drop=False)


def resolve_pe_uid(row: pd.Series) -> str:
    sku = row.get("sku", "")
    if sku and sku in pe_index.index:
        return sku
    suffix = row.get("suffix", "")
    if not row.get("sku", "") and suffix and suffix in pe_index.index:
        return suffix
    return ""


def main() -> None:
    global pe_index
    print(f"Backing up to {BACKUP.name} ...", flush=True)
    shutil.copy2(SRC, BACKUP)

    print("Loading CLD...", flush=True)
    df = pd.read_excel(SRC, sheet_name="Data", dtype=str)
    rows = len(df)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()

    print("Loading PE...", flush=True)
    pe_index = load_pe()

    df["sku"] = df["Supplier SKU"].str.replace(r"\.0$", "", regex=True).str.strip()
    df["suffix"] = df["Custom Label"].str.extract(r"-(\d+)$")[0].fillna("")

    counts: dict[str, int] = {}

    # Resolve PE match per row (primary SKU, F1 suffix fallback)
    pe_uids = df.apply(resolve_pe_uid, axis=1)
    matched = pe_uids.ne("")
    counts["rows_with_pe_match"] = int(matched.sum())
    counts["match_via_supplier_sku"] = int(
        (df["sku"].ne("") & df["sku"].isin(pe_index.index)).sum()
    )
    counts["match_via_suffix_f1"] = int(
        (
            df["sku"].eq("")
            & df["suffix"].ne("")
            & df["suffix"].isin(pe_index.index)
        ).sum()
    )

    pe_dept = pe_uids.map(pe_index["Department"])
    pe_sub = pe_uids.map(pe_index["Sub Department"])
    pe_spc = pe_uids.map(pe_index["SPC"])

    # 4A Category (blank only, matched, G1)
    mask = matched & df["Category"].eq("") & pe_dept.ne("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Category"] = pe_dept[mask].map(g1_format)
        counts["4A_category_filled"] = n

    # 4B Sub-Category (blank only, matched, G1)
    mask = matched & df["Sub-Category"].eq("") & pe_sub.ne("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Sub-Category"] = pe_sub[mask].map(g1_format)
        counts["4B_subcategory_filled"] = n

    # 4D Supplier Name (blank only, matched)
    mask = matched & df["Supplier Name"].eq("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Supplier Name"] = BTC_SUPPLIER
        counts["4D_supplier_name_filled"] = n

    # 4E Supplier Product Code (blank only, matched)
    mask = matched & df["Supplier Product Code"].eq("") & pe_spc.ne("")
    n = int(mask.sum())
    if n:
        df.loc[mask, "Supplier Product Code"] = pe_spc[mask]
        counts["4E_spc_filled"] = n

    # 4C Apparel Image slug from Gender Apparel + Colour (all rows where both present)
    has_both = df["Gender Apparel"].ne("") & df["Colour"].ne("")
    combined = df["Gender Apparel"] + " " + df["Colour"]
    new_images = (
        combined.str.replace(r"\s+", "-", regex=True)
        .str.replace(r"-+", "-", regex=True)
        .str.strip("-")
    )
    changed_img = has_both & (df["Apparel Image"] != new_images)
    n_img = int(changed_img.sum())
    df.loc[has_both, "Apparel Image"] = new_images[has_both]
    counts["4C_apparel_image_set_or_updated"] = n_img
    counts["4C_apparel_image_total_with_both_fields"] = int(has_both.sum())

    df.drop(columns=["sku", "suffix"], inplace=True)

    print(f"Counts: {counts}", flush=True)

    # QA samples
    sample = df.loc[has_both, ["Gender Apparel", "Colour", "Apparel Image"]].head(5)
    print("Sample Apparel Images:", flush=True)
    print(sample.to_string(index=False), flush=True)

    double_dash = int(df["Apparel Image"].str.contains(r"--", regex=True, na=False).sum())
    empty_cat_matched = int((matched & df["Category"].eq("")).sum())
    print(f"QA double-dash in Apparel Image: {double_dash}", flush=True)
    print(f"QA matched but Category still blank: {empty_cat_matched}", flush=True)

    print(f"Writing {OUT} ...", flush=True)
    df.to_excel(OUT, sheet_name="Data", index=False)
    print("Excel written.", flush=True)

    log = f"""# Phase 4 Changelog

**Executed:** {datetime.now().strftime('%d %B %Y')}  
**Supervisor approval:**
- 4A Category: YES (G1 title case)
- 4B Sub-Category: YES (G1 title case)
- 4C Apparel Image: Gender Apparel + Colour slug (not PE URL)
- 4D Supplier Name -> BTC Activewear: YES
- 4E Supplier Product Code from SPC: YES
- 4F suffix join: F1
- 4G text: G1

**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `{BACKUP.name}`  
**Rows:** {rows:,} (unchanged — no deletes)

---

## Summary

| Metric | Count |
|--------|------:|
| Rows with PE match (SKU and/or F1 suffix) | {counts.get('rows_with_pe_match', 0):,} |
| Match via Supplier SKU | {counts.get('match_via_supplier_sku', 0):,} |
| Match via Custom Label suffix (F1) | {counts.get('match_via_suffix_f1', 0):,} |
| Category filled (4A) | {counts.get('4A_category_filled', 0):,} |
| Sub-Category filled (4B) | {counts.get('4B_subcategory_filled', 0):,} |
| Apparel Image set/updated (4C) | {counts.get('4C_apparel_image_set_or_updated', 0):,} |
| Supplier Name filled (4D) | {counts.get('4D_supplier_name_filled', 0):,} |
| Supplier Product Code filled (4E) | {counts.get('4E_spc_filled', 0):,} |

---

## 4C — Apparel Image rule

Format: `Gender Apparel` + `Colour` with whitespace replaced by `-`, consecutive dashes collapsed.

Example: `Fruit Of The Loom - Mens Valueweight T` + `White` -> `Fruit-Of-The-Loom-Mens-Valueweight-T-White`

Applied to all rows where both Gender Apparel and Colour are non-empty ({counts.get('4C_apparel_image_total_with_both_fields', 0):,} rows).

---

## QA

| Check | Count |
|-------|------:|
| Apparel Image containing `--` | {double_dash} |
| Matched rows with Category still blank | {empty_cat_matched} |

---

## Sample Apparel Images (first 5)

```
{sample.to_string(index=False)}
```

---

*See: [PHASE_4_APPROVAL.md](PHASE_4_APPROVAL.md)*
"""
    LOG.write_text(log, encoding="utf-8")
    print(f"Changelog: {LOG}", flush=True)
    print("Phase 4 complete.", flush=True)


if __name__ == "__main__":
    main()
