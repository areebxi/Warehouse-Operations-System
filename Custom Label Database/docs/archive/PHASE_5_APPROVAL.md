# Phase 5 — Approval Request

**Status:** AWAITING SUPERVISOR APPROVAL  
**Working file:** `Custom Label Database_Updated.xlsx` (119,179 rows)  
**Helper files available:**
- `M01_print_config_20260814_103010.xlsx` (print positions, mm sizes, product metadata)
- `Configuration Workbook.xlsx` (print size references, overrides)
- `ProductExport.xlsx` (already used in Phase 4)

**Backup if approved:** `Custom Label Database_Updated_prePhase5_*.xlsx`  
**Changelog if approved:** `docs/PHASE_5_CHANGELOG.md`

---

## Goal

Finish **remaining structural cleanup**: Print Positions naming, placeholder/zero cleanup, and optional fills for columns that are still empty — using config workbooks where data exists.

No row deletes unless you separately re-approve Phase 3B.

---

## Current state (post Phase 4 scan)

### Still fully empty (0% filled) — 26 columns

| Group | Columns |
|-------|---------|
| Print config detail | Print Position Code, Position 1–4 Name, Print Size 1–4, Width/Height 1–4 (mm) |
| Product meta | Printing Type, Design Type |
| Dimensions / packaging | Length/Width/Height (cm), Weight (g), Outer Packaging, Inner Packaging, Dispatch Days |

### Partially filled — needs policy

| Column | Filled | Notes |
|--------|-------:|-------|
| Print Positions | 36.8% | 75,336 blank; mixed human + kebab-case + `(M###)` codes |
| Package Type | 44.4% | 13,867 rows = `0`; values: Large Letter, Parcel, … |
| Weight | 44.3% | 13,423 rows = `0`; numeric grams elsewhere |
| Service | 44.3% | 13,867 rows = `0`; Royal Mail48, etc. |
| Tags | 44.3% | 52,839 rows = `0`; no real tag values |
| Size (Dimensions) | 44.3% | 52,839 rows = `0`; no real values |
| Customise | 54.5% | 54,262 blank vs 64,917 `Yes` |
| Amazon Prime | 2.7% | 3,275 `Yes`; rest blank |
| Category / Sub-Category | 90.2% | 11,710 rows still blank (no PE match) |

### Print Positions value mix (top)

| Value | Rows |
|-------|-----:|
| *(blank)* | 75,336 |
| Front Center | 12,467 |
| Front Center, Back Center | 5,706 |
| Front Left Pocket | 4,277 |
| … with `(M118)` / `(M262)` / `(M180)` codes | ~12,500 combined |
| kebab-case technical strings | 568 |
| Oddities: `Back Center, Back Center` | 1 |

---

## In scope — proposed (pick each)

### 5A — Print Positions text cleanup (recommended: YES)

| Rule | Example |
|------|---------|
| Trim / collapse spaces | already mostly clean |
| `&` → `,` | `Front Left Pocket & Front Right Pocket` → `Front Left Pocket, Front Right Pocket` |
| Remove duplicate segment | `Back Center, Back Center` → `Back Center` |
| Normalize comma spacing | `A,B` → `A, B` |

**Does not** remove `(M118)` codes unless you opt in below.

### 5B — Strip print mock codes from Print Positions (optional)

| Option | Action |
|--------|--------|
| **B0** | Keep `(M118)`, `(M262)`, etc. |
| **B1** | Remove ` (M###)` suffixes for readability |

Example: `Front Left Pocket, Back Center (M118)` → `Front Left Pocket, Back Center`

**Est. impact:** ~12,500 cells if B1.

### 5C — Kebab-case Print Positions → human labels (optional, need mapping table)

568 rows use strings like:
`front-neck-left, left-long sleeve-front-full forearm-shoulder to sleeve`

| Option | Action |
|--------|--------|
| **C0** | Leave as-is |
| **C1** | Map known kebab patterns to nearest human equivalent (requires your sign-off on mapping) |
| **C2** | Flag in report only |

**Default proposal: C0** until mapping is agreed.

### 5D — Placeholder zero cleanup (recommended: YES)

Replace literal `0` with blank in columns that use `0` as placeholder:

| Column | Rows with `0` |
|--------|-------------:|
| Package Type | 13,867 |
| Weight | 13,423 |
| Service | 13,867 |
| Tags | 52,839 |
| Size (Dimensions) | 52,839 |

| Option | Action |
|--------|--------|
| **D1** | Clear `0` → blank in all five columns |
| **D2** | Clear only Tags + Size (Dimensions) (never had real values) |
| **D0** | Skip |

**Default proposal: D1** — `0` is not meaningful data here.

### 5E — Fill print config columns from `M01_print_config` (optional)

`M01_print_config_20260814_103010.xlsx` has:
- **M01 Print Config** — position names, default print sizes, width/height mm by mock code
- **Per-SKU Print Config** — SKU-level Printing Type, Design Type, dimensions, packaging, etc.

Join candidates: `Supplier SKU`, `Supplier Product Code`, `Custom Label` partials.

| Sub-option | Fill target |
|------------|-------------|
| **E0** | Skip config fills |
| **E1** | Fill Position 1 Name / Print Size 1 / Width 1 / Height 1 only where blank |
| **E2** | E1 + Printing Type, Design Type, Length/Width/Height (cm), Weight (g), packaging, Dispatch Days |

**Default proposal: E2** where join matches; blank-only; no overwrite.

*Exact match counts require a join scan after you approve E1/E2.*

### 5F — Infer blank Print Positions from Category (optional, low confidence)

75,336 rows have blank Print Positions. Possible defaults by Category:

| Category (examples) | Suggested default |
|--------------------|-------------------|
| T-Shirts | Front Center |
| Sweatshirts / Hoodies | Front Center |
| Headwear / Bags | Front Center or leave blank |

| Option | Action |
|--------|--------|
| **F0** | Do not infer — leave blank |
| **F1** | Set default `Front Center` for apparel categories only |

**Default proposal: F0** — inferring print position without SKU config is risky.

### 5G — Customise / Amazon Prime normalization (optional)

| Column | Current | Proposal |
|--------|---------|----------|
| Customise | blank or `Yes` | blank → `No`? or leave blank? |
| Amazon Prime | blank or `Yes` | blank → `No`? or leave blank? |

**Default proposal: leave as-is** unless you want explicit `No`.

### 5H — Final export / archive (recommended: YES)

After Phase 5:
1. Keep `Custom Label Database_Updated.xlsx` as master working copy  
2. Optionally copy to `Custom Label Database_FINAL.xlsx`  
3. Update `docs/FINDINGS.md` with final stats  

---

## Out of scope (unless you add explicitly)

- Phase 3B same-core duplicate merge (~50k labels still duplicated)  
- Phase 3 conflict report / D2 gender merges  
- Overwriting non-empty Print Positions, Category, Apparel Image  
- Inventing dimensions with no config/PE match  

---

## Execution plan (after approval)

1. Backup working file  
2. Apply approved 5A–5G in order  
3. If E1/E2 approved: join `M01_print_config` + log match rate  
4. Write `Custom Label Database_Updated.xlsx` + changelog  
5. Optional FINAL copy if 5H approved  

---

## Supervisor checklist — reply with choices

```
Phase 5: APPROVED with choices
5A Print Positions text cleanup: YES/NO
5B mock codes: B0 / B1
5C kebab-case: C0 / C1 / C2
5D clear placeholder zeros: D0 / D1 / D2
5E config fills: E0 / E1 / E2
5F infer blank Print Positions: F0 / F1
5G Customise/Amazon Prime blank -> No: YES/NO/leave
5H write FINAL copy: YES/NO
```

---

## Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Supervisor | | ☐ Approved ☐ Approved with changes ☐ Rejected | |
| Database manager (agent) | Auto | Pending supervisor | 17 Aug 2026 |

---

*See: [FINDINGS.md](FINDINGS.md), [PHASE_4_CHANGELOG.md](PHASE_4_CHANGELOG.md)*
