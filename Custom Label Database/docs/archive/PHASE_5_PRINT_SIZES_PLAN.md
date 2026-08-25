# Phase 5 — Print Size Fill Plan

**Status:** APPROVED AND EXECUTED (17 August 2026)  
**Scope:** Fill print Width/Height (mm) and Position 1–4 Name (no other Phase 5 cleanup)  
**Working file:** `Custom Label Database_Updated.xlsx` (119,179 rows)  
**Reference files:**
- `M01_print_config_20260814_103010.xlsx` — **target output shape** (demo)
- `Configuration Workbook.xlsx` → **Size References** — primary lookup (22,727 rows)
- `Configuration Workbook.xlsx` → **Override Print Size** — 3 SKU-contains overrides
- `Print Sizes.xlsx` — apparel-size fallback table (15 size bands × 3 print types)

---

## 1. Goal

Populate the **17 print-config columns** that are currently 100% empty, matching the structure shown in `M01_print_config` → **Per-SKU Print Config**:

| Output column group | Example (from M01 demo) |
|---------------------|-------------------------|
| Print Position Code | `F4-B4-F14-F15` |
| Position 1–4 Name | `Front Top Centre`, `Back Top Centre`, … |
| Print Size 1–4 | `A4`, `A9`, `A10` |
| Width 1–4 (mm) | `210`, `210`, `37`, `26` |
| Height 1–4 (mm) | `297`, `297`, `52`, `37` |

We keep **existing DB position naming** (`Front Center`, not `Front Top Centre`) unless you instruct otherwise.

---

## 2. What the reference data actually contains

### 2.1 M01 demo — the recipe

Each SKU row is **exploded by print position**:

1. Parse `Print Positions` into an ordered list (1–4 positions).
2. For each position, set **Position N Name**, **Print Size N** (paper label), **Width/Height N (mm)**.
3. Build **Print Position Code** from position + size codes (`F4`, `B4`, …).

The demo uses `64000L` with 4 positions; most DB rows have 1–2 positions.

### 2.2 Size References — primary engine

22,727 rows keyed by several overlapping patterns:

| Row type | Key fields | Suffix meaning | Example |
|----------|------------|----------------|---------|
| **Mock config** | `SKU Value` = `M118 (102722)` | `P` = pocket/chest, `F` = front, `B` = back | M118 Men 4XL → P: 80×100, B: 297×420 |
| **Product + position** | `Product Code` + `Gender` + `Size` + `Printing Position` | same | `64000` Men Small Front Print → 237×336 |
| **Paper size** | `SKU Value` = `A4`, `A3`, `A6` | — | A4 → 210×297 |
| **Multi-design SKU** | `SKU Value` = `10AILG-M-T` | `F/B/S/S-1` | 4 positions for all-in-one products |

**Critical:** The `(M###)` codes embedded in DB `Print Positions` **directly match** mock prefixes in Size References:

| DB mock | DB Print Positions pattern | Size Ref `Printing Position` | Suffixes |
|---------|---------------------------|------------------------------|----------|
| M118 | Front Left Pocket, Back Center | Left Chest & Back Print | P + B |
| M262 | Front Left Pocket, Back Center | Left Chest & Back Print | P + B |
| M42 | Back Center, Front Left Pocket | Left Chest & Back Print | P + B |
| M180 | Front Center, Back Center | Front & Back Print | F + B |
| M263 | Front Center, Back Center | Front & Back Print | F + B |
| M195 | Front Center, Back Center | Front & Back Print | F + B |

**Same visual layout, different dimensions** — e.g. Men Medium back print:

| Mock | Pocket (P) | Back (B) | `Printing Size` |
|------|------------|----------|-----------------|
| M118 | 80×100 | **297×420** | A4 |
| M262 | 80×100 | **210×297** | A4 |
| M42 | 80×100 | **210×297** | A3 |
| M180 | 210×297 (F) | 210×297 (B) | A4 |
| M263 | **255×340** (F) | **297×420** (B) | A4 |

→ **Mock code (or an equivalent disambiguator) is mandatory** for dual-position rows that share product codes.

### 2.3 Print Sizes.xlsx — fallback

15 apparel size bands (kids + men) × 3 print types:

| Print type column | Use when position is… |
|-------------------|----------------------|
| Standard – A4 Print | Front Center / standard chest |
| Full Front/Back – A3 Print | Back Center / full back |
| Neck/Center Print | Front Left Pocket / small chest |

Example: `Men Medium` + Front Center → **267×378 mm**.

Used when Size References has no product-code match but size band is known.

### 2.4 Override Print Size

3 rules (`62310LG`, `2819ALG`, `5039ALG` → 80×100). Applied last if Custom Label / product code contains string.

---

## 3. Current database state

| Metric | Count | % |
|--------|------:|--:|
| Total rows | 119,179 | 100% |
| **Print Positions blank** | 75,336 | 63.2% |
| Print Positions filled | 43,843 | 36.8% |
| With `(M###)` mock code | 13,451 | 11.3% |
| Without mock but has positions | 30,392 | 25.5% |
| All Width/Height mm columns | **0 filled** | 0% |

**Top filled Print Positions patterns:**

| Print Positions | Rows |
|---------------|-----:|
| Front Center | 12,467 |
| Front Center, Back Center | 5,706 |
| Front Left Pocket | 4,277 |
| Front Left Pocket, Back Center (M118) | 3,760 |
| Back Center | 3,022 |
| Front Left Pocket, Back Center (M262) | 2,811 |
| Front Center, Back Center (M180) | 2,088 |
| … | … |

---

## 4. Fill algorithm (proposed)

### Step 0 — Parse positions

For each row with non-blank `Print Positions`:

1. Strip trailing ` (M###)` → store as **Mock Code** (may be empty).
2. Split on `,` or `&` → ordered list → **Position 1…N Name** (max 4).
3. Map position list to Size References **`Printing Position`** label:

| DB position combo | Size Ref `Printing Position` |
|-------------------|------------------------------|
| Front Center | Front Print |
| Back Center | Back Print |
| Front Left Pocket | Left Chest |
| Front Center, Back Center | Front & Back Print |
| Front Left Pocket, Back Center | Left Chest & Back Print |
| Back Center, Front Left Pocket | Left Chest & Back Print |

4. Map DB **Gender Apparel** → `Men` / `Women` / `Kids`; map **Size** → Size Ref format (`Extra Large` → `XL`, `2-3 Years` → `2-3Y`, etc.).

### Step 1 — Tier 1: Mock-code lookup (highest confidence)

**When:** `Print Positions` contains `(M118)` etc.

**Lookup key:** `(Mock, Gender, Size, Printing Position, Suffix)`

**Suffix order** follows position order:

| Pattern | Position 1 suffix | Position 2 suffix |
|---------|-------------------|-------------------|
| Left Chest & Back Print | P (pocket) | B (back) |
| Front & Back Print | F (front) | B (back) |

**Estimated rows:** ~13,451 → **~12,400 full matches** (mock + gender + size + position all hit Size References).

### Step 2 — Tier 2a: Single-position, no mock

**When:** One position only (Front Center / Front Left Pocket / Back Center), no mock.

**Lookup key:** `(Supplier Product Code, Gender, Size, Printing Position, Suffix)`

Search Size References where `Product Code` contains the supplier code.

| Pattern | Rows | Est. matchable |
|---------|-----:|---------------:|
| Front Center | 12,467 | ~11,500 (product code in ref) |
| Front Left Pocket | 4,277 | ~3,800 |
| Back Center | 3,022 | ~2,700 |
| **Subtotal** | **19,766** | **~18,000** |

**Fallback:** If no Size Ref hit → `Print Sizes.xlsx` by apparel size key + print type (A4 / A3 / Neck).

### Step 3 — Tier 2b: Dual-position, no mock ⚠️ ambiguous

**When:** e.g. `Front Center, Back Center` (5,706 rows) or `Front Left Pocket, Back Center` (1,909 rows) **without** `(M###)`.

**Problem:** Multiple mocks share the same product codes and position text (M118/M262/M42 or M180/M263/M195).

**Requires supervisor policy (pick one):**

| Option | Action | Risk |
|--------|--------|------|
| **2b-0** | Skip — leave mm blank, flag in report | Safest; ~7,600 rows unfilled |
| **2b-1** | Default mock per pattern (e.g. M118 for pocket+back, M180 for front+back) | Fast; ~some wrong dimensions |
| **2b-2** | Infer mock from `Supplier Product Code` subset when only one mock uses that exact code set | Medium coverage; complex rules |
| **2b-3** | Append mock code to Print Positions first (separate sub-phase), then Tier 1 | Best accuracy; needs mock inference rules |

**Recommendation:** **2b-0** for first execution + export ambiguity report; optionally **2b-3** if you want us to research mock inference from product code.

### Step 4 — Tier 3: Overrides

Apply `Override Print Size` if SKU/label contains `62310LG`, `2819ALG`, or `5039ALG` → force 80×100 on matching position.

### Step 5 — Derive Print Size label

From Size References `Printing Size` column (A4, A3, A6, A6/A3).

If blank, infer from dimensions vs known paper sizes (A4=210×297, A3=297×420, A6=105×148, etc.).

### Step 6 — Build Print Position Code

Concatenate position codes per slot (demo: `F4-B4-F14-F15`).

Requires a **position-code map** (F4=Front A4, B4=Back A4, P6=Pocket A6, …). This map is implied by M01 but not explicitly in the workbooks — we will **derive it** from unique `(Suffix, Printing Size, position name)` combos in Size References + M01 demo, and document any gaps.

### Step 7 — Blank Print Positions (75,336 rows)

**Cannot fill print mm without knowing positions.**

| Option | Action |
|--------|--------|
| **7-0** | Skip entirely (recommended for this phase) |
| **7-1** | Default single position `Front Center` for apparel categories, then Tier 2a | Fills ~60k rows but **invents** print layout |
| **7-2** | Separate future phase: infer Print Positions from Category / product type first | Correct sequencing |

**Recommendation:** **7-0** — this phase fills only rows that already have `Print Positions`.

---

## 5. Estimated coverage

| Tier | Description | Est. rows | Confidence |
|------|-------------|----------:|------------|
| 0 | Blank Print Positions → skip | 75,336 | — |
| 1 | Mock `(M###)` lookup | ~12,400 | **High** |
| 2a | Single position + Size Ref / Print Sizes | ~18,000 | **High** |
| 2b | Dual position, no mock (if 2b-0) | 0 | — |
| 2b | Dual position (if 2b-1 default mock) | ~7,600 | Medium |
| 3 | Overrides | ~0–few | High |
| **Total high-confidence** | Tiers 1 + 2a | **~30,000** | **69% of rows with positions** |
| **Total optimistic** | + dual + defaults | ~38,000–44,000 | Depends on policy |

---

## 6. Edge cases & QA

| Case | Handling |
|------|----------|
| Kebab-case positions (568 rows) | Skip or map in separate cleanup sub-step |
| `Front Center, Sleeve` (1,288) | Size Ref has sleeve suffix `S` on multi-design SKUs — needs custom 2-slot logic |
| Non-apparel (bags, headwear, mugs) | Size References has bag codes (BG125, QD442) — use product-code rows, not Print Sizes |
| Size `A4` / `A5` as product size | Direct paper-size lookup in Size References |
| Kids sizes `12-14 Years`, `14-15 Years` | Map to Size Ref `14-15Y` |
| Rows with empty Supplier Product Code | Fall back to Print Sizes.xlsx only |
| Dimension conflicts on join | Log to conflict report; do not overwrite |

**Validation checks after fill:**
1. Width/Height > 0 and Width ≤ Height for portrait prints (flag exceptions).
2. Position count matches Number of Designs in Size References.
3. Spot-check 20 rows against M01 demo pattern (64000L-style products).
4. Compare filled mm to `Print Sizes.xlsx` for Front Center-only rows — should align within rounding.

---

## 7. Execution steps (after approval)

1. Backup → `Custom Label Database_Updated_prePhase5Print_*.xlsx`
2. Build in-memory lookup indexes from Size References + Print Sizes
3. Run Tier 1 → 2a → 2b (per policy) → 3 on **blank-only** cells
4. Write changelog with per-tier counts + unfillable row export
5. Update `FINDINGS.md`

**No row deletes. No overwrites of non-empty mm fields.**

---

## 8. Supervisor decisions needed

Reply with choices:

```
Phase 5 Print Sizes: APPROVED with choices

Primary scope:
  Fill only rows WITH Print Positions: YES/NO

Tier 2b (dual position, no mock):
  2b-0 skip + report / 2b-1 default mock / 2b-2 infer / 2b-3 fix positions first

Tier 2b-1 defaults (if 2b-1):
  Pocket+Back default mock: M118 / M262 / other
  Front+Back default mock: M180 / M263 / other

Blank Print Positions (75k rows):
  7-0 skip / 7-1 default Front Center / 7-2 defer

Also populate:
  Print Position Code: YES/NO
  Position 1-4 Name: YES/NO (split from Print Positions)
  Print Size 1-4 labels: YES/NO

Position naming:
  Keep DB names (Front Center): YES
  Use M01 names (Front Top Centre): NO

Overrides (62310LG etc.): YES/NO
```

---

## 9. Sign-off

| Role | Name | Decision | Date |
|------|------|----------|------|
| Supervisor | | ☐ Approved ☐ Approved with changes ☐ Rejected | |
| Database manager (agent) | Auto | Plan submitted | 17 Aug 2026 |

---

*Analysis scripts: `scripts/print_sizes_analysis.py`, `print_sizes_simulation.py`, `print_sizes_mock_analysis.py`*
