# Order grouping — locked decisions

Living notes. Sources: **ShipStation**; **CL DB** (`database/shared/custom_label/Custom_Label_Database.csv`); **Plain Database** (`database/shared/plain/Plain Database.xlsx`); **Packs Database** (`database/shared/packs/Packs Database.xlsx`); **configuration**.
A **grouping run** only **reads** the three catalogs (it does not overwrite them). **Step 2 fill** may write all three after supervisor **fill / run**. Backup first.

**Sequence (do not skip):** (1) lock **grouping logic** — **CEO approved 2026-09-08** → (2) catalog **fill on all three databases** (CL + Plain + Packs) — **done 2026-09-09** → (3) **build** **Order Grouping Sorter** (new app, outside Packing) → (4) **dry-run** on live `awaiting_shipment` (counts + process names, **no** Packing Input write) until supervisor **run**. Do not write Input CSVs until **run**.

**CEO review table:** `order-grouping-criteria.csv` — one row per criterion. Edit that file to correct anything.

## Dimensions vs example values

The screenshot / Graph header row is the **axis list** (what we can split on), in order:

`order-status` → `ship-by-date` → `shift` → `product-finish` → `order-source` → `design-grouping` → `shipping-service` → `printing-method` → `customized` → `customization-type` → `print-size` → `print-position` → `supply-method` → `supplier` → `package-type` → `category` → `product-type` → `product-style` → `department` → `brand` → `size` → `color`

Sheet spellings `customized` / `customization-type` / `color` = our `customised` / `customisation-type` / `colour` (CL uses `Customise`, `Colour`).

**Values on the Graph and Grouping Data are examples only**, not a closed list. There will be more (other supply methods, channels, printing methods, brands, …). When a flag is `1` (or a 30-chain step fires), split on **whatever definite values exist** in ShipStation / CL / config at run time. A missing Graph branch does **not** mean that value is off.

**In-house manufacturer** = we **make it in the warehouse**. Locked cell: **`In House Manufacture`** = iron-on **or sticker** (Custom Label SKU or Gender Apparel contains `iron on` / `ironon` / `iron-on` / `sticker`). **Plain cannot be in-house** (plain is not made here). If a line looks plain but supply-method is in-house → **`unmatched`**. Printed can be in-house. Plain `Supply Method` is still flag `1`: `Warehouse Stock` or `Supplier On Demand` (never In House Manufacture on Plain/Packs).

## Definite match / unmatched

Grouping **never guesses**. A field is used only when the value is definite. If a required field is missing or blank, that order is **unmatched**.

| | Meaning |
|---|---|
| **unmatched** | One process file named **`unmatched`**. Floor processes it **manually this run**. Then we **investigate why** it failed a definite match and **tighten the rule or catalog** so the next run can match it. Not mixed into `today-…` piles. |
| Same order | If any line fails a required match, the **whole order** goes to `unmatched`. |

**SKU match keys (entire-cell, casefold).** Each database uses **one** key rule — no numeric stripping, no cross-key guessing.

| Source | File | Key from Item SKU | Example Item SKU | Key matched in DB |
|---|---|---|---|---|
| Custom Label | `database/shared/custom_label/Custom_Label_Database.csv` | **After first dash** | `77989LG-M-T-BLK-M` | `M-T-BLK-M` → `Custom Label` column |
| Plain Database | `database/shared/plain/Plain Database.xlsx` sheet `Sheet1` | **Till last dash** | `1243-1` | `1243` → column **SKU** |
| Packs | `database/shared/packs/Packs Database.xlsx` sheet `01-Database` | **Whole SKU** | `SET4741` | `SET4741` → **Channel Child SKU** |

**Plain vs printed:** finish gate (with explicit SKU override). If Item SKU contains `plain` / `plainlg` → plain. Otherwise finish comes from database hit: **CL** matches `Custom Label` after the first dash → printed; **Plain Database** matches `SKU` till the last dash (or whole SKU) → plain; **Packs** matches whole SKU (`Channel Child SKU`) → plain. If none hit → `unmatched`. (These are entire-cell key matches; no numeric-prefix stripping for plain.)

**Attribute source when a line needs catalog fields:** Packs if whole-SKU hits → else CL if after-first-dash hits → else Plain Database if till-last-dash hits. Unmatched for that line’s required fields only if **none** of the three hit.

SET / pack orders (`SET*`) match **Packs** on whole SKU. Checked 2026-09-03: `SET4741`, `SET15007`, `SET5733` are in Packs Database.

**Blank `shipByDate`:** unmatched (not today, not “wait for a later ship-by”). Live 2026-09-03: 17 orders.

**Future `shipByDate`:** not unmatched — date is known. **Today/overdue fill the shift cap first.** If that pool is **under** the cap, **add future ship-by orders** until the cap is reached. Only leftover future (after all shift caps are full) waits for a later run.

**Intake:** **ShipStation `awaiting_shipment` only.** No supervisor CSV/file — ShipStation CSV export has no tags. Order of gates: skip `post-order-designs` → resend tag (wins even if ship-by is blank) → blank ship-by → `unmatched` → fill shift caps with today/overdue **lines**, then future if still under cap → split remaining. A later split with a blank required catalog field also sends the whole order to `unmatched`.

Until catalog columns are filled (e.g. `Printing Type`), printed lines will go to `unmatched` in a test run. That is expected. Catalog fill is step 2 **on all three databases**. Unmatched is a **feedback loop**, not a dump: investigate → tighten logic/catalog → next run should match.

Live check 2026-09-03: 191 `awaiting_shipment` orders. **CL-only** match ~94% of units. SET SKUs that missed CL (`SET4741`, `SET15007`, `SET5733`) **are** in Packs Database. `Printing Type` empty. No mixed plain+printed orders in that pool.

## Process vs process number

| | Meaning |
|---|---|
| **Process** | One output file / one pile. Filename follows **Graph flags** (plain and printed names differ). Special filenames: **`resend`**, **`unmatched`**. |
| **Process number** | The `-1`, `-2` after that name (colour 3+ groups and parts). Same customer order shares the same `-N`. |
| **Item** | Line inside that `-N`: `Item 1`, `Item 2`, … |

On the packing line: `Process today-plain-own-…-1 Item 1` then `…-1 Item 2` then `…-2 Item 1`.

Same customer order **always** stays in one process file. If one order has **plain and printed** lines → whole order goes **printed** (printed-wins).

## Flags

| Flag | Meaning |
|---|---|
| `1` | Split into **new process files**. Value goes in the process name. |
| `x` | Do not split. Name slot is `x`. |
| `0` | Off **now** (same as `x` at run time). Stays in config so CEO can set `1` later. |
| `30` | On the taxonomy chain only: if that bucket has **≥ 30** units, **new process file**. |
| Colour **3+** | **Qty (units)**, not order count. ≥ 3 units of that colour → **own process numbers inside** the same process. One order with qty 3 qualifies. Does not split an order. Sheet note said “orders”; supervisor locked **qty**. |
| Parts | **Process numbers inside** the same process, not new files. Same idea as Packing PDF parts: **50 units per part** (Packing writes `_Part N.pdf` at 50 pages; one page = one unit). CEO graph bands `0–30` / `31–60` / `61–90` are **replaced** by this 50 threshold. |

**Taxonomy chain (new process files at 30):** category → product-type → product-style → department → brand → size → colour.

If a branch on the CEO sheet **does not draw that chain all the way to colour**, that is **shorthand** (save writing). It still uses the same tail as the sibling branch that *was* written out. Missing cells do **not** mean “stop splitting here.”

Plain vs printed tails differ where they *are* written (plain: all `30`; printed: department `1`, brand `0`, size `1`, colour `30`).

**Left-side dimensions (new process files when `1`):** shift, product-finish, order-source, design-grouping, shipping-service (prime / non-prime), printing-method, customised, customisation-type, print-size, print-position, supply-method, supplier, package-type. **`shift` is on in the filename** (slot `1st` / `2nd` / `3rd`, Graph order after ship-by-date) **and** is the Packing Input folder (`1st Shift` / `2nd Shift` / `3rd Shift`).

**Plain vs printed flags (Graph, locked):**

| Slot | Plain | Printed warehouse-stock | Printed supplier-on-demand |
|---|---|---|---|
| shift | 1 | 1 | 1 |
| order-source | 1 | 1 | inherits |
| design-grouping | x | 0 | |
| shipping-service | 1 | 1 | |
| printing-method | x | 1 | |
| customised | x | 1 | |
| customisation-type | x | x | |
| print-size / print-position | x | 0 | |
| supply-method | 1 | 1 | 1 |
| supplier | 1 | x | 1 |
| package-type | 0 | 0 | 0 |

The CEO example string `today-plain-all_channels-x-prime-dtf-readymade-x` is **stale** vs these flags. Names follow the table. Off slots are `x`. 30-chain values append only when that level actually splits.

`Grouping Data` **Usage** column:

- **grouping** = sorter uses it to choose a process file.
- **display** = print that field on the **packing PDF for that order’s page**. Display does **not** mean “skip grouping.” A field can be both (Graph flag `1` + display on the PDF).
- Display-only examples: blank product image, print-area template, product description, packaging image, weight, dimensions, customer/internal notes.

Catalog `Amazon Prime` is PO/inventory, not grouping.

**Why plain processes exist for stock:** each process pile is how stock is **ordered**. Packs vs Gildan T-shirts happen on the **30-chain** (product type / brand), not package-type.

## Locked fields

| Field | Split | Source | Detail |
|---|---|---|---|
| today | process files | **ShipStation** `shipByDate` | **Today = run date or overdue** (`shipBy <= run date`). **Blank ship-by → `unmatched`**. Future is **not** skipped: it fills leftover shift-cap **lines** after today/overdue. Filename **first slot:** literal **`today`** for run-date/overdue; future-fill orders use the actual **`YYYY-MM-DD`**. |
| unmatched | process files | any required field with no definite value | Filename **`unmatched` only**. Whole order. Includes blank ship-by and blank required CL fields when that split is on. Manual this run; then investigate and tighten so the next run matches. |
| shipping-service (prime) | process files | **ShipStation** tag `Amazon Prime Order` | Tag → `prime`. No tag → `non-prime`. Do **not** use CL `Amazon Prime` (that is product-level, for PO). Live 2026-09-03: 12 Prime orders, all `amazon_shipping`. |
| order source | process files | **ShipStation** store (and later tags) + **configuration** peel-off list | Flag `1`. Unlisted → **`own`**. **Amazon is not its own channel**. First peel-off: store **MAS Clothing** → process-name slot **`fawad`**. More channels later. `daataa-direct` on the Graph is a CEO example, not a live peel until listed. |
| product finish | process files | **DB finish gate + plain override** | **Plain override:** if Item SKU contains `plain` / `plainlg` → plain (finish locked). Otherwise finish comes from database hit: **CL** (match `Custom Label` after **first dash**) → printed; **Plain Database** (match `SKU` till **last dash**, or whole SKU) → plain; **Packs** (match whole SKU → Channel Child SKU) → plain. If none hit → `unmatched`. We assume catalog curation keeps printed items in CL and plain items in Plain/Packs. |
| mixed plain+printed | one process (printed-wins) | same customer order | Whole order goes to the **printed** process. Never two files. None in the 2026-09-03 pool. |
| customised vs ready-made | process files (**printed only**, flag `1`) | **CL DB** `Customise` | Printed + `Yes` → customised. Other printed → ready-made. Plain slot is `x`. |
| printing method | process files (**printed only**, flag `1`) | **CL DB** `Printing Type` | Split on cell value. Locked 2026-09-09: **`DTF`** default; **`Sublimation`** = mugs. Mock `M##` → `Mocks Databse.csv` Printing-Type when DTF/Sublimation; else mug (`Category (Areeb)` Mugs or Gender Apparel starts with Mug) → Sublimation; else DTF. Blank → **`unmatched`**. Plain slot is `x`. Code: `shared/printing_type.py`. Do not fill `Design Type`. |
| supply method | process files | **`Supply Method`** on CL + Plain + Packs | Flag `1` on plain and printed. Locked values (2026-09-09): **`Warehouse Stock`** = Fruit of the Loom men / women / kids **t-shirts only**; **`In House Manufacture`** = Custom Label SKU or Gender Apparel contains iron on / ironon / iron-on / sticker (printed only); **`Supplier On Demand`** = Gildan t-shirts **and everything else**. Do **not** reuse CL `Warehouse Stock` (Yes on China bags). **Plain cannot be in-house** → never write In House Manufacture on Plain/Packs. Blank → **`unmatched`**. Code: `shared/supply_method.py`. |
| supplier | process files | **`Supplier Name`** on CL + Plain + Packs | Plain `1`. Printed warehouse-stock `x`. Printed supplier-on-demand `1`. Canonical cells: **`BTC Activewear`**, **`Uneek Clothing`**, **`Absolute Apparels`**. Absolute = babysuits only (`C800T` / `C8020T` / `C8030T`). Blank when the split is on → **`unmatched`**. Filled 2026-09-09. |
| package-type | off v1 (flag `0`); **display** on packing PDF | **CL DB** `Package Type` | Plain and printed both `0` (supervisor: treat plain the same). No process split. Still print on the PDF. Blank does **not** send to `unmatched` for grouping. Live CL values: Large Letter, Parcel, RM Small Parcel. |
| category (30-chain) | process files at ≥30 | `Category (Areeb)` | CL: warehouse `cl_standard` from Gender Apparel. Plain/Packs: BTC Department / Uneek Category. Plain leftover (no supplier join): Description → BTC Department words. Blank → **`unmatched`**. |
| product type (30-chain) | process files at ≥30 | `Product Type (Areeb)` | CL: `cl_standard`. Plain/Packs: BTC Sub Department / Uneek Product Name. Plain leftover: Description → BTC Sub Department. |
| product style (30-chain) | process files at ≥30 | `Product Style (Areeb)` | CL: `cl_standard` style token from Gender Apparel (**not** Brand). Plain/Packs: BTC Brand / Uneek Full Description. Plain leftover: Plain `Brand`. |
| department (30-chain) | process files at ≥30 | `Department (Areeb)` | CL: warehouse **gender only** (`Mens` / `Womens` / `Kids` / `Unisex` / `General`). Plain/Packs: BTC Description / Uneek Gender. Plain leftover: Plain `Description` (not gender). Do **not** overwrite PE `Department`. |
| brand (30-chain) | process files at ≥30 | **CL** `Brand` / Plain `Brand` / Packs **`Brand Name`** | Flag `0` on printed = off for now. Blank when the split is on → **`unmatched`**. Packs always use **Brand Name**. |
| size (30-chain) | process files at ≥30 | **CL** `Size` / Plain `Size` / Packs **`Pack Size`** | Existing (`Small`, `5-6 Years`, …). Packs use **Pack Size**. Blank when the split is on → **`unmatched`**. |
| colour (30-chain) | process files at ≥30 **and** process numbers at ≥3 qty | **CL** `Colour` / Plain `Colour` | ≥30 **qty** → **new process file**. ≥3 **qty** of that colour → **own `-N` inside** the current process (same order stays together). Same column for both. Blank when the split is on → **`unmatched`**. **Packs colour is later** — do not use Item 1–10 Colour (often different; guessing Item 1 breaks definite-match; dumping mixed packs to unmatched is worse). Packs still split on Areeb + Brand Name + Pack Size. Pack colour does **not** unmatched. |
| resend | process files | **ShipStation** tag **`1014-ALL-RESEND` only** | Exact tag on the **order** → filename **`resend` only** (no slots). Whole order regardless of plain/printed/prime. **Do not** treat `1015-ALL-RESEND MANUALLY DISPATCHED`, `1016-ALL-RESEND PRIME`, or `1017-BULK-RESEND MAKING` as resend. Those follow normal grouping (or `unmatched` if they fail a definite match). |
| shift fill | intake + **folder** + **filename** | **configuration** | One run fills **all three** Packing Input shift folders: **`1st Shift` = 300**, **`2nd Shift` = 100**, **`3rd Shift` = 100** **lines** (not orders). Fill each cap with **today/overdue** first, then **future `shipByDate`** if still under. Ignore existing ShipStation shift tags (`001-1st Shift`, …). **Folder** matches Packing: `Input/{DD-MM-YYYY}/1st Shift/` (and `2nd Shift`, `3rd Shift`). **Filename slot** (flag `1`, after `today` / `YYYY-MM-DD`): **`1st`** / **`2nd`** / **`3rd`**. Same process in two shifts = two files. `resend` / `unmatched` still have no shift slot. |
| order pool | intake | **ShipStation API only** | Fetch **all** `awaiting_shipment`. **No file intake** (CSV has no tags). Skip tag `post-order-designs`. |
| app split | — | — | **Order Grouping Sorter** (new first-level folder, outside Packing): reads ShipStation `awaiting_shipment` + the three catalogs; writes **one CSV per process** into Packing `Input/{date}/{shift}/`. CSV shape = Packing current-view columns (`Order #`, `Ship By`, `Quantity`, `Item SKU`, …). **Packing:** filename = process name; `100APCDX` removed after a dry-run the supervisor accepts. First milestone: **dry-run** (counts + process names, no Input write) until **run**. |
| parts | process numbers inside file | **50 units** (Packing PDF threshold) | Every 50 units → next `-N` inside the same process. Not a new process file. Replaces CEO graph `0–30` / `31–60` / `61–90`. |
| colour then parts | inside file | colour 3+ then 50-unit parts | **Colour 3+ groups first**, then 50-unit parts inside those groups. Same customer order stays on **one `-N`** (a part split must not break an order across parts). Packs skip the colour-group step. |
| process name | filename | **Graph flags** | Hyphens, spaces → underscores. Flag `x`/`0` → slot `x`. First slots: `today` or `YYYY-MM-DD`, then **`1st` / `2nd` / `3rd`**. Special files: **`resend`**, **`unmatched`** (no slots, including no shift). 30-chain value only appears when that level actually splits. Plain and printed names differ (see flag table). |
| design grouping | process files when flag `1` | **configuration** (per scenario) | Off now. When on: slot is `group-01`… from **that scenario’s** Design ID / logo list. |
| print size | off in v1 | **CL DB** `Print Size 1` | Do not split in first version. |
| print position | off in v1 | **CL DB** `Print Positions` | Do not split in first version. |
| customisation type | off in v1 | **CL DB** `Customisation Type` | Column present. Values empty. Slot `x` until a fill rule exists. Plain/Packs do not need this column. |

### Plain vs printed (locked)

Finish comes from database hit (with an explicit SKU override):

1. If Item SKU contains `plain` / `plainlg` → **plain**
2. Else if CL DB matches `Custom Label` using **after first dash** → **printed**
3. Else if Plain Database matches `SKU` using **till last dash** (or whole SKU) → **plain**
4. Else if Packs Database matches **whole SKU** (`Channel Child SKU`) → **plain**
5. Else → **`unmatched`**

`Customise = Yes` is a **printed** split (CL), not the plain/printed gate. DTF-transfer / `PER` / SET: see locked section below.

## Order Grouping Sorter (step 3, locked 2026-09-10)

New app folder **`Order Grouping Sorter`**. Not inside Packing. Reads ShipStation + CL + Plain Database + Packs. Writes into Packing `Input/{DD-MM-YYYY}/{shift folder}/`.

**v1 filename:** `{today|YYYY-MM-DD}-{1st|2nd|3rd}-{plain|printed}-{own|fawad}-…` with Graph slots. Special names **`resend`** and **`unmatched`** have no slots. Inside each CSV: colour 3+ groups first (not packs), then 50-unit parts; same order stays on one `-N`.

**First milestone:** live `awaiting_shipment` dry-run — print shift folder, process names, order/line/unit counts. **No Input write** until supervisor **run**.

## Catalog fill (step 2) — Areeb 30-chain (locked 2026-09-08)

CEO approved the grouping **logic**. 30-chain sources are the four **Areeb** columns on CL, Plain Database, and Packs (not PE `Category` / `Department`). Rule: `.cursor/rules/custom-label-database/areeb-taxonomy.mdc`. Code: `shared/areeb_taxonomy.py`.

Checked 2026-09-08 (no writes):

| Database | Size | Grouping-ready today | Missing for grouping |
|---|---|---|---|
| **CL** | 131,892 rows, 60 cols | Colour / Size / Brand / Supplier Name / Category / Sub-Category ~90–100%. `Customise` Yes on 10% (blank = readymade). | `Printing Type` **0%**. No `Supply Method`. `Department` = copy of `Category` (T-Shirts, Hoodies…) — **not** CEO men/general. No product-style `Description`. `Package Type` 34% (display only). |
| **Plain Database** | 78,039 rows | Brand / Colour / Size / Description / Package **100%**. Areeb + Supply Method + **Supplier Name filled 2026-09-09**. | — |
| **Packs** | 38,452 rows on `01-Database` | Category / Sub Category / Brand Name / Pack Size **100%**. Supply Method + **Supplier Name filled 2026-09-09** (`BTC` → `BTC Activewear`). | `Description` is often **eBay HTML**. Colour is per item (Item 1–5). |

**Do not add CL `Product Type` / `Product Style`.** Criteria rows 25–27 already map the Graph 30-chain onto existing catalog language for **plain**: category → **Department**, product-type → **Sub-Department**, product-style → **Description**. BTC Product Data already has Department / Sub Department / Description keyed by UID (= Plain `SKU`). Uneek Product Data has Category / Product Name / Gender (no BTC-style Sub Department).

**Do not overwrite CL `Department` with men/general.** That column is the PE category clone today. CEO men/general needs a **new** column (proposed: keep Graph slot `department`; header TBD).

Fill sources (when we get to fill/run): **CL Areeb** = warehouse `cl_standard` from Gender Apparel only (never BTC/Uneek/Brand; Department = gender only). **Plain Areeb** = BTC UID, else Uneek Short Code, else Product Code → BTC SPC, else leftover from Plain Brand/Description in BTC language. **Packs Areeb** = BTC/Uneek joins. **Supply Method** = `shared/supply_method.py` (FOTL t-shirts / iron-on+sticker / on-demand). **Printing Type** = `shared/printing_type.py` (DTF default; Sublimation = mugs). **Supplier Name** = `shared/supplier_name.py` (Absolute babysuits / Uneek / BTC). SKU/token rules for Customise. Fill **by rule across the catalog**, not only today’s `awaiting_shipment` rows.

## Catalog fill (step 2) — Supply Method (locked 2026-09-09)

Add column **`Supply Method`** on CL, Plain Database, and Packs. Fill every row from `shared/supply_method.py` (later CL rows: `fill_from_seeds.py --steps supply`). One-off: `python scripts/fill_supply_method.py`.

| Cell value | What it is | How the system decides |
|---|---|---|
| `Warehouse Stock` | Fruit of the Loom **men / women / kids t-shirts only**. That is all. | Brand is FOTL (`Fruit Of The Loom` / `Fruit of the Loom` / `FOTL` / `FOLT`) **or** Gender Apparel is `Mens-T-Shirt` / `Womens-T-Shirt` / `Kids-T-Shirt` with blank Brand; **and** `Category (Areeb)` is `T-SHIRTS`; **and** not a vest/tank. Long-sleeve FOTL tees count. FOTL hoodies / polos / bags do **not**. |
| `In House Manufacture` | Iron-on **or sticker**, made in the warehouse | CL only: **Custom Label** (SKU) or **Gender Apparel** contains `iron on` / `ironon` / `iron-on` / `sticker` (hyphens and spaces ignored). **Never** written on Plain or Packs. |
| `Supplier On Demand` | Gildan t-shirts **and everything else** | Default. Includes Gildan tees, FOTL hoodies/polos, vests/tanks, bags, Uneek, China bags (the old `Warehouse Stock` = Yes column is **not** this field). |

Do **not** reuse CL `Warehouse Stock` (32 China bags marked Yes). Gildan brand always wins over a `Womens-T-Shirt` Gender Apparel token.

**Filled 2026-09-09** (overwrite all rows; backups first). 0 blanks.

| File | Rows | Warehouse Stock | In House Manufacture | Supplier On Demand | Backup |
|---|---:|---:|---:|---:|---|
| Custom_Label_Database.csv | 131,892 | 83,801 | 453 | 47,638 | `database/shared/custom_label/backups/Custom_Label_Database.bak_20260909_170833.csv` |
| Plain Database.xlsx | 78,039 | 2,530 | 0 | 75,509 | `database/shared/plain/archive/Plain Database.bak_20260909_170955.xlsx` |
| Packs Database.xlsx | 38,452 | 17,252 | 0 | 21,200 | `database/shared/packs/archive/Packs Database.bak_20260909_171153.xlsx` |

## Catalog fill (step 2) — Printing Type (locked 2026-09-09)

Fill existing CL column **`Printing Type`**. Code: `shared/printing_type.py`. One-off: `python scripts/fill_printing_type.py`. Later CL rows: `fill_from_seeds.py --steps printing_type`.

| Cell value | What it is | How the system decides |
|---|---|---|
| `DTF` | Default print method | Custom Label leading `M##` hits Mocks `Printing-Type` = DTF, **or** not a mug. Iron-on and stickers are DTF. |
| `Sublimation` | Mugs / drinkware | Mock `Printing-Type` = Sublimation (`M61` / `M64`), **or** `Category (Areeb)` = `Mugs`, **or** Gender Apparel starts with `Mug`. |

Do not fill `Design Type`. Plain flag is `x` (no Printing Type split).

**Filled 2026-09-09** (overwrite all CL rows). 0 blanks. Backup `database/shared/custom_label/backups/Custom_Label_Database.bak_20260909_173522.csv`.

| File | Rows | DTF | Sublimation |
|---|---:|---:|---:|
| Custom_Label_Database.csv | 131,892 | 131,802 | 90 |

## Catalog fill (step 2) — Supplier Name (filled 2026-09-09)

Column **`Supplier Name`** on all three catalogs. Grouping split: Plain `1`; printed warehouse-stock `x`; printed supplier-on-demand `1`. Canonical cells. Code: `shared/supplier_name.py`. One-off: `python scripts/fill_supplier_name.py`.

| Cell | When |
|---|---|
| `BTC Activewear` | BTC Product Data UID or SPC hit. Packs existing `BTC` normalizes to this. Plain leftover numeric SKU (discontinued BTC UID) also this. |
| `Uneek Clothing` | Uneek Product Data Short Code or Product Code hit. Uneek `Company` is 100% this string. |
| `Absolute Apparels` | Babysuits purchased from Absolute only. Styles **`C800T` / `C8020T` / `C8030T`** (Body Suit Baby / Romper Suit Baby on Absolute Product Data). Token in Custom Label, Gender Apparel (`C800T-BS`), SKU, or Product Code. Not the rest of the Absolute wholesale sheet. `BZ10-Body Suit` is not Absolute. |
| (blank) | CL in-house only (iron-on / sticker). No supplier. Printed warehouse-stock does not split on this field. |

Decision order: in-house blank → Absolute babysuit style → BTC UID → Uneek Short Code → BTC SPC → Uneek Product Code → `BTC Activewear`. Do not use Packs short `BTC` as a second spelling.

**Filled 2026-09-09** (overwrite; backups first).

| File | Rows | BTC Activewear | Uneek Clothing | Absolute Apparels | Blank | Backup |
|---|---:|---:|---:|---:|---:|---|
| Custom_Label_Database.csv | 131,892 | 123,948 | 6,992 | 499 | 453 (in-house) | `database/shared/custom_label/backups/Custom_Label_Database.bak_20260909_185544.csv` |
| Plain Database.xlsx | 78,039 | 71,047 | 6,992 | 0 | 0 | `database/shared/plain/archive/Plain Database.bak_20260909_185710.xlsx` |
| Packs Database.xlsx | 38,452 | 38,452 | 0 | 0 | 0 | `database/shared/packs/archive/Packs Database.bak_20260909_185937.xlsx` |

CL wrote 5,430 cells. Plain 78,039. Packs 38,452 (`BTC` normalized to `BTC Activewear`). C8020T not in catalogs yet.

### Proposed 30-chain column map (not locked until supervisor confirms)

| Graph slot | CL (printed) | Plain Database | Packs |
|---|---|---|---|
| category | existing `Category` (PE Department values) | **add** `Department` from BTC/Uneek | existing `Category` |
| product-type | existing `Sub-Category` | **add** `Sub-Department` from BTC/Uneek | existing `Sub Category` |
| product-style | TBD (no Description; `Gender Apparel` is closest) | existing `Description` | **not** `Description` (HTML). Closest short fields: `Name` or `Product Sub-Category` |
| department (men / general) | **add** new column; do not overwrite `Department` | **add** same new column | **add** same new column |
| brand | `Brand` | `Brand` | `Brand Name` |
| size | `Size` | `Size` | `Pack Size` |
| colour | `Colour` | `Colour` | pack line has several item colours — later |

**Supply Method** (filled 2026-09-09 on all three). **Printing Type** (filled 2026-09-09 on CL): `DTF` / mug `Sublimation`. **Supplier Name** (filled 2026-09-09 on all three): `BTC Activewear` / `Uneek Clothing` / babysuit `Absolute Apparels`.

## CL DB — fill vs add

Superseded in part by **Catalog fill (step 2)** above. Do not add `Product Type` / `Product Style`. Do not overwrite `Department` until the 30-chain map is confirmed.

| Need | Column | Action |
|---|---|---|
| Customise | `Customise` | **Have.** `Yes` / blank. No add. |
| Customisation type | `Customisation Type` | **Have (empty).** Split off in v1. Do not fill until a rule is locked. |
| Printing method | `Printing Type` | **Have, filled 2026-09-09.** `DTF` default; `Sublimation` = mugs. Do **not** add a second column. Do not fill `Design Type`. |
| Supply method | `Supply Method` | **Have, filled 2026-09-09** on all three. `Warehouse Stock` / `In House Manufacture` / `Supplier On Demand`. Do **not** reuse `Warehouse Stock`. |
| Package type | `Package Type` | **Have** (~34% filled). Fill remaining for **packing PDF**. Not a grouping split in v1 (flag `0` plain and printed). |
| Colour, size, brand, supplier | `Colour`, `Size`, `Brand`, `Supplier Name` | **Have, filled 2026-09-09** on all three. CL 123,948 BTC Activewear / 6,992 Uneek Clothing / 499 Absolute Apparels / 453 in-house blank. |
| Category | `Category` | **Have.** 30-chain. Fill blanks. |
| Product type | none | **Add** `Product Type`, then fill. |
| Product style | none | **Add** `Product Style`, then fill. |
| Department | `Department` | **Overwrite and refill** (`men` / `general`, …). Production overwrite needs fill/run + backup. |
| Design groups | Design ID lists | **Configuration, per scenario.** Off now. |
| Print positions / size | `Print Positions`, `Print Size 1` | Flag `0` in v1. |
| Amazon Prime (catalog) | `Amazon Prime` | **Not grouping.** PO/inventory only. |

## Locked: DTF-transfer / `PER` / SET edge cases vs plain

DTF-transfer / `PER` finish-gate behaviour is locked:

- They do **not** match the **Plain Database** (till last dash) and do **not** match the **Packs Database** (whole SKU / `Channel Child SKU`) under the key rules.
- Therefore, unless the **Item SKU** explicitly contains `plain` / `plainlg`, the finish gate will fall through to **`unmatched`** (and the **whole order** goes to `unmatched` if any required split field is missing).

For `SET*` lines specifically: finish still comes from the existing rule that **Packs Database** whole-SKU hits resolve to **plain**.
