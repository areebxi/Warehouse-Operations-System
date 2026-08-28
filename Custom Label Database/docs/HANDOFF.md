# Custom Label Database — Agent snapshot

**Updated:** 28 August 2026 (M55 full SPC 61082)  
**Standing brief:** `AGENTS.md` (handbook) · Parent map: `../AGENTS.md`  
**Facts:** `docs/FINDINGS.md` · **Paths:** `docs/WORKSPACE.md` · **Policy:** parent `.cursor/rules/custom-label-database/` · **Chat copies:** `docs/chats/`

Prior long chats: [Custom Label DB cleanup](4455a0cd-185b-4d3e-86d5-b1c620841dd4), [shirt print sizes](59e96d0f-08d7-4ced-bb91-67d9556b29ca).

---

## Role

Warehouse Automation System Engineer on this catalog domain; user is supervisor. No production writes without **yes / do it / fill / run**. One problem at a time. Prefer CSV. **Save everything as we go** (parent CL rules + docs + `AGENTS.md`) — chat is not memory.

---

## Live now

Live catalog: `database/shared/custom_label/Custom_Label_Database.csv` — **124,762** rows × **60** cols.  
Helpers: `../support/` (`Size References.csv` **97,203** rows), `Shirts Print Sizes.csv`, `Mocks Databse.csv`).

Main filler: `python scripts/fill_from_seeds.py`. Size References reverse fill: `python scripts/fill_size_references_from_cl.py --dry-run`.

### Customise rule enforced — 28 Aug 2026 06:51

`-P{digit}-` in Custom Label ⇒ `Customise` = **Yes** (personalised; e.g. `M260-P5-*`, `N220-P3-*`). Plain mock+UID (`M55-{UID}`, `M56-{UID}`) ⇒ **blank** (not Yes). Fixed live CL: cleared **28,043** wrong `Yes`; set **2,063** missing `Yes` on `-P#-` rows. `fill_from_seeds.py` now has `--steps customise`. Backup: `backups/Custom_Label_Database_preFill_20260828_065100.csv`.

### M55 full SPC 61082 — 28 Aug 2026 05:36

Preflight unmatched `422991LG-M55-120852` / `421612LG-M55-3257` — UIDs existed as **M56** only. Policy: **all PE UIDs for SPC**. Seeded **132** more `M55-{UID}` (130 net new + 2 earlier) → **134/134** for SPC `61082` Original T; cloned from `M56-{UID}` peers; Front Center; print sizes filled. `fill_size_references_from_cl.py` +**130** keys `M55 ({UID})`. CL 124,630→**124,762**; SR 97,073→**97,203**. Backups: `backups/Custom_Label_Database_before_m55_spc61082_20260828_053615.csv`, `…_preFill_20260828_053638.csv`, `support/backups/Size_References_preFill_20260828_053655.csv`.

### Size References ← N220 — 27 Aug 2026 15:02

Appended **7** keys `N220-P3-{UID}` (**80×45**, Front Print). Also wrongly added product-code `DIAMOND` (not a SKU) — removed in fallback write. Live `Size References.csv` was locked; clean file: `support/Size_References_write_fallback.csv` (97,072→**97,071**, no DIAMOND). Backup: `support/backups/Size_References_preN220_20260827_150252.csv`.

### Apparel Images ← recent adds — 27 Aug 2026 15:09

Downloaded **84** unique PE `colour image 01` files for `iloc[124138:]` (N220 + M56 + M260-P3 + F/P) into `Apparel Images/`. 0 failed. Fixed `download_apparel_images.py` PE encoding fallback (utf-8 → cp1252/latin-1).

### Size References ← M56 batch — 27 Aug 2026 14:59

`fill_size_references_from_cl.py` appended **320** keys (`M56 ({UID})`) from the midday CL seed. 96,744 → **97,064** rows. Backup: `support/backups/Size_References_preFill_20260827_145900.csv`.  
M260-P3 UIDs already had `M260 ({UID})` in SR (all 164). F/P compound not mock+UID — still not in SR.

### M56 + M260-P3 + F/P-F8 compound — 27 Aug 2026 11:55

Appended **485** rows (`iloc[124145:]`), then `fill_from_seeds` sku+pe+suppliers+image+print. Print Positions from `Mocks Databse.csv` (`M56`/`M260` = Front Print → **Front Center**). Seed Colour/Size/GA cloned from existing `M261-*` / `M260-*` peers for the same UID.

| Block | Count | Custom Label |
|--|--|--|
| Old compound token | 1 | `F/P-F8-M-T-BLK-5XL 161121LG-B4-M-T-BLK-5XL` (F/P = Front Center + Front Left Pocket; 357×504 + 80×100) |
| M56 SPC `61082` Original T | 134 | `M56-{UID}` |
| M56 SPC `61430` Iconic 150 | 186 (2 already existed) | `M56-{UID}` → **188/188** |
| M260-P3 SPC `61033` kids VW | 164 | `M260-P3-{UID}` |

Backups: `backups/Custom_Label_Database_before_m56_m260p3_fp_20260827_115521.csv`, `…_preFill_20260827_115540.csv`.

### N220 DIAMOND helmets — 27 Aug 2026 09:12

Appended all **7** PE UIDs for SPC `DIAMOND` (Delta Plus Hi-Vis Baseball Safety Helmet) as `N220-P3-{UID}`. Design-prefix SKUs (`189381LG-…`) stay out of Custom Label. Seeds: Front Center / Yes / Standard Size / 80×45. Filled sku+pe+suppliers+image on `iloc[124138:]`.

| | |
|--|--|
| Labels | `N220-P3-55708` … `55713`, `N220-P3-99823` |
| Colours | Blue, Green, Red, Orange, White, Yellow, Black |
| Backups | `backups/Custom_Label_Database_preN220Diamond_20260827_091234.csv`, `…_preFill_20260827_091247.csv` |

### Size References reverse fill — 25 Aug 2026 20:23

Filled `support/Size References.csv` from the catalog, mock+UID only (`M123-45678` → `M123 (45678)`). Appended missing keys; blank-only on existing millimetres; Gender / Size / Printing Position / Product Code / Printing Size filled where blank. Multi-design CL slots exploded to extra SR rows.

| | |
|--|--|
| Before → after | 22,727 → **96,744** rows |
| New keys / new rows | 59,608 / 74,017 (12,719 keys with 2+ designs) |
| Existing Gender fills | 8,542 |
| Existing Printing Position, Product Code, Printing Size | 188 each |
| Untouched non-mock rows | 133 (`A4`, `BG125`, …) |
| Backup | `support/backups/Size_References_preFill_20260825_202358.csv` |

25 Aug 20:44 dry-run against the same file: **0** new keys, **0** extra design rows, **0** blank-fills left. CL CSV was not written. M251-class beanies still have blank mm (catalog Width 1 blank).

### PE taxonomy fill — 24 Aug 2026 22:15

Blank-only from `BTC Product Export.csv` (118,230 UID matches). Existing Category/Sub-Category already matched PE (0 differed). Supplier Name / SPC unchanged.

| Column | Filled | Still blank (no PE UID) |
|--------|-------:|------------------------:|
| Department | 118,230 | 5,908 |
| Sub-Department | 118,230 | 5,908 |
| Brand | 118,230 | 5,908 |
| Category | 19 | 5,908 |
| Sub-Category | 19 | 5,908 |

---

## Locked fill rules (short)

| Topic | Rule |
|-------|------|
| Category / Department | PE `Department` (title case). Blank-only first; **overwrite** when PE Department is corrected |
| Sub-Category / Sub-Department | PE `Sub Department` (title case). Blank-only first; **overwrite** when PE Sub Department is corrected |
| Brand | PE `Brand` as-is, **blank only** |
| Apparel Image | **Blanks only** — never rewrite existing names |
| NocoDB | No column-name normalization; supervisor maps uploads |
| Duplicates | Leave in place unless asked to merge/delete |
| Shirts (tee/polo/hoodie/sweat/tank, or Size maps) | **Shirts Print Sizes** (A4) → then Size References |
| Not shirts | Size References only; **never** generic mock prefix |
| Width/Height | Blank cells only unless asked to correct mm |
| Supplier SKU | Last numeric UID on Custom Label |
| Dedicated BTC/Ralawise/Absolute cols | From **Supplier Name**, blank-only |
| Tags / Size (Dimensions) | Do not fill unless asked |

Shirt Size = DB `Size`, else PE `Size` via UID. Pocket 80×100 (kids F8 `-K-` = 65×80). Women use the men print band.

---

## Current leftovers (ask before acting)

1. **BTC dedicated cols** — `fill_from_seeds.py --steps suppliers --dry-run`, then blanks only. Largest remaining fill (~83k BTC SKU / BTC Product Code on 24 Aug).
2. **Non-shirt Width 1 blanks** (~485 on 24 Aug): stickers, mugs, caps, bags, aprons, beanies, M251 / M290 / M307. Mock+UID keys are now in Size References; mm stay blank until the catalog (or an override) has Width/Height.
3. **`--all-mocks` image download** — ~189 unique remaining `M##` Apparel Image files. Does not change the CSV.
4. **`generate_from_mocks`** — ~293 guide IDs not in the DB. Pass current support CSV paths if script defaults still name old xlsx/guide files.
5. **`Tags` / `Size (Dimensions)`** — still blank; not filled from PE unless asked.
6. **24 Aug tail seed drift** (29 appended rows; duplicates kept): apostrophes in a few FOTL Gender Apparel values; `M281-P5-C800T-30-0>3` Size 3-6 Months vs 0-3; `K-H-DHR-YXS` Colour `Dark Heather` vs sibling `Dark Heather Grey`; 12/29 Print Positions blank.
7. **No PE UID** — 5,908 rows stay blank on Category / Department / Brand (iron-ons, bags without trailing UID, etc.).
8. **PE Department / Sub Department corrections** — when the product worksheet is fixed, run `--overwrite-pe-taxonomy` (dry-run first) so Category, Sub-Category, Department, and Sub-Department match the new PE. Brand stays blank-only.

Shirt print sizes on the 24 Aug block are filled, including hoodie `M138-38262`, tank `77123-BTC`, and `K-H-DHR-YXS` → 176×250.

---

## Useful commands

```text
python scripts/fill_size_references_from_cl.py --dry-run
python scripts/fill_from_seeds.py --dry-run
python scripts/fill_from_seeds.py --steps sku,pe --overwrite-pe-taxonomy --dry-run
python scripts/fill_from_seeds.py --steps print --shirts-only --w1-blank
python scripts/fill_from_seeds.py --iloc-from 124109
python scripts/generate_from_mocks.py --dry-run
python scripts/db_export.py
python scripts/db_update.py
```

If the live CSV is locked: filler writes `Custom_Label_Database_write_fallback.csv`. Close the live file, then swap.

---

## Do not reopen as a project plan

Old dated approval/changelog files are in `docs/archive/`. They refer to `Custom Label Database_Updated.xlsx` and numbered work packets. The living way of working is this file + `FINDINGS.md` + parent `.cursor/rules/custom-label-database/`.
