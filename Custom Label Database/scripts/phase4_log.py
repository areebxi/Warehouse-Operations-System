"""Changelog for phase4_cleanup."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def write_phase4_changelog(
    path: Path,
    *,
    backup_name: str,
    rows: int,
    counts: dict[str, int],
    sample,
    double_dash: int,
    empty_cat_matched: int,
) -> None:
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
**Backup:** `{backup_name}`  
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
    path.write_text(log, encoding="utf-8")
