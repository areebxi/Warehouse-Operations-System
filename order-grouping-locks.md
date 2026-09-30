# Order grouping — locked decisions

Living notes. Sources: **ShipStation**; **CL DB** (`database/shared/custom_label/Custom_Label_Database.csv`); **Plain Database** (`database/shared/plain/Plain Database.xlsx`); **Packs Database** (`database/shared/packs/Packs Database.xlsx`); **configuration**.
A **grouping run** only **reads** the three catalogs (it does not overwrite them). **Step 2 fill** may write all three after supervisor **fill / run**. Backup first.

**Sequence (do not skip):** (1) lock **grouping logic** — **CEO approved 2026-09-08** → (2) catalog **fill on all three databases** (CL + Plain + Packs) — **done 2026-09-09** → (3) **build** **Order Grouping Sorter** (new app, outside Packing) → (4) **dry-run** on live `awaiting_shipment` (counts + process names, **no** Packing Input write) until supervisor **run**. Do not write Input CSVs until **run**.

**v1 process names accepted 2026-09-11** (supervisor: they look right). Inside-file `-N` (colour 3+ then 50-unit parts) is in the dry-run report.

**Unmatched loop 2026-09-11:** Flag-30 blank stays in the parent (in-house Brand / sticker Colour are empty by design). Do not dump those to `unmatched`. Blank ship-by → today (2026-09-24). Missing CL rows are a catalog add, not a matcher guess.

**CEO review table:** `order-grouping-criteria.csv` — one row per implemented rule, in run order. Columns: Stage, Criterion, Implemented logic, Plain/Printed split, Source type, Live file or API, CL / Plain / Packs column headers, ShipStation or config field, If blank or mixed, Filename / output.

## Dimensions vs example values

The screenshot / Graph header row is the **axis list** (what we can split on), in order:

`order-status` → `ship-by-date` → `shift` → `product-finish` → `order-source` → `design-grouping` → `shipping-service` → `printing-method` → `customized` → `customization-type` → `print-size` → `print-position` → `supply-method` → `supplier` → `package-type` → `category` → `product-type` → `product-style` → `department` → `brand` → `size` → `color`

Sheet spellings `customized` / `customization-type` / `color` = our `customised` / `customisation-type` / `colour` (CL uses `Customise`, `Colour`).

**Values on the Graph and Grouping Data are examples only**, not a closed list — **except** Hashim #038 **category / product type / product style / department** (the four Areeb columns) plus PE **subcategory**, which are closed pick-lists (`database/order-grouping-sorter/taxonomy_picklists.csv`). When a product arrives, pick only from those rows; do not invent a new drive. Other dimensions (supply methods, channels, printing methods, brands, sizes, colours, …) still take whatever definite values exist at run time. A missing Graph branch does **not** mean that value is off.

**In-house manufacturer** = we **make it in the warehouse**. Locked cell: **`In House Manufacture`** = iron-on **or sticker** (Custom Label SKU or Gender Apparel contains `iron on` / `ironon` / `iron-on` / `sticker`). **Plain cannot be in-house** (plain is not made here). If a line looks plain but supply-method is in-house → **`unmatched`**. Printed can be in-house. Plain `Supply Method` is still flag `1`: `Warehouse Stock` or `Supplier On Demand` (never In House Manufacture on Plain/Packs).

## Closed pick-lists (Hashim #038, squeezed 2026-09-16)

Hold basic configuration for the **four Areeb columns** plus PE subcategory. File: `database/order-grouping-sorter/taxonomy_picklists.csv`. Code: `shared/taxonomy_picklist.py` + `shared/taxonomy_catalog.py`.

| Column | Warehouse header | Notes |
|---|---|---|
| category | `Category (Areeb)` | Title Case families (`T-Shirts`, `Sweatshirts & Hoodies`, …). No ALL CAPS. No BTC wholesale extras (Footwear, Consumables, …). |
| product type | `Product Type (Areeb)` | Silhouette / bag kind. **No gender** (`Short Sleeve T-Shirt`, not Mens/Ladies/Childrens). Gender lives in Department. |
| product style | `Product Style (Areeb)` | Named range or simplified product name (`Valueweight`, `Junior Fashion Backpack`). **Never a supplier code** (`BG125L`). Generic warehouse SKU → `Standard`. |
| department | `Department (Areeb)` | Gender only: `Mens` / `Womens` / `Kids` / `Unisex` / `General`. On the pick-list. |
| subcategory | PE `Sub-Category` | Closed Title Case list. **Not** a 30-chain split. Do **not** add a fifth Areeb column. |

When a product arrives, pick only from the CSV. Unknown warehouse fill → **blank that cell** (do not invent). To allow a new value, add it in `shared/taxonomy_catalog.py` and rebuild (`python scripts/build_taxonomy_picklists.py`). Do not re-harvest catalogs. Grouping does **not** unmatched an already-filled catalog cell that is off-list. **Plain / Packs Areeb copy BTC / Uneek product data** — do not refill those two from the warehouse pick-list. **CL live refill 2026-09-16 10:17** (`python scripts/fill_areeb_taxonomy.py --target cl`): 131,909 rows; 298,338 Areeb cells; 0 blank / 0 off-list. Backup `Custom_Label_Database.bak_20260916_101719.csv`.

## Definite match / unmatched

Grouping **never guesses**. A field is used only when the value is definite. If a required field is missing or blank, that order is **unmatched**.

| | Meaning |
|---|---|
| **unmatched** | One process file named **`unmatched`**. Floor processes it **manually this run**. Then we **investigate why** it failed a definite match and **tighten the rule or catalog** so the next run can match it. Not mixed into `today-…` piles. |
| Same order | If any line fails a required match, the **whole order** goes to `unmatched`. |

**SKU match keys (entire-cell, casefold).** Each database uses **one** key rule — no numeric stripping, no cross-key guessing.

| Source | File | Key from Item SKU | Example Item SKU | Key matched in DB |
|---|---|---|---|---|
| Custom Label | `database/shared/custom_label/Custom_Label_Database.csv` | **After first dash**; **no dash → whole SKU** | `77989LG-M-T-BLK-M` / `A515` | `M-T-BLK-M` / `A515` → `Custom Label` |
| Plain Database | `database/shared/plain/Plain Database.xlsx` sheet `Sheet1` | **Till last dash** | `1243-1` | `1243` → column **SKU** |
| Packs | `database/shared/packs/Packs Database.xlsx` sheet `01-Database` | **Whole SKU** | `SET4741` | `SET4741` → **Channel Child SKU** |

**Plain vs printed:** finish gate (with explicit SKU override). If Item SKU contains `plain` / `plainlg` → plain. Otherwise finish comes from database hit: **CL** matches `Custom Label` after the first dash (or **whole SKU when there is no dash**, locked 2026-09-22) → printed; **Plain Database** matches `SKU` till the last dash (or whole SKU) → plain; **Packs** matches whole SKU (`Channel Child SKU`) → plain. If none hit → `unmatched`. (These are entire-cell key matches; no numeric-prefix stripping for plain.)

**Attribute source when a line needs catalog fields:** Packs if whole-SKU hits → else CL if after-first-dash hits (or whole SKU when no dash) → else Plain Database if till-last-dash hits. Unmatched for that line’s required fields only if **none** of the three hit.

SET / pack orders (`SET*`) match **Packs** on whole SKU. Checked 2026-09-03: `SET4741`, `SET15007`, `SET5733` are in Packs Database.

**Blank `shipByDate`:** treat as **today** (run date) and process this run — if it is in ShipStation `awaiting_shipment`, it must go out today (supervisor 2026-09-24: *agar ShipStation me aaya hua hai, usse aaj nikalna hai*). Applies to **all stores** (after earlier skips). Unparseable non-blank ship-by stays unmatched. Store **`DTFOcean.co.uk WP`** is skipped earlier and never reaches this gate.

**Future `shipByDate`:** not unmatched — date is known. This run writes future CSVs too. **Hashim 2026-09-14 (#037):** when Shift 1 **order** volume is **above 300**, split process CSVs by date (**today/overdue vs later ship-by**). At or under 300, today and later may share a process. **Do not** dump overflow into Shift 2/3 as capacity caps (wrong: keep 300 / 100 / 100 and drop the rest). Counts are **orders**, not lines. Fixed batches follow the same mix/split.

**Intake:** **ShipStation `awaiting_shipment` only.** No supervisor CSV/file — ShipStation CSV export has no tags. Order of gates: skip `post-order-designs` → skip store **`DTFOcean.co.uk WP`** (not processed in this system; supervisor 2026-09-24) → resend tag (wins even if ship-by is blank) → blank ship-by → **today** → write **all** eligible orders into this run’s shift folder → split remaining. **Today/overdue always get CSVs this run** (core policy — never held). A later split with a blank required catalog field also sends the whole order to `unmatched`.

**Testing vs production (locked 2026-09-15):** Testing rewrites **`1st Shift`** on every `--run` (many test runs). **Nth `--run` of the day = nth shift** starts at **production**, not now.

Until catalog columns are filled (e.g. `Printing Type`), printed lines will go to `unmatched` in a test run. That is expected. Catalog fill is step 2 **on all three databases**. Unmatched is a **feedback loop**, not a dump: investigate → tighten logic/catalog → next run should match.

Live check 2026-09-03: 191 `awaiting_shipment` orders. **CL-only** match ~94% of units. SET SKUs that missed CL (`SET4741`, `SET15007`, `SET5733`) **are** in Packs Database. `Printing Type` empty. No mixed plain+printed orders in that pool.

## Batch, process number, item number (locked 2026-09-23)

| | Meaning |
|---|---|
| **Batch** | One output CSV / one pile. Filename is the full batch name (fixed `B100-S1-PRINTED-…-1` or leftover `B1-S1-PRINTED-…-1`). Special filenames: **`RESEND`**, **`UNMATCHED`**. |
| **Process number** | The increment **inside** that batch: `-1`, `-2`, … Colour 3+ groups first, then 50-unit splits. Same customer order shares one process number. |
| **Item number** | Line inside that process number: `Item 1`, `Item 2`, … |

**Packing PIN** (display only — not the on-disk filename): `{B-code}-S{n}-{process_number} Item {item_number}`  
Uses **batch code + shift only** from the filename (drops finish/prime/supply/R|P/priority).  
Example: filename `B100-S1-PRINTED-2-WAREHOUSE STOCK-R-1` → PIN `B100-S1-1 Item 1` then `B100-S1-1 Item 2` then `B100-S1-2 Item 1`.  
Leftover example: filename `B1-S1-PRINTED-2-SUPPLY ON DEMAND-R-3` → PIN `B1-S1-1 Item 1`.

Same customer order **always** stays in one batch file. If one order has **plain and printed** lines → whole order goes **printed** (printed-wins).

## Flags

| Flag | Meaning |
|---|---|
| `1` | Split into **new process files**. Value goes in the process name. |
| `x` | Do not split. Name slot is `x`. |
| `0` | Off **now** (same as `x` at run time). Stays in config so CEO can set `1` later. |
| `30` | On the taxonomy chain only: if that bucket has **≥ 30** units, **new process file**. |
| Colour **3+** | **Qty (units)**, not order count. ≥ 3 units of that colour → **own process numbers inside** the same batch. One order with qty 3 qualifies. Does not split an order. Sheet note said “orders”; supervisor locked **qty**. |
| Parts (→ process numbers) | **Process numbers inside** the same batch, not new batch files. Same idea as Packing PDF parts: **50 units per process number** (Packing writes `_Part N.pdf` at 50 pages; one page = one unit). CEO graph bands `0–30` / `31–60` / `61–90` are **replaced** by this 50 threshold. |

**Taxonomy chain (new process files at 30):** category → product-type → product-style → department → brand → size → colour.

If a branch on the CEO sheet **does not draw that chain all the way to colour**, that is **shorthand** (save writing). It still uses the same tail as the sibling branch that *was* written out. Missing cells do **not** mean “stop splitting here.”

**Graph is the source of truth (supervisor 2026-09-11).** Walk left to right in Graph order. The 30-chain is **the same for plain and printed**: every step is `30`. Example: 29 short-sleeve t-shirts stay **one process** (all departments, brands, sizes, colours together). Printed department/size are **not** always-split. Printed brand is **not** skipped. Packs still skip colour (later).

**Left-side dimensions (new process files when `1`):** shift, product-finish, order-source, design-grouping, shipping-service (prime / non-prime), printing-method, customised, customisation-type, print-size, print-position, supply-method, supplier, package-type. **`shift` is on in the filename** (slot `1st` / `2nd` / `3rd` / …, Graph order after ship-by-date) **and** is this run’s Packing Input folder (`1st Shift` / `2nd Shift` / `3rd Shift` / …).

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
| today | process files | **ShipStation** `shipByDate` | **Today = run date or overdue** (`shipBy <= run date`), **or blank ship-by** (treat as today — in awaiting_shipment → pull today; 2026-09-24). Unparseable non-blank ship-by → unmatched. **Core policy:** every today/overdue order gets a process CSV on this run — never held. **Hashim 2026-09-14 (#037):** Shift 1 **order** volume **above 300** → separate process CSVs for today vs later dates; ≤300 → may mix. Do not dump overflow into Shift 2/3. Filename has **no** today/future slot. |
| unmatched | process files | any required field with no definite value | Filename **`UNMATCHED` only**. Whole order. Includes unparseable ship-by and blank required CL fields when that split is on. Blank ship-by is **not** unmatched (→ today). Manual this run; then investigate and tighten so the next run matches. |
| shipping-service (prime) | process files | **ShipStation** tag `Amazon Prime Order` | Tag → `prime`. No tag → `non-prime`. Do **not** use CL `Amazon Prime` (that is product-level, for PO). Live 2026-09-03: 12 Prime orders, all `amazon_shipping`. |
| order source | process files | **ShipStation** store (and later tags) + **configuration** peel-off list | Flag `1`. Unlisted → **`own`**. **Amazon is not its own channel**. First peel-off: store **MAS Clothing** → process-name slot **`fawad`**. More channels later. `daataa-direct` on the Graph is a CEO example, not a live peel until listed. |
| product finish | process files | **DB finish gate + plain override** | **Plain override:** if Item SKU contains `plain` / `plainlg` → plain (finish locked). Otherwise finish comes from database hit: **CL** (match `Custom Label` after **first dash**, or **whole SKU when there is no dash**) → printed; **Plain Database** (match `SKU` till **last dash**, or whole SKU) → plain; **Packs** (match whole SKU → Channel Child SKU) → plain. If none hit → `unmatched`. We assume catalog curation keeps printed items in CL and plain items in Plain/Packs. |
| mixed plain+printed | one process (printed-wins) | same customer order | Whole order goes to the **printed** process. Never two files. None in the 2026-09-03 pool. |
| customised vs ready-made | process files (**printed only**, flag `1`) | **CL DB** `Customise` + **SS tag** | Printed + `Yes` → customised. Other printed → ready-made. Plain slot is `x`. **Mixed P vs R in one order (locked 2026-09-17):** whole order follows **majority printed units**; **tie → readymade**. Not unmatched. Same order stays together. **Personalised ready gate (locked 2026-09-25):** customised piles only when the order has ShipStation tag **`1004- Personalised Design-Ready-`** (exact name; design already on the floor). Customised without that tag → **held** this run (not written; stay in `awaiting_shipment`). Readymade / plain unaffected. Not `1003-…Not Ready`. |
| printing method | process files (**printed only**, flag `1`) | **CL DB** `Printing Type` | Split on cell value. Locked 2026-09-09: **`DTF`** default; **`Sublimation`** = mugs. Mock `M##` → `Mocks Database.csv` Printing-Type when DTF/Sublimation; else mug (`Category (Areeb)` Mugs or Gender Apparel starts with Mug) → Sublimation; else DTF. Blank → **`unmatched`**. Plain slot is `x`. Code: `shared/printing_type.py`. Do not fill `Design Type`. |
| supply method | process files | **`Supply Method`** on CL + Plain + Packs | Flag `1` on plain and printed. **`In House Manufacture`** = Custom Label SKU or Gender Apparel contains iron on / ironon / iron-on / sticker (printed only). **`Supplier On Demand`** = everything that is not warehouse stock (Gildan tees, off-list FOTL colours, other garments). Do **not** reuse CL `Warehouse Stock` (Yes on China bags). **Plain cannot be in-house** → never write In House Manufacture on Plain/Packs. Blank → **`unmatched`**. **Mixed supply-method in one order (locked 2026-09-22):** whole order **Supplier On Demand** (on-demand item arrives later). Not unmatched. Same order stays together. **CL Warehouse Stock (locked 2026-09-23):** FOTL t-shirts only, and only the colour lists in `shared/supply_method.py` (`Mens` / `Womens` = Ladies / `Kids`; whole `Colour` cell). Plus Kids **`C800T` / `C8030T`** in Black, Lemon Yellow, Light Blue, Light Pink, Red, Sports Grey, White. Not `C8020T`. **Plain / Packs Warehouse Stock** stays all FOTL men/women/kids t-shirts (no colour list). Code: `shared/supply_method.py`. |
| supplier | process files | **`Supplier Name`** on CL + Plain + Packs | Plain `1`. Printed warehouse-stock `x`. Printed supplier-on-demand `1`. Canonical cells: **`BTC Activewear`**, **`Uneek Clothing`**, **`Absolute Apparels`**. Absolute = babysuits only (`C800T` / `C8020T` / `C8030T`). Blank when the split is on → **`unmatched`**. Filled 2026-09-09. |
| package-type | off v1 (flag `0`); **display** on packing PDF | **CL DB** `Package Type` | Plain and printed both `0` (supervisor: treat plain the same). No process split. Still print on the PDF. Blank does **not** send to `unmatched` for grouping. Live CL values: Large Letter, Parcel, RM Small Parcel. |
| category (30-chain) | process files at ≥30 | `Category (Areeb)` | CL: warehouse `cl_standard` from Gender Apparel, snapped to the closed Title Case pick-list (Hashim #038, squeezed 2026-09-16). Plain/Packs: BTC Department / Uneek Category (supplier copy, not invented). Plain leftover (no supplier join): Description → BTC Department words — **does not snap** to the warehouse list. **Flag 30 blank stays in the parent**. |
| product type (30-chain) | process files at ≥30 | `Product Type (Areeb)` | CL: silhouette, **no gender** (Department holds gender), snapped to the pick-list. Plain/Packs: BTC Sub Department / Uneek Product Name. Plain leftover: BTC Sub Department words, no warehouse snap. Flag 30 blank stays in the parent. |
| product style (30-chain) | process files at ≥30 | `Product Style (Areeb)` | CL: named range / simplified product name from Gender Apparel + supplier catalogs (**not** Brand, **not** a product code like `BG125L`). Unknown style is left blank. Plain/Packs: BTC Brand / Uneek Full Description. Plain leftover: Plain `Brand`. Flag 30 blank stays in the parent. |
| department (30-chain) | process files at ≥30 | `Department (Areeb)` | Same `30` on plain **and** printed. CL: warehouse **gender only** (`Mens` / `Womens` / `Kids` / `Unisex` / `General`), on the pick-list. Plain/Packs: BTC Description / Uneek Gender. Plain leftover: Plain `Description` (not gender). Do **not** overwrite PE `Department`. Blank / mixed / under 30 stay in the parent file (not unmatched). |
| brand (30-chain) | process files at ≥30 | **CL** `Brand` / Plain `Brand` / Packs **`Brand Name`** | Same `30` on plain **and** printed (Graph). Blank / mixed / under 30 stay in the parent. Packs always use **Brand Name**. **In-house (iron-on / sticker) Brand is intentionally blank** — that is not unmatched. Absolute babysuits and bags often have blank PE Brand too. |
| size (30-chain) | process files at ≥30 | **CL** `Size` / Plain `Size` / Packs **`Pack Size`** | Same `30` on plain **and** printed (Graph). Packs use **Pack Size**. Blank / mixed / under 30 stay in the parent (not unmatched). |
| colour (30-chain) | process files at ≥30 **and** process numbers at ≥3 qty | **CL** `Colour` / Plain `Colour` | ≥30 **qty** → **new process file**. ≥3 **qty** of that colour → **own `-N` inside** the current process (same order stays together). Same column for both. Flag 30 blank stays in the parent (sticker Colour is often empty). **Packs colour is later** — do not use Item 1–10 Colour (often different; guessing Item 1 breaks definite-match; dumping mixed packs to unmatched is worse). Packs still split on Areeb + Brand Name + Pack Size. Pack colour does **not** unmatched. |
| resend | process files | **ShipStation** tag **`1014-ALL-RESEND` only** | Exact tag on the **order** → filename **`RESEND` only** (no slots). Whole order regardless of plain/printed/prime. **Do not** treat `1015-ALL-RESEND MANUALLY DISPATCHED`, `1016-ALL-RESEND PRIME`, or `1017-BULK-RESEND MAKING` as resend. Those follow normal grouping (or `UNMATCHED` if they fail a definite match). |
| shift fill | intake + **folder** + **filename** | **configuration** | Company has 3 shifts. **Do not** use 300/100/100 as write caps (Hashim #037). Testing: every `--run` writes **`1st Shift` / `S1`** and replaces those CSVs. Production later: 1st `--run` of the day → 1st Shift, 2nd → 2nd, …. Ignore existing ShipStation shift tags (`001-1st Shift`, …). **Folder** matches Packing. **Filename field 1** (after optional floor prefix): `S1` / `S2` / `S3` / …. `RESEND` / `UNMATCHED` have no shift slot in the name; they land in **this run’s** shift folder. Locked 2026-09-15; field order moved 2026-09-22. |
| order pool | intake | **ShipStation API only** | Fetch **all** `awaiting_shipment`. **No file intake** (CSV has no tags). Skip tag `post-order-designs`. |
| app split | — | — | **Order Grouping Sorter** (new first-level folder, outside Packing): reads ShipStation `awaiting_shipment` + the three catalogs; writes **one CSV per batch** into Packing `Input/{date}/{shift}/`. CSV shape = Packing current-view columns (`Order #`, `Ship By`, `Quantity`, `Item SKU`, …). **Packing:** filename = full batch name; Process Number Tracker off; PIN `{B}-S{n}-{process_number} Item {item}` (batch+shift only). |
| parts | process numbers inside batch | **50 units** (Packing PDF threshold) | Every 50 units → next process number (`-N`) inside the same batch. Not a new batch file. Replaces CEO graph `0–30` / `31–60` / `61–90`. |
| colour then parts | inside batch | colour 3+ then 50-unit process numbers | **Colour 3+ groups first**, then 50-unit process numbers inside those groups. Same customer order stays on **one process number** (a split must not break an order across process numbers). Packs skip the colour-group step. |
| process name | batch filename | **6 fields** (logic still Graph + fixed-batch overlay) | Filename: `{B}-S{n}-{finish}-{1\|2}-{supply}-{R\|P}-{priority}`. Fixed batches use the locked codes in `fixed_batches.csv` (`B10`…`B8050`, 2026-09-28). Leftover uses `B1`/`B2`/… skipping reserved. **Packing PIN** (not the filename): `{B}-S{n}-{process_number} Item {item}`. Process Number Tracker is off. Locked field order 2026-09-22; cousins retired 2026-09-23; **B** prefix + leftover B1… + short PIN 2026-09-23. |
| design grouping | process files when flag `1` | **configuration** (per scenario) | Off now. When on: slot is `group-01`… from **that scenario’s** Design ID / logo list. |
| print size | off in v1 | **CL DB** `Print Size 1` | Do not split in first version. |
| print position | off in v1 | **CL DB** `Print Positions` | Do not split in first version. |
| customisation type | off in v1 | **CL DB** `Customisation Type` | Column present. Values empty. Slot `x` until a fill rule exists. Plain/Packs do not need this column. |

### Plain vs printed (locked)

Finish comes from database hit (with an explicit SKU override):

1. If Item SKU contains `plain` / `plainlg` → **plain**
2. Else if CL DB matches `Custom Label` using **after first dash**, or **whole SKU when there is no dash** → **printed**
3. Else if Plain Database matches `SKU` using **till last dash** (or whole SKU) → **plain**
4. Else if Packs Database matches **whole SKU** (`Channel Child SKU`) → **plain**
5. Else → **`unmatched`**

`Customise = Yes` is a **printed** split (CL), not the plain/printed gate. Mixed P vs R in one order: majority printed units; tie → readymade. DTF-transfer / `PER` / SET: see locked section below.

## Order Grouping Sorter (step 3, locked 2026-09-10)

New app folder **`Order Grouping Sorter`**. Not inside Packing. Reads ShipStation + CL + Plain Database + Packs. Writes into Packing `Input/{DD-MM-YYYY}/{shift folder}/`.

**v1 filename (locked 2026-09-14, short names for Windows MAX_PATH; shift-first 2026-09-22; fixed-batch `B` prefix 2026-09-23; leftover `B1`/`B2`… 2026-09-23):** six fields only — `S{1\|2\|3}-{PLAIN\|PRINTED}-{1\|2}-{WAREHOUSE STOCK\|SUPPLY ON DEMAND\|IN HOUSE MANUFACTURE}-{R\|P}-{priority}`. **Fixed batches** prefix their code from `fixed_batches.csv` (2026-09-30 set: `B10` / `B40` / `B50` / `B70` / `B80` / `B90` / `B100` / `B1000` / `B1050` / `B1080` / `B2300` / `B2400` / `B3100` / `B3500` / `B3600` / `B3700` / `B4000` / `B5000` / `B5080` / `B5500` / `B8000` / `B8050`) **before** the shift token. **Leftover** plain piles prefix `B2000`, `B2100`, `B2200`, `B2500`, `B2600`, `B2700`, …; printed leftover piles prefix `B1`, `B2`, `B3`, …; both **skip** reserved numbers. Special names **`RESEND`** and **`UNMATCHED`** have no `B` code. Inside each **batch**: colour 3+ groups first (not packs), then 50-unit **process numbers**. **Packing PIN** uses only `{B}-S{n}-{process_number} Item {item}` (not the full filename).

**Graph 30-chain still runs** (same as 2026-09-11). It still peels leftover bins at ≥30. Those peel values do **not** go in the filename.

**Graph 30-chain locked 2026-09-11 (CEO Graph is source of truth):** same sequential `30` for plain and printed (category → product-type → product-style → department → brand → size → colour). Under 30, do not go deeper — e.g. 29 short-sleeve t-shirts stay one process, all departments together. Printed department/size are not always-split. Printed brand is not skipped.

**Graph ship-by-date binary (locked 2026-09-11, filename dropped 2026-09-14, Hashim #037 2026-09-15):** today/overdue always get CSVs this run. Future is written too. Mix today+later in one process only when eligible **orders** ≤ 300; **above 300** split today vs later dates. Do not dump overflow into Shift 2/3. Filename has no today/future slot. A mixed pile counts as **today** for priority if it has any due/overdue order.

**Hashim Shift-1 overload (locked 2026-09-15, tracker #037):** Company has 3 shifts. When Shift 1 **order** volume for a day is **above 300**, split by **date** (today vs later ship-by). **Do not** dump overflow into Shift 2/3 as capacity caps. Wrong: 3000 orders → Shift1 300 + Shift2 100 + Shift3 100, rest lost. All eligible orders still get CSVs this run (today piles and later-date piles). Testing rewrites `1st Shift` each `--run`; nth-run = nth shift is production later (`SHIFT_PER_RUN`).

**Priority field 6 (locked 2026-09-15):** per shift, packing-list order is **today first**, then **prime first**, then as files are made (fixed batches, then leftover Graph/30-chain bins). Number `1`, `2`, `3`… in that order. Further ranking later.

**First Input write 2026-09-11** (supervisor **run**). One CSV per process into Packing `Input/{DD-MM-YYYY}/{shift}/`. Testing: **`1st Shift`** every `--run`. `RESEND.csv` / `UNMATCHED.csv` land there. Default CLI stays dry-run; `--run` writes. Production later: nth `--run` of the day = nth shift.

**Fixed batches locked 2026-09-12** (match logic unchanged 2026-09-14; cousins removed 2026-09-23; renamed from “named floor” + **`B` prefix 2026-09-23**; **criteria table 2026-09-23**). Source of truth: `database/order-grouping-sorter/fixed_batches.csv`. Criteria columns (Graph order): `order-status`, `ship-by-date`, `product-finish`, `order-source`, `design-grouping`, `shipping-service`, `printing-method`, `customised`, `customisation-type`, `print-size`, `print-position`, `supply-method`, `supplier`, `package-type`, `category`, `product-type`, `product-style`, `department`, `brand`, `size`, `color`. Cell `any` / `x` / blank = do not care. After classify, matching orders take the fixed-batch `batch_code` as a **prefix** on the 6-field filename and **skip the 30-chain**. The prefix is the **same code every shift** (`B100` stays `B100` on S2/S3). Intake / unmatched / resend / inside-file `-N` stay as already locked. Leftover still uses Graph + 30-chain to choose bins; on-disk name is the 6 fields only.

| Batch | Batch name | Match (all must hold) |
|---|---|---|
| B3500 | Glow In The Dark | any line Item Name contains `Glow In The Dark` (hyphen/spacing variants count). First-match peel (above FOTL). |
| B5500 | Design 179975LG | any line Item SKU contains `179975LG`. First-match peel (above FOTL). |
| B1050 | Stickers | any line Item SKU contains `STICKER`. Contain peel (above iron-on / Gildan). Manual floor 1050. |
| B40 | Gildan T-Shirts | printed + `gildan_tee`: Brand Gildan + Category T-Shirts, **or** style token `5000` / `G5000` in Item SKU or Gender Apparel (not a substring of `15000`). Manual floor 40. |
| B3700 | Sweatshirts | printed + Product Type (Areeb) = Sweatshirt (not Hoodie). Manual floor 3700. |
| B80 | Fawad Short Sleeve FOTL T-Shirts Ready-Made | printed DTF, MAS Clothing, non-prime, readymade, Warehouse Stock, Category T-SHIRTS, short-sleeve / kids tee (not long sleeve) |
| B90 | Fawad Short Sleeve FOTL T-Shirts Personalized | same as B80, CL Customise = Yes |
| B100 | Short Sleeve FOTL T-Shirts Ready-Made | same, store **own** (not MAS) |
| B1000 | Iron-on Ready-Made | printed DTF, own, readymade, In House Manufacture, Category Iron-On (not sticker). **Prime stays in this file** (manual 1000 was mostly Prime Letter) |
| B1080 | Fawad Iron-on Ready-Made | same, MAS Clothing |
| B4000 | Short Sleeve FOTL T-Shirts Personalized | own, non-prime, CL Customise = Yes, FOTL short-sleeve |
| B5000 | Iron-On Personalized | own, Customise = Yes, iron-on (not sticker) |
| B5080 | Fawad Iron-On Personalized | MAS Clothing + Customise = Yes + iron-on |
| B8000 | Short Sleeve FOTL T-Shirts Ready-Made Prime | own, tag `Amazon Prime Order`, readymade, FOTL short-sleeve |
| B8050 | Short Sleeve FOTL T-Shirts Personalized Prime | own, Prime tag, personalised, FOTL short-sleeve (was B8060) |

Table above is the 2026-09-12 set; **superseded by the 2026-09-28 lock below** (live source: `fixed_batches.csv`).

**Fixed-batch revision locked + built 2026-09-28** (priority = CSV row order: B5500, B3500, B1050, B10, B70, B3100, B3600, B3700, B40, B8050, B8000, B90, B80, B4000, B100, B50, B5080, B1080, B5000, B1000, B2400, B2300; then plain sequence / leftover). `-Yes` in SKU and `Personali` / `Custom` in Item Name mark personalised, so those exclusions sit on **ready-made rows only** (B100 / B50 / B80 / B8000 / B1000 / B1080). Dry-run prints `fixed-batch overlaps` (orders that also met a lower batch). supervisor sent new batches (B10 International, B70 Mugs, B2000/B2100/B2200/B2500/B2600 Plain 1–5, B2300 Uneek Plain, B2400 Packs Plain, B3100 Baby Suits, B3600 Hoodies) and tightened B100 / B1000 / B1080 / B5500 (B5500 = SKU `179975LG` **and** Item Name `Dancing Queen`). Rule: **no batch overlap** — narrow peels (Dancing Queen, Glow) sit above broad ones. Locked so far: **B90 and B1050 stay; B8050 replaces B8060.** **Personalised (fixed batches) = CL `Customise` = Yes OR any line Item Name contains `Personali` / `Custom`** (case-insensitive); otherwise ready-made. **Priority top: B5500 Dancing Queen → B3500 Glow In The Dark → B1050 Stickers always win (own batch, even when international); B10 International comes next, above every other batch.** **B10 International = ShipStation `shipTo.country` is not `GB`** (Jersey / Guernsey / Isle of Man count as international). **Design-code SKU tokens (`M61`, `M55`, `M118`, …) match a whole dash-separated SKU part only** (`M61` hits `…-M61-…`, not `M610`). Text needles (`STICKER`, `-t-`, `IronOn`, `179975LG`, `-Yes`, …) stay case-insensitive contains. **Plain batches 1–5 = sequence, not criteria:** plain piles (after Uneek B2300 / Packs B2400 peel) still split by Graph + 30-chain, and take codes in the order made: `B2000`, `B2100`, `B2200`, `B2500`, `B2600` (instead of leftover `B1`/`B2`/…). Example 2026-09-28: B1–B4 plain → B2000 / B2100 / B2200 / B2500. 6th+ plain pile → `B2700`, `B2800`, … (skip reserved). **T-shirt family (replaced 2026-09-29; SKU include list and 62023LG/115881LG/115883LG/85677LG exclusions dropped):** all keep catalog FOTL short-sleeve (`ss_fotl`), printed, DTF. **B100** = own, no Prime tag, ready-made, **Warehouse Stock**, Item Name not `Personali;Custom;Glow In The Dark;Add Your Name Soccer;Dancing Queen`, Item SKU not `sticker;-Yes;-SS-;-H-;IronOn`. **B50** = same as B100 but **Supplier On Demand** (colors ordered; arrive later) — locked 2026-09-30; mirrors for B4000/B80/B90/primes not yet. **B8000** = B100 + Prime tag. **B4000** = own, no Prime tag, personalised FOTL tee (not Gildan — Gildan is B40 above), Item Name not `Glow In The Dark;Dancing Queen`, Item SKU not `sticker;-SS-;-H-;IronOn`. **B8050** = B4000 + Prime tag. **B80 / B90 (MAS Clothing, non-Prime) mirror B100 / B4000** (same exclusions), store = MAS Clothing (supervisor confirmed 2026-09-29). **B70 Mugs = printed + (Item SKU contains `MUG` OR SKU token `M61` OR CL Printing Type = Sublimation).** **B3100 Printed Baby Suits = printed + (SKU token `C800T` / `C8020T` / `C8030T` OR Product Type (Areeb) = `Body Suit`).** **B3600 Printed Hoodies = printed + Product Type (Areeb) `Hoodie` or `Zip Hoodie`** (`T-Shirt & Hoodie` bundle stays leftover). **Iron-on family (B1000 / B1080 / B5000 / B5080) = catalog iron-on (`iron_on`) OR Item SKU contains `IronOn`**, and always: Item SKU not contains `sticker`; Item Name not contains `Glow In The Dark` (ready-made rows also not `-Yes` in SKU and not `Personali;Custom` in name). Store own vs MAS Clothing and ready-made vs personalised as before; Prime stays in these batches. **Plain peels (before plain sequence): B2400 Sets/Packs = plain + any line hits Packs Database; then B2300 Uneek = plain + every line Supplier Name `Uneek Clothing`.**
Fixed-batch CSVs live in the shift folder (`Input/{date}/{1st|2nd|3rd} Shift/B100-S{n}-PRINTED-2-WAREHOUSE STOCK-R-1.csv`). Same batch code every shift; shift is only `S{n}`. Leftover Graph piles use **`B1` / `B2` / …** (skipping reserved fixed-batch numbers) plus the same 6 fields. Today and later dates in the same batch merge **only** when eligible orders ≤ 300; above 300 they split. Mugs, packs, plain, hoodies, Fawad Prime FOTL wait for later fixed codes (leftover `B1`… names until then). Design-token FOTL stays in the B100/B50 family by supply method. Fawad personalised FOTL is **B90**.

**B50 locked 2026-09-30:** own / non-prime / ready-made FOTL short-sleeve **Supplier On Demand** — same match rules as B100 except supply-method. B100 = colors kept in warehouse and restocked; B50 = colors ordered, arrive later. `ss_fotl` = Brand Fruit of the Loom + short-sleeve T-Shirts; Warehouse Stock vs On Demand is the CSV supply-method cell only. Scope is **B50 only** (no B4000 / B80 / B90 / primes On Demand mirrors).

**Leftover batches CSV locked 2026-09-23:** each sorter run (dry-run and `--run`) writes `database/order-grouping-sorter/leftover_batches/{YYYY-MM-DD}.csv` with the same columns as `fixed_batches.csv`. One file per run date; overwritten on the next sorter run for that date. Rows = leftover `B1`/`B2`/… piles only (Graph + 30-chain slots). Fixed-batch codes are not listed. Path: `shared.paths.sorter_leftover_batches_path`. Writer: `Order Grouping Sorter/scripts/leftover_batches.py`.

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
| `Warehouse Stock` | **CL (2026-09-23):** FOTL men / women / kids t-shirts **in the locked colour lists only**, plus Kids body styles `C800T` / `C8030T` in Black, Lemon Yellow, Light Blue, Light Pink, Red, Sports Grey, White. **Plain / Packs:** FOTL men / women / kids t-shirts (no colour list). | CL tee: FOTL identity **and** `Category (Areeb)` is `T-SHIRTS` **and** not vest/tank **and** `Department (Areeb)` is Mens / Womens / Kids **and** `Colour` is on that department’s list (exact cell). Ladies = Womens. CL body: Kids **and** Custom Label / Gender Apparel / Supplier Product Code contains `C800T` or `C8030T` **and** colour on the body list. Not `C8020T`. Not `BZ10-Body Suit`. Deep Navy is not Navy. Two-tone colours are not stock. Plain / Packs: FOTL identity and t-shirt category, no colour gate. |
| `In House Manufacture` | Iron-on **or sticker**, made in the warehouse | CL only: **Custom Label** (SKU) or **Gender Apparel** contains `iron on` / `ironon` / `iron-on` / `sticker` (hyphens and spaces ignored). **Never** written on Plain or Packs. |
| `Supplier On Demand` | Everything that is not warehouse stock | Default. Includes Gildan tees, FOTL tees whose `Colour` is off that department’s list, FOTL hoodies/polos, vests/tanks, bags, Uneek, `C8020T`, China bags (the old `Warehouse Stock` = Yes column is **not** this field). |

Do **not** reuse CL `Warehouse Stock` (32 China bags marked Yes). Gildan brand always wins over a `Womens-T-Shirt` Gender Apparel token.

**Filled 2026-09-09** (overwrite all rows; backups first). 0 blanks.

| File | Rows | Warehouse Stock | In House Manufacture | Supplier On Demand | Backup |
|---|---:|---:|---:|---:|---|
| Custom_Label_Database.csv | 131,892 | 83,801 | 453 | 47,638 | `database/shared/custom_label/backups/Custom_Label_Database.bak_20260909_170833.csv` |
| Plain Database.xlsx | 78,039 | 2,530 | 0 | 75,509 | `database/shared/plain/archive/Plain Database.bak_20260909_170955.xlsx` |
| Packs Database.xlsx | 38,452 | 17,252 | 0 | 21,200 | `database/shared/packs/archive/Packs Database.bak_20260909_171153.xlsx` |

**CL colour gate filled 2026-09-23.** Overwrite `Supply Method` only. Backup `database/shared/custom_label/backups/Custom_Label_Database.bak_20260923_103520.csv`. Plain / Packs not rewritten.

| File | Rows | Warehouse Stock | In House Manufacture | Supplier On Demand | Wrote |
|---|---:|---:|---:|---:|---:|
| Custom_Label_Database.csv | 132,224 | 63,399 | 458 | 68,367 | 21,728 |

21,213 FOTL tees left Warehouse Stock (colour off that department’s list). 515 entered: C800T 416 + C8030T 99.

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
