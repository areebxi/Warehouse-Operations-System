# Custom Label Database — Key findings

Facts and locked lessons. Snapshot numbers that can drift are dated. Policy that must not be forgotten is also in `.cursor/rules/`.

---

## What this is

A warehouse **custom-label catalog**: one row per printable SKU (garment, bag, paper/iron-on, mug, cap, etc.). The supervisor seeds a few columns; scripts fill the rest from Product Export, Shirts Print Sizes, and Size References.

**Live file:** `Custom_Label_Database.csv`  
**Archive Excel:** `Custom Label Database.xlsx` (not live)

As of **28 Aug 2026:** **124,762** data rows × **60** columns (+132 M55 SPC `61082` aliases cloned from M56). Original archive Excel was 127,741 × 48.

---

## Column groups

**Seed (user-filled, do not invent):**  
`Custom Label`, `Gender Apparel`, `Colour`, `Size`, `Apparel Image`, `Print Positions`, `Customise`

**Print slots (max 4):**  
`Position N Name`, `Print Size N`, `Width N (mm)`, `Height N (mm)` — N = 1..4. Slot count follows **Number of Designs** when present, else positions listed in `Print Positions`. Position **names** come from the DB `Print Positions` text, not from Size References suffixes.

**Supplier:**  
`Supplier Name`, `Supplier SKU`, `Supplier Product Code`, `Supplier Stock`  
plus dedicated **BTC / Ralawise / Absolute** SKU, Product Code, Supplier Stock.

**From Product Export:**  
`Category` and `Department` ← PE `Department` (title case).  
`Sub-Category` and `Sub-Department` ← PE `Sub Department` (title case).  
`Brand` ← PE `Brand` (as-is, blank-only).

First fill is blank-only. Some PE Department / Sub Department rows are wrong; when those are corrected on the product worksheet, **overwrite** the four taxonomy columns on matching UIDs (`--overwrite-pe-taxonomy`). Do not keep stale DB values just because the cells are already filled.

**Do not fill unless asked:** `Tags`, `Size (Dimensions)`.

`id` is for NocoDB round-trip. Blank `id` = new insert. Keep the column.

---

## Join keys

| Join | Use |
|------|-----|
| Last **numeric** suffix of `Custom Label` → PE `UID` | Primary. `M260-214332` → `214332`. `M261-P4-24786` → `24786`. |
| `Supplier SKU` → PE `UID` | Same UID when already filled. |
| `Supplier Product Code` → PE `SPC` | Weak overlap historically; not the main join. |

**UID extraction misses** labels with **no trailing digits:** iron-ons (`M260-P5-IronOn-A4`), C800T age tokens (`M281-P5-C800T-30-0>3`), bag codes (`BG-BG542-BLK-O/S-YES`), size-in-label SKUs (`K-H-DHR-YXS`, `W-T-ATTHR-M`), and `77123-BTC` (UID is the prefix; existing mocks of that garment are `M38-77123`). Do not invent a UID for those.

PE sizes are often letters (`S`/`M`/`L`). DB sizes are often words (`Small`/`Medium`/`Large`) or age bands (`9-11 Years`). Map; do not blindly overwrite DB Size with PE Size.

`BTC Product Export.csv` is **not always UTF-8** (e.g. byte `0xB2`). Loaders try `utf-8`, `utf-8-sig`, `cp1252`, `latin-1` and may `replace` bad bytes.

---

## Duplicates

Duplicate **Custom Labels are normal** in this file (same label, extra copies, sometimes richer vs seed-only). Exact full-row duplicates were stripped once from the original Excel (~8.4k, then ~168 more). **Same-label different-identity rows were not auto-merged** (supervisor declined that pass).

On 24 Aug 2026, 29 rows were appended: 13 truly new labels, 16 copies of labels already in the file (`M51-37686` pasted twice in the tail). Supervisor: **leave duplicates in place** and fill other columns.

Do not merge, delete, or “dedupe” unless asked.

Colour-only “conflicts” are often abbreviation vs full name (`Dark Heather` vs `Dark Heather Grey`). Navy / Royal families were **left as distinct colours** on purpose.

---

## Size systems

Three systems coexist and are all valid:

- Words: `Small`, `Medium`, `Large`, `Extra Large`, `Extra Small`
- Letters: `S`, `M`, `L`, `XL`, `XS`, `2XL`…
- Age / youth: `3-4 Years`, `YXS`, `12-13 Years`, `3-6 Months`, …

Cleanup already applied on the old Excel: `_x000D_` / CR-LF stripped; age shorts like `9-11Y` → `9-11 Years`; typos `Meduim` / `Wodium` → `Medium`. Letter→word mapping was applied on that pass for some rows; both forms still appear.

**Women use the Men print-size band** in Shirts Print Sizes.

---

## Colour

Typos already corrected on the old Excel (do not re-run blindly): `Fuschia`→`Fuchsia`, `Colbalt Blue`→`Cobalt Blue`, `Sport Grey`→`Sports Grey`, `Light-Pink`→`Light Pink`. Approved expands: `Dark Heather`→`Dark Heather Grey`, `Azure`→`Azure Blue` (not applied to every later paste).

Navy / Royal variants (`Navy` vs `Navy Blue` vs `French Navy`, etc.) stay as-is unless asked.

New-row seed drift (24 Aug tail, not auto-fixed): `K-H-DHR-YXS` Colour `Dark Heather` while sibling K-H-DHR sizes use `Dark Heather Grey`. Apostrophes in Gender Apparel on a few FOTL rows (`Fruit Of The Loom Men's Iconic 150 T`) while siblings use `FOTL Mens Iconic 150 T`. `M281-P5-C800T-30-0>3` Size was **3-6 Months** (label and cousins say 0-3).

---

## Gender Apparel

Two styles mixed:

1. Legacy category-like: `Mens-T-Shirt`, `Kids-Hoodie`
2. Current: `{Brand Code} {Description}` from PE (e.g. `GILDAN Heavy Cotton Adult T-Shirt`)

No special characters in seed columns (`™`, `&`); dash and commas OK. `Men's`→`Mens` style flattening is used on generated mocks.

---

## Print sizes (critical)

**SKU source is always `Custom Label`.**

### Shirts (all kinds)

Tee, t-shirt, polo, hoodie, sweatshirt, tank — **and** any row whose `Size` maps to the shirt table (`Small` / `Large` / `YXS` / `12-13 Years`, …), unless Gender Apparel is clearly not a shirt (bag, tote, apron, beanie, hat, cap, iron-on, romper, bodysuit, waistcoat, sticker, mug, mask).

1. **`support/Shirts Print Sizes.csv` first** — Standard **A4** for Front/Back (A3 column only if that paper is selected; missing → A4). Size = DB `Size`, else PE `Size` via UID.
2. **Then `support/Size References.csv`** if the band does not map, or for extra positions / paper / an **exact** `M## (UID)` row.

Pocket / left chest → **80×100**. Kids F8 (`-K-` in the label) → **65×80**. Front and Back use the **same** millimetres.

### Not shirts

Bags, paper/iron-on, stickers, mugs, caps, beanies, aprons, masks: **Size References only**.

**Never** take millimetres from a **generic mock prefix** (`M96` with no UID). That is how new `M96-138334` was wrongly set to **318×450** (3XL A4 / Large A3) instead of **250×353** (12-13 Years/YXL A4). Size References is not a garment-size table.

Fill **blank** Width/Height only, unless the supervisor asks to correct wrong mm.

Override Print Size used to live on a Configuration Workbook **xlsx** sheet. Current Size References **CSV has no override sheet**, so contain-match overrides currently load **empty**.

### Known millimetre corrections (24 Aug 2026)

| Custom Label | Was | Should be / is | Source |
|--------------|-----|----------------|--------|
| `M96-138334` (new copy) | 318×450 | **250×353** | 12-13 Years/YXL A4 |
| `W-T-ATTHR-M` | 270×320 | **267×378** | Medium A4 |
| `W-T-ATTHR-2XL` | 271×313 | **267×378** | 2XL A4 |
| `M66-M-T-NAT-2XL` | 271×313 | **267×378** | 2XL A4 |
| `M-T-NAVBE-3XL-Yes` | 320×370 | **318×450** | 3XL A4 |
| `K-H-DHR-YXS` | 180×150 (SR `K-H (YXS)`) | **176×250** | 3-4 Years/YXS A4 |
| `M138-38262` (new copy, hoodie Large via PE 38262) | blank | **267×378** | Large A4 |
| `77123-BTC` (tank 2XL) | blank | **267×378** | 2XL A4 |

Original `M96-138334` was already 250×353. ~10.9k shirts with an **exact** `M## (UID)` Size References row were left as-is during that correction.

### Remaining blanks

After shirt fills, **Width 1 still blank** on hundreds of **non-shirt** rows (stickers, mugs, caps, bags, aprons, beanies, leftover mocks M251 / M290 / M307). Those need a Size References hit or an explicit override — not a shirt-table fill.

### Size References reverse fill (25 Aug 2026)

Supervisor: fill Size References from the live catalog; mock+UID only; other columns too. Script: `scripts/fill_size_references_from_cl.py`. Live helper path: `support/Size References.csv`.

| Rule | Choice |
|------|--------|
| Key | Custom Label `M123-45678` → SKU Value `M123 (45678)` |
| Skip | Non-mock codes, iron-on/hybrids (`M260-P5-…`), bare `M96` |
| Existing mm | Blank-only — never overwrite Size Width/Height |
| New keys | Append; explode Width/Height 1–4 into extra rows + Suffix |
| Other cols | Gender, Size, Printing Position, Product Code, Printing Size, Number of Designs |
| Product Code / Printing Size | Mocks guide for that `M##`, else catalog |

**25 Aug write:** 22,727 → **96,744** rows. Backup: `support/backups/Size_References_preFill_20260825_202358.csv`. 20:44 dry-run at the same path: no remaining mock+UID work.

| Change | Count |
|--------|------:|
| New mock+UID keys | 59,608 |
| New rows (incl. 12,719 multi-design keys) | 74,017 |
| Existing Gender blank-fill | 8,542 |
| Existing Printing Position / Product Code / Printing Size | 188 each |
| Non-mock SR rows left alone | 133 |

Spot checks: `M118 (102722)` still 80×100 P / 297×420 B; `M96 (138334)` 250×353 Kids 12-13Y; `M251 (169164)` appended with blank mm (beanie still has no Width 1 on CL). One duplicate-label seed `M38 (77098)` was corrected Men/2Xl → Women/2XL.

Non-apparel pocket rename (done once, 58 rows): bags / backpacks / keyrings only, `Front Left Pocket` → `Pocket`.

---

## Apparel Image

Format: `(Gender Apparel)-(Colour)` with spaces → `-`, letters/digits/dash only, consecutive dashes collapsed.

**Fill blanks only. Never rewrite an existing name.**

A past bulk pass rewrote **~34,755** Apparel Image cells. The true pre-change backup was **deleted**. Agreed fallback: restore from `support/Workbook.xlsx` column `Picture Name` (23 Aug 2026: 64,848 matched, 6,913 changed, 369 sanitized). That is **not** a perfect undo.

Download files with `scripts/download_apparel_images.py` using PE **`colour image 01`**, saved as the **exact** DB Apparel Image filename. Legacy `download-images.ps1` names from Brand-Description-Colour and does **not** match DB names.

Iron-on mock rows with no numeric UID have no PE image (e.g. `DTF-IronOn-A4-Iron-On-Sticker`). `--all-mocks` still needed for remaining unique `M##` filenames (on the order of **~189** on 24 Aug 2026).

---

## Supplier columns

Dedicated BTC / Ralawise / Absolute columns copy from **Supplier Name** (keyword), not from SKU:

- Supplier SKU → `{Supplier} SKU`
- Supplier Product Code → `{Supplier} Product Code`
- Stock stays blank if the source is empty

On 24 Aug 2026: tens of thousands of rows named BTC Activewear still had **blank BTC SKU / BTC Product Code**. Script exists (`fill_from_seeds.py --steps suppliers`); **ask before** a whole-file fill. Ralawise / Absolute named rows were **0**.

---

## Design-prefix SKUs → Custom Label (N220 helmets)

Packing Item SKUs like `189381LG-N220-P3-55709` / `189382LG-N220-P3-55712` are **design-id + Custom Label**. Store the **tail only** in CL (`N220-P3-{UID}`), not the `digitsLG-` prefix — same garment serves multiple designs.

| Fact | Value |
|------|--------|
| PE SPC | `DIAMOND` |
| Product | Delta Plus Hi-Vis Baseball Safety Helmet |
| UIDs (all 7) | `55708` Blue, `55709` Green, `55710` Red, `55711` Orange, `55712` White, `55713` Yellow, `99823` Black |
| Custom Label | `N220-P3-{UID}` |
| Gender Apparel | `DELTA Hi-Vis Baseball Safety Helmet` |
| Size | `Standard Size` (PE `O/s`) |
| Print Positions / Customise | `Front Center` / `Yes` (supervisor: token `P3` here ≠ garment mock Front+Back) |
| Print mm | Cap-style **80×45** (no Size References `N220` row; not a shirt) |
| PE taxonomy | Headwear / Safety Headwear; Brand Delta Plus; BTC Product Code `DIAMOND` |

Added **27 Aug 2026** (iloc 124138–124144). Backups: `Custom_Label_Database_preN220Diamond_20260827_091234.csv`, then `…_preFill_20260827_091247.csv`.

When a supervisor asks for a few UIDs of a BTC style, **prefer adding every PE UID for that SPC** unless they scope otherwise.

---

## Mocks generator

`scripts/generate_from_mocks.py` + `support/Mocks Databse.csv` (and PE):

- Custom Label = `{Pasting Mocks ID}-{UID}` (e.g. `M260-214332`)
- Fill **only** the seed columns; skip a mock if any seed cell cannot be filled
- Skip mock IDs **already present** in the DB
- Then run `fill_from_seeds.py`

Script **defaults** may still point at old names (`ProductExport.xlsx`, `14-01-Mocks Database Guide(…).csv`). Pass current `support/` CSV paths if those defaults 404. On 24 Aug 2026, **~293** guide IDs were not yet in the DB.

---

## NocoDB / Postgres

- Table `Custom_Label_Database`; file `Custom_Label_Database.csv`
- `DELETE_ROWS_MISSING_FROM_CSV = True` in `db_update.py` (50% mass-delete safety unless forced)
- Credentials live in those scripts (user-owned). Do not copy them into docs or chat dumps.
- **Do not** add column-name normalization helpers for upload.

---

## Incidents (do not repeat)

| What | Lesson |
|------|--------|
| Apparel Image bulk rewrite | Blanks only; never overwrite names |
| Generic `M96` Size References match | Never use mock prefix without this UID |
| Hoodie/sweat/tank skipped as “not shirts” | All shirt kinds + mappable Size → Print Sizes first |
| Live CSV locked in editor | Write fallback, swap after close |
| Category/Sub-Category withheld from PE | Reversed 24 Aug 2026: fill from PE Department / Sub Department |
| NocoDB name-normalization | Reverted; supervisor maps uploads |

---

## Working habits that matter

- **Save everything as we go** in this folder, including a copy of the chat transcript in `docs/chats/`. Chat UI is not memory; a new computer still starts a new thread, but can read the copies.
- Backup under `backups/` before a write.
- Prefer `--dry-run` and scoped `--iloc-from` / `--shirts-only` / `--w1-blank`.
- Report every CSV change in the reply (file, labels, columns, before→after, count, backup).
- Large CSV: do not open it in Cursor/Excel to “take a look” if a script can scan it.
- Support files are **CSV** as of 24 Aug 2026 evening. Older docs that say `Print Sizes.xlsx` / `ProductExport.xlsx` / `Configuration Workbook.xlsx` mean the current CSV names above.
