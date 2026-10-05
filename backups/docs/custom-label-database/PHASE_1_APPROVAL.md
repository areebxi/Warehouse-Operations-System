# Phase 1 — Approval Request

**Status:** APPROVED AND EXECUTED (15 August 2026)  
**Target file:** `Custom Label Database.xlsx`  
**Output:** `Custom Label Database_PHASE1.xlsx` (original left untouched)  
**Changelog:** `docs/PHASE_1_CHANGELOG.md`

---

## Goal

Perform **safe, low-risk cleanup only**. No merges of conflicting products, no ProductExport fills, no colour/size system conversions beyond explicit age-band expansion and dirty-text removal.

---

## In scope (Phase 1)

### 1. Strip dirty text (all text columns)

| Action | Example |
|--------|---------|
| Remove `_x000D_` | `M150-137470_x000D_` → `M150-137470` |
| Replace CR/LF with a single space | multi-line cells → one line |
| Trim leading/trailing whitespace | `5-6 Years ` → `5-6 Years` |

**Estimated impact:** ~940 Custom Labels, ~184 Gender Apparel, plus smaller hits on Colour / Size / Print Positions / Supplier Product Code.

### 2. Delete exact full-row duplicates

Keep the **first** occurrence; drop later rows that are identical across all 48 columns (after dirty-text cleanup above).

**Estimated impact:** ~8,261 rows removed.

### 3. Standardize age-band Size values only

| From | To |
|------|----|
| `2-3Y`, `3-4Y`, `5-6Y`, `7-8Y`, `9-11Y`, `14-15Y` (any case) | `2-3 Years`, `3-4 Years`, … |
| Bare age ranges used as kids sizes: `1-2`, `2-3`, `3-4`, `4-5`, `5-6`, `7-8`, `9-11`, `12-13`, `12-14`, `14-15` | `N-N Years` |
| `9-11 years` (lowercase) | `9-11 Years` |
| `5Years` / `NYears` stuck form | `5 Years` / `N Years` |
| Values already like `2-3 Years` | unchanged |

**Not in Phase 1:**

- Converting `Small` ↔ `S` / `Large` ↔ `L`
- Changing month sizes (`0-3 Months`, etc.)
- Changing non-apparel sizes (`A4`, `11Oz`, `150mm*150mm`, …)

**Estimated impact:** ~2,200+ Size cells.

---

## Out of scope (later phases)

- Colour spelling merges (`Fuschia` → `Fuchsia`, `Colbalt` → `Cobalt`, …)
- Navy / Royal / Grey variant policy
- Gender Apparel normalization (`Men's` vs `Mens`, double spaces)
- Duplicate collapse when rows differ in any field
- Conflict Custom Labels (same label, different Gender/Colour/Size)
- Filling Category / Sub-Category / Supplier Name / images from ProductExport
- Print Positions standardization
- Overwriting the original workbook

---

## Execution plan (after approval)

1. Load `Custom Label Database.xlsx` → sheet `Data`
2. Apply dirty-text cleanup on all object/text columns
3. Apply age-band Size mapping
4. Drop exact full-row duplicates
5. Write `Custom Label Database_PHASE1.xlsx`
6. Write changelog with before/after row counts and per-rule change counts
7. Stop and wait for Phase 2 approval

---

## Risks & safeguards

| Risk | Mitigation |
|------|------------|
| Accidental data loss | Original file never modified; Phase 1 writes a new file |
| Age bare ranges misclassified | Only apply bare `N-N` → `N-N Years` for known kids age bands listed above |
| Duplicate drop removes a “better” identical twin | Rows are identical after cleanup — no information loss |
| Custom Label uniqueness still not guaranteed | Phase 1 only removes exact duplicates; near-dupes remain for Phase 3 |

---

## Supervisor checklist

Reply with approval, e.g.:

```
Phase 1: APPROVED
```

Or approve with edits, e.g.:

```
Phase 1: APPROVED with changes
- Do not touch bare N-N sizes
- Changelog must include sample before/after rows
```

Or reject:

```
Phase 1: REJECTED
- reason...
```

---

## Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Supervisor | | Approved (implement) | 15 Aug 2026 |
| Database manager (agent) | Auto | Executed — see `PHASE_1_CHANGELOG.md` | 15 Aug 2026 |

---

*See also: [FINDINGS.md](FINDINGS.md) for full scan detail.*
