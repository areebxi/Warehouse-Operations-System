# Phase 3 — Approval Request

**Status:** APPROVED AND EXECUTED (15 August 2026) — see choices below  
**Working file:** `Custom Label Database_Updated.xlsx`  
**Backup:** `Custom Label Database_Updated_prePhase3_*.xlsx`  
**Changelog:** `docs/PHASE_3_CHANGELOG.md`  

**Supervisor choices:** 3A YES · 3B NO · 3C YES · D1 YES · D2 NO · D3 NO


---

## Current duplicate profile (after Phase 2)

| Metric | Count |
|--------|------:|
| Total rows | 119,347 |
| Unique Custom Labels | 62,729 |
| Labels appearing once | 12,010 |
| Labels appearing 2+ times | **50,719** |
| Rows involved in duplicate labels | 107,337 |
| Exact full-row duplicates still present | **135** |
| **Same-core** duplicates (same Gender + Colour + Size) | **50,250** labels / **105,776** rows |
| **Conflict** duplicates (same label, different Gender/Colour/Size) | **469** labels / **1,561** rows |

Phase 2 colour expansion cut conflicts sharply (was ~2,419 labels pre–Phase 2).

---

## Goal

Collapse safe duplicates so each Custom Label ideally maps to one product row, without silently destroying true conflicts.

---

## In scope (Phase 3) — proposed

### 3A — Drop remaining exact full-row duplicates (recommended: YES)

Same as Phase 1 rule: keep first, drop identical extras.

**Est. rows removed:** ~135

### 3B — Same-core merge: keep one “richest” row per Custom Label (recommended: YES)

For labels where **Gender Apparel + Colour + Size** are identical across duplicates:

1. Score each row by count of non-empty fields  
2. Tie-break prefer `Customise = Yes`  
3. Tie-break prefer non-empty `Supplier SKU`  
4. Tie-break prefer non-empty `Supplier Name`  
5. Tie-break prefer non-empty `Print Positions`  
6. Keep highest-scoring row; drop the rest  

**Est. rows removed:** ~55,526  
**Note:** Many same-core pairs differ mainly in `Package Type` / `Supplier Name` / `Customise` (empty vs filled). Richest-row keeps the more complete record.

### 3C — Pre-fix size typos inside conflicts (recommended: YES)

| From | To | Labels affected (size-only conflicts) |
|------|----|--------------------------------------:|
| `Meduim` | `Medium` | ~10 |
| `ExtraSmall` | `Extra Small` | ~2 |
| `Wodium` | `Medium` | ~1 |

After fix, re-classify; some may become same-core and merge under 3B.

### 3D — Conflict handling (need your picks)

#### Conflict breakdown now

| Type | Labels | Notes |
|------|-------:|-------|
| Colour-only | 141 | See pairs below |
| Gender-only | 223 | Category name vs brand/product name |
| Size-only | 26 | Typos + a few real mismatches |
| Multi-field | 79 | Often different products sharing a label |

**Top colour-only pairs**

| Pair | Labels |
|------|-------:|
| Black ↔ Navy | 56 |
| Navy ↔ Navy Blue | 42 |
| Royal ↔ Royal Blue | 35 |
| Black ↔ White | 8 |

**Top gender-only pattern:** e.g. `Kids-T-Shirt` ↔ `Fruit Of The Loom - Kids Valueweight T` (same SKU family, different naming style).

#### Proposed conflict policy options

| ID | Action | Default proposal |
|----|--------|------------------|
| **D1** | Expand `Navy`→`Navy Blue` and `Royal`→`Royal Blue` **only inside colour-only conflict groups**, then re-run same-core merge | **YES** (narrow; does not touch standalone Navy/Royal rows) |
| **D2** | Gender-only: keep the **longer / brand-style** name (contains ` - ` or starts with brand), drop category-only twin if Colour+Size+SKU align | **YES** when Supplier SKU matches or both empty; else report |
| **D3** | True conflicts (Black↔Navy, Black↔White, multi-field, mismatched size/gender products) | **Report only** — do not auto-delete; write `PHASE_3_CONFLICTS.csv` |
| **D4** | After 3A–3D, leave remaining conflict labels in the DB but listed in the report | **YES** |

---

## Out of scope

- ProductExport Category / Sub-Category / image / supplier fills → **Phase 4**
- Full Print Positions taxonomy → **Phase 5**
- Renaming Custom Labels to fix shared-SKU identity collisions

---

## Expected outcome (if defaults approved)

| Step | Approx effect |
|------|----------------|
| 3A exact dups | −135 rows |
| 3B same-core keep richest | −~55,500 rows |
| 3C size typos | small; enables a few more merges |
| 3D1 Navy/Royal inside conflicts | reduces ~77 colour-only conflicts |
| 3D2 gender-only safe merges | reduces a large share of 223 |
| Remaining conflicts | reported in CSV; rows kept |

Rough landing: **~60–65k rows** (exact depends on D2 strictness). Unique labels stay ~62.7k minus any label fully removed (none — we keep ≥1 row per label except impossible cases).

Actually: we never delete a Custom Label entirely in Phase 3; we only remove extra rows. Unique label count stays the same or drops only if a label’s rows somehow all vanish (they won’t).

---

## Execution plan (after approval)

1. Backup `Custom Label Database_Updated.xlsx`  
2. Apply 3A → 3C → 3D (approved parts) → 3B (richest merge, possibly twice if D1/D2 create new same-cores)  
3. Write updated working file  
4. Write changelog + conflict CSV  
5. Stop for Phase 4 approval  

---

## Supervisor checklist — reply with choices

```
Phase 3: APPROVED with choices
3A exact dups: YES
3B same-core keep richest: YES
3C size typos Meduim/ExtraSmall/Wodium: YES
D1 Navy/Royal expand only inside colour conflicts: YES/NO
D2 gender-only prefer brand-style when safe: YES/NO
D3 true conflicts report only: YES
```

Or reject with reasons.

---

## Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Supervisor | | Approved: 3A YES, 3B NO, 3C YES, D1 YES, D2 NO, D3 NO | 15 Aug 2026 |
| Database manager (agent) | Auto | Executed — see `PHASE_3_CHANGELOG.md` | 15 Aug 2026 |

---

*See: [FINDINGS.md](FINDINGS.md), [PHASE_2_CHANGELOG.md](PHASE_2_CHANGELOG.md)*
