# Phase 2 Changelog

**Executed:** 15 August 2026  
**Supervisor approval:** A YES · B leave Navy/Royal · B+ abbrev YES · C words YES · D YES · E YES  
**Input / output:** `Custom Label Database_Updated.xlsx`  
**Backup:** `Custom Label Database_Updated_prePhase2_20260815_180426.xlsx`  
**Original archive:** `Custom Label Database.xlsx` (untouched)

---

## Summary

| Metric | Value |
|--------|------:|
| Rows (unchanged — no deletes) | 119,347 |
| Mapping cells changed (sum of rule hits) | 24,555 |

---

## Changes applied

### A — Colour typos

| Change | Rows |
|--------|-----:|
| `Fuschia -> Fuchsia` | 2,398 |
| `Colbalt Blue -> Cobalt Blue` | 302 |
| `Sport Grey -> Sports Grey` | 320 |
| `Light-Pink -> Light Pink` | 3 |

### B+ — Colour abbreviation expand (approved pairs only)

| Change | Rows |
|--------|-----:|
| `Dark Heather -> Dark Heather Grey` | 819 |
| `Azure -> Azure Blue` | 910 |

**B — Navy / Royal families:** left unchanged (per approval).

### C — Size letter → word

| Change | Rows |
|--------|-----:|
| `S -> Small` | 611 |
| `M -> Medium` | 611 |
| `L -> Large` | 611 |
| `XL -> Extra Large` | 3,522 |
| `XS -> Extra Small` | 72 |

Left unchanged: `2XL`, `3XL`, `4XL`, `5XL`, age bands, months, `A4`/`11Oz`/etc.

### D — Gender Apparel

| Change | Rows |
|--------|-----:|
| `collapse_double_spaces` | 1,123 |
| `Men's -> Mens` | 12,959 |
| `Womens-Sweat-Shirt -> Womens-Sweatshirt` | 4 |

### E — Print Positions

| Change | Rows |
|--------|-----:|
| `Front Print -> Front Center` | 290 |


---

## QA after Phase 2

| Check | Count |
|-------|------:|
| Remaining `Fuschia` | 0 |
| Remaining `Colbalt Blue` | 0 |
| Remaining `Sport Grey` | 0 |
| Remaining `Dark Heather` | 0 |
| Remaining exact `Azure` | 0 |
| Remaining letter `S`/`M`/`L`/`XL`/`XS` | 0 |
| Remaining `Men's` | 0 |
| Remaining double spaces in Gender Apparel | 0 |
| Remaining `Front Print` | 0 |
| `Royal` still present (expected) | 1693 |
| `Navy` still present (expected) | 4260 |

---

## Not in Phase 2

- Near-duplicate / conflict Custom Label merges → Phase 3
- ProductExport Category / image / supplier fills → Phase 4
- Full Print Positions taxonomy → Phase 5

---

*See: [PHASE_2_APPROVAL.md](PHASE_2_APPROVAL.md), [FINDINGS.md](FINDINGS.md)*
