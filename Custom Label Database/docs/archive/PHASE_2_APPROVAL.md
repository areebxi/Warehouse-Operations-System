# Phase 2 — Approval Request

**Status:** APPROVED AND EXECUTED (15 August 2026)  
**Working file (input/output):** `Custom Label Database_Updated.xlsx`  
**Backup:** `Custom Label Database_Updated_prePhase2_*.xlsx`  
**Changelog:** `docs/PHASE_2_CHANGELOG.md`

---

## Working-file convention (locked in)

| File | Role |
|------|------|
| `Custom Label Database.xlsx` | Original archive — do not modify |
| `Custom Label Database_Updated.xlsx` | **Active working copy** for Phase 2+ |
| `ProductExport.xlsx` | Helper catalog |

Phase 1 file `Custom Label Database_PHASE1.xlsx` was renamed to `Custom Label Database_Updated.xlsx`.

---

## Goal

Standardize **values and naming** that are clearly inconsistent, without deleting near-duplicate rows or filling from ProductExport (those are Phases 3–4).

---

## In scope (Phase 2) — proposed

### A. Colour spelling / typo fixes (recommended: YES)

| From | To | Approx rows (pre-Phase-1 scan) |
|------|----|-------------------------------:|
| `Fuschia` | `Fuchsia` | ~2,398 |
| `Colbalt Blue` | `Cobalt Blue` | ~344 |
| `Sport Grey` | `Sports Grey` | ~330 |
| `Light-Pink` | `Light Pink` | ~4 |

### B. Colour near-duplicate policy (need your pick)

These look related but may be real distinct supplier colours. Default proposal: **leave alone** unless you choose merge.

| Family | Examples | Proposal default |
|--------|----------|------------------|
| Navy | Navy, Navy Blue, Deep Navy, French Navy… | **Leave** |
| Royal | Royal, Royal Blue, Bright Royal… | **Leave** |
| Grey (other) | Heather Grey, Ash Grey, etc. | **Leave** |
| Abbreviation expansion only | `Dark Heather` → `Dark Heather Grey`, `Azure` → `Azure Blue` | **Optional** — helps Phase 3 conflicts |

### C. Size letter ↔ word policy (need your pick)

| Option | Action |
|--------|--------|
| **C1 — Keep mixed (default)** | No change to `S`/`Small` systems |
| **C2 — Prefer words** | `S`→`Small`, `M`→`Medium`, `L`→`Large`, `XL`→`Extra Large`, `XS`→`Extra Small`; leave `2XL`/`3XL`/age/months as-is |
| **C3 — Prefer letters** | Reverse of C2 (`Small`→`S`, …) to align with ProductExport |

### D. Gender Apparel light cleanup (recommended: YES)

| Action | Example |
|--------|---------|
| Collapse double spaces after hyphens/dashes | `GILDAN -  Softstyle` → `GILDAN - Softstyle` |
| Normalize `Men's` → `Mens` in FOTL-style names **or** reverse | need pick |
| Fix rare `Womens-Sweat-Shirt` → `Womens-Sweatshirt` | 4 rows |

**Not rewriting** category-like (`Mens-T-Shirt`) into brand/product names or vice versa in Phase 2.

### E. Print Positions light cleanup (recommended: YES)

| From | To |
|------|----|
| Remaining casing/spacing only if any | trim already done in Phase 1 |
| `Front Print` → `Front Center` | **Optional** (~249 rows) — unify synonym |

Defer full Print Positions taxonomy to Phase 5.

---

## Out of scope (later phases)

- Deleting / merging near-duplicate Custom Labels (Phase 3)
- Conflict label resolution (Phase 3)
- Filling Category / Sub-Category / Supplier Name / images from ProductExport (Phase 4)
- Packaging, print size mm fields, Dispatch Days, etc. (Phase 5)

---

## Execution plan (after approval)

1. Load `Custom Label Database_Updated.xlsx`
2. Apply approved mappings only
3. Write results back to `Custom Label Database_Updated.xlsx` (after copying a timestamped backup e.g. `Custom Label Database_Updated_prePhase2.xlsx`)
4. Write `docs/PHASE_2_CHANGELOG.md`
5. Stop for Phase 3 approval

---

## Supervisor checklist — reply with choices

Copy/paste and edit:

```
Phase 2: APPROVED with choices
A colour typos: YES
B navy/royal leave: YES
B abbreviation expand (Dark Heather→Dark Heather Grey, Azure→Azure Blue): YES/NO
C size policy: C1 / C2 / C3
D Gender Apparel double-space fix: YES
D Men's → Mens: YES / NO / reverse (Mens → Men's)
D Womens-Sweat-Shirt fix: YES
E Front Print → Front Center: YES/NO
Output: update Custom Label Database_Updated.xlsx + prePhase2 backup
```

Or reject:

```
Phase 2: REJECTED
- reason...
```

---

## Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Supervisor | | Approved: A YES, B leave, B+ YES, C words, D YES, E YES | 15 Aug 2026 |
| Database manager (agent) | Auto | Executed — see `PHASE_2_CHANGELOG.md` | 15 Aug 2026 |

---

*See also: [FINDINGS.md](FINDINGS.md), [PHASE_1_CHANGELOG.md](PHASE_1_CHANGELOG.md)*
