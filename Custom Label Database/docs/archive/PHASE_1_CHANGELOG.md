# Phase 1 Changelog

**Executed:** 15 August 2026  
**Supervisor approval:** Phase 1 approved (implement)  
**Source:** `Custom Label Database.xlsx`  
**Output:** `Custom Label Database_PHASE1.xlsx` (later renamed to `Custom Label Database_Updated.xlsx`)  
**Original file:** untouched  
**Current working file:** `Custom Label Database_Updated.xlsx`

---

## Summary

| Metric | Count |
|--------|------:|
| Rows before | 127,741 |
| Rows after | 119,347 |
| Exact full-row duplicates removed | 8,394 |
| Dirty-text cells changed | 1,572 |
| Size age-standardization cells changed | 2,259 |
| Columns | 48 |

---

## 1. Dirty-text cleanup

Actions: remove `_x000D_`, replace CR/LF with space, trim leading/trailing whitespace.

### Cells changed by column

| Column | Cells changed |
|--------|--------------:|
| Custom Label | 940 |
| Gender Apparel | 184 |
| Apparel Image | 176 |
| Colour | 170 |
| Size | 55 |
| Print Positions | 41 |
| Supplier Product Code | 6 |

### QA

| Check | Count |
|-------|------:|
| Rows still containing `_x000D_` | 0 |

---

## 2. Age-band Size standardization

### Changes by rule

| Rule | Cells |
|------|------:|
| `bare_age_band` | 87 |
| `short_Y` | 2154 |
| `stuck_Years` | 2 |
| `years_casing_or_spacing` | 16 |

### Sample before → after

| Before | After | Rule |
|--------|-------|------|
| `3-4` | `3-4 Years` | `bare_age_band` |
| `5-6` | `5-6 Years` | `bare_age_band` |
| `7-8` | `7-8 Years` | `bare_age_band` |
| `9-11` | `9-11 Years` | `bare_age_band` |
| `14-15` | `14-15 Years` | `bare_age_band` |
| `2-3` | `2-3 Years` | `bare_age_band` |
| `5Years` | `5 Years` | `stuck_Years` |
| `9-11 years` | `9-11 Years` | `years_casing_or_spacing` |
| `7-8Y` | `7-8 Years` | `short_Y` |
| `2-3Y` | `2-3 Years` | `short_Y` |
| `3-4Y` | `3-4 Years` | `short_Y` |
| `5-6Y` | `5-6 Years` | `short_Y` |
| `9-11Y` | `9-11 Years` | `short_Y` |
| `14-15Y` | `14-15 Years` | `short_Y` |

### QA

| Check | Count |
|-------|------:|
| Remaining `N-NY` sizes | 0 |
| Remaining bare age-band sizes (1-2, 2-3, 3-4, 4-5, 5-6, 7-8, 9-11, 12-13, 12-14, 14-15) | 0 |

**Not changed in Phase 1:** letter↔word sizes (`S`/`Small`), months, `A4`/`11Oz`/dimension sizes.

---

## 3. Exact full-row duplicates

- Method: `duplicated(keep="first")` after cleanup + size standardization
- Removed: **8,394** rows
- Near-duplicates and conflict Custom Labels **retained** for later phases

---

## Next

Await supervisor approval for **Phase 2** (colour spelling, Gender Apparel normalization, size letter/word policy).

See: `docs/FINDINGS.md`, `docs/PHASE_1_APPROVAL.md`
