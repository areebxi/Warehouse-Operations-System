# Custom Label Database — Key findings

Facts and locked lessons. Snapshot numbers that can drift are dated. Policy that must not be forgotten is also in `.cursor/rules/`.

## CL warehouse stock colours 2026-09-23

Warehouse in-house stock on Custom Label is no longer “every FOTL t-shirt”. `Supply Method` = `Warehouse Stock` only when:

- FOTL t-shirt (`Category (Areeb)` T-Shirts, not a vest) and `Colour` is on that department’s list (`Mens` / `Womens` / `Kids`). Ladies = Womens. Whole colour cell. Deep Navy is not Navy. Heliconia is Womens and Kids only. Yellow and Bottle Green are Mens (Yellow also not Kids). Sports Grey is Mens and Kids, not Womens.
- Kids body styles `C800T` and `C8030T` in Black, Lemon Yellow, Light Blue, Light Pink, Red, Sports Grey, White. `C8030T` is Product Type Romper. `C8020T` is not stock.

Plain Database and Packs still use “all FOTL t-shirts” with no colour list. CL filled 2026-09-23: 63,399 Warehouse Stock, 68,367 Supplier On Demand, 458 In House Manufacture. Backup `Custom_Label_Database.bak_20260923_103520.csv`.

## Size-only acrylic SKU 2026-09-22

Listing SKU `A515` (whole Custom Label `A[4-6]` + two digits) is **always personalised** (`Customise` = Yes). `A515-PHOTO` is a different label. Sorter matches no-dash SKUs on whole Custom Label.

## Kids 14-15 Years print mm 2026-09-22

`Shirts Print Sizes.csv` has no 14-15 band. Warehouse Front Print for 14-15Y = **Small A4 (237×336)**. Do not use 3-4Y (176×250). `AGE_TO_PRINT` maps `14-15 Years` / `14-15Y` → `Small`.

---

## What this is

A warehouse **custom-label catalog**: one row per printable SKU (garment, bag, paper/iron-on, mug, cap, etc.). The supervisor seeds a few columns; scripts fill the rest from BTC Product Data, Shirts Print Sizes, and Size References.

**Live file:** `Custom_Label_Database.csv`  
**Archive Excel:** `Custom Label Database.xlsx` (not live)

As of **28 Aug 2026:** **124,762** data rows × **60** columns (+132 M55 SPC `61082` aliases cloned from M56). Original archive Excel was 127,741 × 48.

---

## Column groups

**Seed (user-filled, do not invent):**  
`Custom Label`, `Gender Apparel`, `Colour`, `Size`, `Apparel Image`, `Print Positions`, `Customise`

**Customise** (derived from Custom Label, not cloned from peers): `Yes` when the label has `-P{digit}-` **or** leading `P{digit}-` **or** a `Yes` segment (supervisor 4 Sep 2026: `Yes` in our SKU = personalised; e.g. `W101-SkyBe-O/S-Yes`). Plain mock+UID stays blank.

**Print slots (max 4):**  
`Position N Name`, `Print Size N`, `Width N (mm)`, `Height N (mm)` — N = 1..4. Slot count follows **Number of Designs** when present, else positions listed in `Print Positions`. Position **names** come from the DB `Print Positions` text, not from Size References suffixes.

**Supplier:**  
`Supplier Name`, `Supplier SKU`, `Supplier Product Code`, `Supplier Stock`  
plus dedicated **BTC / Ralawise / Absolute** SKU, Product Code, Supplier Stock.

**From BTC Product Data:**  
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

**UID extraction misses** labels with **no trailing digits:** iron-ons (`M260-P5-IronOn-A4`), C800T age tokens (`M281-P5-C800T-30-0>3`, `M281-P5-C800T-30-18-24` — the `24` is an age, not a PE UID), DTF gang sheets (`Transfer-1M-1` — the `1` is not a PE UID), bag codes (`BG-BG542-BLK-O/S-YES`), size-in-label SKUs (`K-H-DHR-YXS`, `W-T-ATTHR-M`, `W-H-BLK-M`), and `77123-BTC` (UID is the prefix; existing mocks of that garment are `M38-77123`). Do not invent a UID from the Custom Label for those. `fill_from_seeds.uid_from_custom_label` skips any label containing `C800T` or `Transfer`. Whole-label digits (`208544`) **are** a BTC UID.

**Warehouse garment codes (18 Sep 2026):** packing SKU `{design}-{M|W|K}-{T|H|…}-{colour}-{size}` → Custom Label after first dash (`75931-W-H-BLK-M` → `W-H-BLK-M`). Seed GA from the letters (`W`+`H` → `Womens-Hoodie`), colour/size from the tokens (`BLK`/`M` → Black / Medium). If the design prefix is digits **and** that UID exists in BTC Product Data, set `Supplier SKU` from the prefix (this row: 75931 = FOTL Ladies Classic Hooded Sweat 62038 Black M). Do not clone a mens-hoodie peer’s Supplier SKU onto a womens code. Size References is mock+UID only — shirts use Shirts Print Sizes.

**Gildan 5000 packing codes (20 Sep 2026):** Item SKU `{design}-5000-{colour}-{size}` → Custom Label after first dash (`128357LG-5000-NAT-S` → `5000-NAT-S`). Entire-cell match only — do **not** join to `A3-5000-…`. Fill the `5000-…` label; clone GA/colour/size/mm from the existing `A3-5000-{colour}-{size}` peer. Queue missing-size on those SKUs was catalog gap, not Size References. Apparel Image uses **T-Shirt** (not `TShirt`).

Packing PDF vs Queue: packing Step 2 matches the **company** Custom Label (`ARJ-BDg-C3-D1-ED`). DTF Des remaps that tail via New SKU Database to `5000-NAT-S`. Queue print sizes look up the remapped label. PDF garment photo does not need Width/Height mm.

PE sizes are often letters (`S`/`M`/`L`). DB sizes are often words (`Small`/`Medium`/`Large`) or age bands (`9-11 Years`). Map; do not blindly overwrite DB Size with PE Size.

`BTC_Product_Data.csv` is **not always UTF-8** (e.g. byte `0xB2`). Loaders try `utf-8`, `utf-8-sig`, `cp1252`, `latin-1` and may `replace` bad bytes.

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

Packing shirt colour tokens (Custom Label stays the token; Colour name + peer code for clone): **NAV = Navy** (peer `NVY`), **PUE = Purple** (peer `PRP`). Locked 15 Sep 2026. `add_labels._SHIRT_COLOUR_ALIAS`.

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

Format: `(Gender Apparel)-(Colour)` with spaces → `-`, letters/digits/dash only, consecutive dashes collapsed. Token is **`T-Shirt`**, not `TShirt`. New seeds/clones run `hyphen_tshirt_in_slug`. Do not bulk-rename the catalog.

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

### Grouping fill study — 9 Sep 2026

Canonical grouping cells: **`BTC Activewear`**, **`Uneek Clothing`**, **`Absolute Apparels`**. Uneek Product Data `Company` is 100% `Uneek Clothing`. Packs `BTC` was normalized to `BTC Activewear` on fill.

**Absolute Product Data** added 9 Sep 2026 (`database/shared/absolute_product_data/Absolute_Product_Data.xlsx`, 27,015 rows / 629 styles). Warehouse **only buys babysuits** from Absolute: styles `C800T` / `C8020T` / `C8030T` (48 sheet rows). Do not treat the rest of that price list as warehouse suppliers. `BZ10-Body Suit` (7) is not Absolute.

**Filled 2026-09-09** (`python scripts/fill_supplier_name.py`):

| File | BTC Activewear | Uneek Clothing | Absolute Apparels | Blank | Cells written | Backup |
|---|---:|---:|---:|---:|---:|---|
| Custom Label | 123,948 | 6,992 | 499 | 453 (in-house) | 5,430 | `Custom_Label_Database.bak_20260909_185544.csv` |
| Plain Database | 71,047 | 6,992 | 0 | 0 | 78,039 | `Plain Database.bak_20260909_185710.xlsx` |
| Packs | 38,452 | 0 | 0 | 0 | 38,452 | `Packs Database.bak_20260909_185937.xlsx` |

### Hashim #038 CL Areeb pick-list refill — 16 Sep 2026

Supervisor: refill **CL only**. Plain / Packs Areeb stay **supplier product data** (BTC / Uneek) — do not refill those two.

Supervisor deleted four blank-GA rows: `N217-P3-1D77`, `Transfer-3M`, `Transfer-1M-1`, `208544`. Then `python scripts/fill_areeb_taxonomy.py --target cl` rewrote live CSV. **131,909** rows. **0 Areeb cells changed** (old ALL-CAPS cells already matched that harvest). Backup `Custom_Label_Database.bak_20260916_083255.csv`. CL overwrite now blanks an off-list warehouse style on a future fill (`apply_areeb`). Pick-list: `database/order-grouping-sorter/taxonomy_picklists.csv`.

**Squeezed refill 2026-09-16 10:17** (supervisor **fill**). Same script `--target cl`. **131,909** rows; **131,741** rewritten; **298,338** Areeb cells; **168** already matching. **0 blank / 0 off-list** on the four Areeb columns. Backup `Custom_Label_Database.bak_20260916_101719.csv`. Live cells are Title Case; Product Type has no gender; Product Style is a named product (never `BG125L`); Department is gender only. Source `shared/taxonomy_catalog.py`. Plain / Packs not touched.

### Unmatched sorter SKUs — 17 Sep 2026

Supervisor **add**. **+8** CL rows (132,042 → **132,050**). Backup `Custom_Label_Database_preAdd_20260917_103000.csv`. `add_labels` now: `BG-BG#` colour tokens (`ClaRdOW` = Classic Red-Off White); sticker size from the `(50cmx50cm)` token (clone same-letter L, not A4 iron-on); DTF `Transfer-1M-1` / `Transfer-3M` seed GA `Only-Design` (not blank — those blank-GA rows were deleted 16 Sep). Size References unchanged (no new mock+UID; `C800T` / `A4` / `A6` already present). Skipped: N217 (supervisor later); SET5722 already Packs; 208544 already Plain (blank ship-by).

### C800T `&gt;` / `>` / `-` twins — 17 Sep 2026

Supervisor: **no decoding** on the sorter key. Fill each spelling as its own Custom Label. **+11** (132,050 → **132,061**). Backup `Custom_Label_Database_preAdd_20260917_132821.csv`. P5 now has all five ages in all three spellings. P3 0–3 and no-P 3–6 got the missing twins only. Append-only — old `M281-P5-C800T-30-0>3` Size is still **3-6 Months**.

### BTC columns held shipping data — 10 Sep 2026

`BTC SKU` / `BTC Product Code` / `BTC Supplier Stock` had copies of `Package Type` / `Weight` / `Service` (`Large Letter`, gram weights, `Royal Mail48`). Not a whole-file column shift: Ralawise/Absolute empty; other columns clean. Height mm matching Weight (pocket 80×100) is coincidence — left alone.

**Fixed** (`python scripts/fix_cl_btc_leaked_shipping.py`): 38,697 rows. Leaked cells cleared; 24 orphan Package Type / Weight / Service restored; BTC fields on those rows refilled from Supplier SKU / Product Code / Stock when present. Real UIDs (776) kept. Backup `Custom_Label_Database.bak_20260910_190412.csv`. After: BTC SKU 35,600 / BTC Product Code 35,771 (SPCs like `61082`); remaining BTC blanks are historical, not this leak.

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

`scripts/generate_from_mocks.py` + `support/Mocks Database.csv` (and PE):

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
| BTC SKU = Large Letter / Royal Mail48 | Dedicated BTC cols are UID/SPC/stock. If they look like Package Type / Weight / Service, they leaked — restore packaging cols if blank, then refill from Supplier SKU/PC/Stock |
| Live CSV locked in editor | Write fallback, swap after close |
| Category/Sub-Category withheld from PE | Reversed 24 Aug 2026: fill from PE Department / Sub Department |
| NocoDB name-normalization | Reverted; supervisor maps uploads |
| BTC SKU = Large Letter / Royal Mail48 | Dedicated BTC cols are UID/SPC/stock. If they look like Package Type / Weight / Service, they leaked — restore packaging cols if blank, then refill from Supplier SKU/PC/Stock |

---

## Working habits that matter

- **Save everything as we go** into docs and parent CL rules. Chat is not memory; do **not** copy transcripts into `docs/chats/` (`save-chats` retired).
- Backup under `backups/` before a write.
- Prefer `--dry-run` and scoped `--iloc-from` / `--shirts-only` / `--w1-blank`.
- Report every CSV change in the reply (file, labels, columns, before→after, count, backup).
- Large CSV: do not open it in Cursor/Excel to “take a look” if a script can scan it.
- Support files are **CSV** as of 24 Aug 2026 evening. Older docs that say `Print Sizes.xlsx` / `ProductExport.xlsx` / `Configuration Workbook.xlsx` mean the current CSV names above.
