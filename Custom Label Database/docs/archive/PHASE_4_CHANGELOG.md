# Phase 4 Changelog

**Executed:** 17 August 2026  
**Supervisor approval:**
- 4A Category: YES (G1 title case)
- 4B Sub-Category: YES (G1 title case)
- 4C Apparel Image: Gender Apparel + Colour slug (not PE URL)
- 4D Supplier Name -> BTC Activewear: YES
- 4E Supplier Product Code from SPC: YES
- 4F suffix join: F1
- 4G text: G1

**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `Custom Label Database_Updated_prePhase4_20260817_130356.xlsx`  
**Rows:** 119,179 (unchanged — no deletes)

---

## Summary

| Metric | Count |
|--------|------:|
| Rows with PE match (SKU and/or F1 suffix) | 107,469 |
| Match via Supplier SKU | 72,387 |
| Match via Custom Label suffix (F1) | 35,082 |
| Category filled (4A) | 107,469 |
| Sub-Category filled (4B) | 107,469 |
| Apparel Image set/updated (4C) | 34,755 |
| Supplier Name filled (4D) | 70,799 |
| Supplier Product Code filled (4E) | 107,179 |

---

## 4C — Apparel Image rule

Format: `Gender Apparel` + `Colour` with whitespace replaced by `-`, consecutive dashes collapsed.

Example: `Fruit Of The Loom - Mens Valueweight T` + `White` -> `Fruit-Of-The-Loom-Mens-Valueweight-T-White`

Applied to all rows where both Gender Apparel and Colour are non-empty (118,457 rows).

---

## QA

| Check | Count |
|-------|------:|
| Apparel Image containing `--` | 0 |
| Matched rows with Category still blank | 0 |

---

## Sample Apparel Images (first 5)

```
                       Gender Apparel     Colour                                    Apparel Image
Heavy Blend Adult Crewneck Sweatshirt Light Blue Heavy-Blend-Adult-Crewneck-Sweatshirt-Light-Blue
Heavy Blend Adult Crewneck Sweatshirt Light Blue Heavy-Blend-Adult-Crewneck-Sweatshirt-Light-Blue
Heavy Blend Adult Crewneck Sweatshirt Light Blue Heavy-Blend-Adult-Crewneck-Sweatshirt-Light-Blue
Heavy Blend Adult Crewneck Sweatshirt Light Blue Heavy-Blend-Adult-Crewneck-Sweatshirt-Light-Blue
Heavy Blend Adult Crewneck Sweatshirt Light Blue Heavy-Blend-Adult-Crewneck-Sweatshirt-Light-Blue
```

---

*See: [PHASE_4_APPROVAL.md](PHASE_4_APPROVAL.md)*
