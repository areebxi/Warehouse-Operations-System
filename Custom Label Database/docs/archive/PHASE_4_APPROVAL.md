# Phase 4 — Approval Request

**Status:** APPROVED AND EXECUTED (17 August 2026)  
**Working file:** `Custom Label Database_Updated.xlsx`  
**Changelog:** `docs/PHASE_4_CHANGELOG.md`

**Supervisor choices:** 4A YES · 4B YES · 4C slug (Gender+Colour) · 4D YES · 4E YES · 4F F1 · 4G G1

---

## Goal

Fill **empty** fields in the working database using ProductExport, joined primarily on:

`Supplier SKU` → ProductExport `UID`

No row deletes. No overwrite of already-filled cells (unless you opt in below).

---

## Join coverage (current)

| Metric | Count |
|--------|------:|
| Rows with Supplier SKU matching PE UID | **72,387** |
| Unique matched SKUs | 1,470 |
| Blank Supplier SKU | 46,692 |
| SKU present but no PE match | 100 |
| Blank SKU but Custom Label suffix (`-12345`) matches PE UID | **35,082** |

---

## What PE can fill (matched via Supplier SKU)

| CLD field (now) | PE source | Fillable now | Notes |
|-----------------|-----------|-------------:|-------|
| Category (0% filled) | Department | **72,387** | e.g. T-SHIRTS, SWEATSHIRTS AND HOODIES |
| Sub-Category (0% filled) | Sub Department | **72,387** | e.g. MENS SHORT SLEEVE T-SHIRT |
| Apparel Image (blank only) | image_url_high_res | **290** | only where image empty |
| Supplier Name (blank + matched) | constant `BTC Activewear` | **35,717** | PE is BTC catalog |
| Supplier Product Code (blank) | SPC | **72,097** | style/product code |
| Colour | Colour Name | 0 | already filled on matched rows |
| Size | Size | 0 | already filled; PE uses letters anyway |

### Top PE Department values (among matched rows)

| Department | Rows |
|------------|-----:|
| T-SHIRTS | 49,764 |
| SWEATSHIRTS AND HOODIES | 21,183 |
| Bags | 1,186 |
| HEADWEAR | 194 |
| POLO SHIRTS | 58 |

---

## In scope — choose each

### 4A — Category ← PE Department (recommended: YES)

Fill blank `Category` where Supplier SKU matches PE.

### 4B — Sub-Category ← PE Sub Department (recommended: YES)

Fill blank `Sub-Category` where Supplier SKU matches PE.

### 4C — Apparel Image ← PE high-res URL (recommended: YES)

Fill only where `Apparel Image` is blank and PE has a URL (~290).

### 4D — Supplier Name ← `BTC Activewear` for matched blanks (recommended: YES)

Only where Supplier SKU matches PE and Supplier Name is blank (~35,717).  
Does **not** change rows that already say `BTC Activewear`.

### 4E — Supplier Product Code ← PE SPC (recommended: YES)

Fill blank `Supplier Product Code` from PE `SPC` (~72,097).

### 4F — Secondary join via Custom Label suffix (optional: need pick)

When `Supplier SKU` is blank but Custom Label ends in `-NNNNN` and that number is a PE UID:

| Sub-option | Action |
|------------|--------|
| **F0** | Skip (default) |
| **F1** | Fill Category / Sub-Category / blank image / SPC only (same as A–C,E) |
| **F2** | F1 + also set `Supplier SKU` from the suffix + blank Supplier Name → BTC |

**Est. extra rows if F1/F2:** up to ~35,082

### 4G — Title-case / normalize PE department text (optional)

| Option | Example |
|--------|---------|
| **G0** Keep PE as-is | `T-SHIRTS`, `MENS SHORT SLEEVE T-SHIRT` |
| **G1** Title Case | `T-Shirts`, `Mens Short Sleeve T-Shirt` |

Default proposal: **G0** (preserve supplier wording).

---

## Out of scope

- Overwriting non-empty Category / Colour / Size / Gender Apparel from PE  
- Same-core duplicate merge (declined in Phase 3 as 3B)  
- Print position / packaging / weight / dispatch fields → Phase 5  
- Inventing data for the ~100 SKUs with no PE match  

---

## Execution plan (after approval)

1. Backup working file  
2. Join PE on approved keys  
3. Fill only blank cells per approved 4A–4G  
4. Write `Custom Label Database_Updated.xlsx` + changelog  
5. Stop for Phase 5 approval  

---

## Supervisor checklist — reply with choices

```
Phase 4: APPROVED with choices
4A Category from Department: YES/NO
4B Sub-Category from Sub Department: YES/NO
4C blank Apparel Image from PE URL: YES/NO
4D blank Supplier Name -> BTC Activewear (matched): YES/NO
4E blank Supplier Product Code from SPC: YES/NO
4F suffix join: F0 / F1 / F2
4G department text: G0 / G1
```

---

## Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Supervisor | | Approved: 4A-4E YES, 4C slug, 4F F1, 4G G1 | 17 Aug 2026 |
| Database manager (agent) | Auto | Executed — see `PHASE_4_CHANGELOG.md` | 17 Aug 2026 |

---

*See: [FINDINGS.md](FINDINGS.md), [PHASE_3_CHANGELOG.md](PHASE_3_CHANGELOG.md)*
