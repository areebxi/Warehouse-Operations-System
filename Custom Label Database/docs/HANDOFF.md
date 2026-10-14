# Custom Label Database — current state

**Updated:** 13 October 2026 (M257-138262 fill)

**13 Oct 2026 — M257-138262:** Appended one row to live `Custom_Label_Database.csv` (id 129891) and `Custom_Label_Database (Areeb).csv`. BTC UID 138262 / SPC 61019: Kids-T-Shirt, Orange, 12-13 Years, Front Center A4 250×353, DTF, BTC Activewear, Warehouse Stock. Areeb: T-Shirts / Short Sleeve T-Shirt / Standard / Kids. Customise left blank. Print position follows the 5-6 sibling (Front Center); the 7-8 sibling stays pocket + back. NocoDB was not updated. Backups `backups/custom-label/Custom_Label_Database_preAdd_20261013_144311.csv` and `Custom_Label_Database (Areeb)_preAdd_20261013_144311.csv`. Database Transfer sync: CL Database 129,891 rows, Size References 97,845 rows. Backups `backups/database-transfer/Workbook_preSync_20261013_144343.xlsx` and `Configuration Workbook_preSync_20261013_144343.xlsx`.

**13 Oct 2026 — unmatched fill:** Areeb catalog +2 labels the sorter keys literally. `M281-P5-C800T-30-0to3` cloned from `M281-P5-C800T-30-0-3` (White, 0-3 Months, 110×150, Customise Yes, product code C800T, Absolute Apparels, Warehouse Stock, Babywear / Body Suit / Baby Body Suit / Kids). `M281-P3-C800T-30-3&gt;6` cloned from `M281-P3-C800T-30-3>6` (White, 3-6 Months, same print and supply). Live `M281-P5-C800T-30-0to3` (id 129886) was Light Pink / 6-12 Months / supplier SKU `C800T-52-6>12` / supplier `Absolute` / blank Areeb; now White / 0-3 Months / `C800T-30-0>3` / Absolute Apparels / Warehouse Stock / the four Areeb cells above. Plain Database +4 Absolute price-list hoods (not babysuits): `AA22-36-L`, `AA22-36-M` (Black L/M), `CRBHS30-105-M` (Chocolate M), `C2200-36-S` (Black S). Supplier On Demand, supplier Absolute Apparels. `92802` was already Plain (FOTL 62039, BTC). Already matched on Areeb, not rewritten: `B-K-T-NVY-YXXL-YES`, `M235-P2-138219`, `M281-P3-C800T-30-3>6`. Not a catalog SKU: `4512342670`. NocoDB was not updated. Backups `backups/custom-label/Custom_Label_Database_preFill_20261013_053113.csv`, `Custom_Label_Database (Areeb)_preFill_20261013_053113.csv`, `backups/plain/Plain Database_preFill_20261013_053113.xlsx`.

**12 Oct 2026 — add two labels:** `M281-P3-C800T-30-3>6` was already on the live file (id 128034, White, 3-6 Months, 110×150, product code C800T); Customise was blank and is now `Yes`, and the four Areeb columns are Babywear / Body Suit / Baby Body Suit / Kids. Appended to the Areeb file (Absolute Apparels, Warehouse Stock). `M-SS-FGRN-XL-YES` added to both files, cloned from `M-SS-FGRN-XL`: Mens-Sweatshirt, Forest Green, Extra Large, Customise Yes, Front Center 267×378, BTC product code 18000, SKU 52925, Supplier On Demand. Backups `backups/custom-label/Custom_Label_Database_preAdd_20261012_150837.csv` and `Custom_Label_Database (Areeb)_preAdd_20261012_150837.csv`. Database Transfer sync: CL Database 129,887 rows. Backups `backups/database-transfer/Workbook_preSync_20261012_150901.xlsx` and `Configuration Workbook_preSync_20261012_150901.xlsx`. NocoDB was not updated.

**12 Oct 2026 — preflight fill:** Live `Custom_Label_Database.csv` and `Custom_Label_Database (Areeb).csv`. `M280-IronOn-A3` was blank (unmatched): now DTF-IronOn-A3 / Iron On Sticker / A3 / Front Center 297×420 / product code `A3O` / In House Manufacture / DaataaDirect / Iron-On · Iron-On Transfer · A3 · General. Customise left blank (no `Yes` or `-P#` token). `M235-17258`, `M257-138259`, `M257-138260` were already on the live file with product codes `61033` / `61019` / `61019` and shirt mm (5-6 Years 222×315; 7-8 Years pocket 80×100 and back 250×353) — appended to the Areeb file only. W415 print mm corrected to the locked chart (60×100, 100×140, 160×200, 230×260, 320×380, 480×530). Areeb gained `W415-NAT-M-Yes`. Backups `backups/custom-label/Custom_Label_Database_preFill_20261012_145906.csv` and `Custom_Label_Database (Areeb)_preFill_20261012_145906.csv`. Live `M280-P5-IronOn-A3` (id 129850) is still sized as A4 (210×297). NocoDB was not updated. Database Transfer sync: CL Database 129,886 rows, Size References 97,845 rows. Backups `backups/database-transfer/Workbook_preSync_20261012_150020.xlsx` and `Configuration Workbook_preSync_20261012_150020.xlsx`.

**10 Oct 2026 — Areeb size correction:** `Custom_Label_Database (Areeb).csv` line that was `SF500B-SND-YL` / `7-8 Years` → `9-11 Years` (YL is 9–11; YM is 7–8). The other `SF500B-SND-YL` row was already `9-11 Years`. Print mm unchanged (250×353). Backup `backups/custom-label/Custom_Label_Database (Areeb)_preSize_20261010_111059.csv`. Live NocoDB export still has one `SF500B-SND-YL` at `7-8 Years` (line 129112) — not edited locally. No Database Transfer sync.

**10 Oct 2026 — Areeb append unmatched:** +4 rows on `Custom_Label_Database (Areeb).csv`. `M280-P5-IronOn-A3` (A3 iron-on, 297×420, In House Manufacture, DaataaDirect; live row was sized as A4). `IronOn-A4` (A4 iron-on, 210×297, same supply). `F/B-M-T-NVY-2XL-YES` (Mens-T-Shirt, Navy, 2XL, Warehouse Stock, DTF, BTC). `N01-P7-67362` (Gildan Softstyle Youth, Red, Small, Supplier On Demand, DTF, BTC). Backup `backups/custom-label/Custom_Label_Database (Areeb)_preAdd_20261010_094255.csv`. No Database Transfer sync.

**9 Oct 2026 — Areeb append 2nd Shift unmatched:** +2 rows. `M-H-DCHC-XL` (Mens-Hoodie, Dark Chocolate, Extra Large, Supplier On Demand, DTF, BTC; Sweatshirts & Hoodies / Hoodie / Standard / Mens; print 267×378). `M95-138248` (FOTL Kids Original T, Red, 7-8 Years, Warehouse Stock, DTF, BTC; T-Shirts / Short Sleeve T-Shirt / Original / Kids; print 250×353; BTC UID 138248 / SPC 61019). Backup `backups/custom-label/Custom_Label_Database (Areeb)_preAdd_20261009_120302.csv`. No Database Transfer sync.

**9 Oct 2026 — Areeb append unmatched:** +6 rows on `Custom_Label_Database (Areeb).csv`. `M235-17260` / `M235-17259` (FOTL Kids Valueweight T, Light Pink, 9-11 / 7-8 Years, Warehouse Stock). `N07-P2-67364` (Gildan Softstyle Youth, Red, Large, Customise Yes, Supplier On Demand). `A415` (Photo Acrylic, A4 15mm, Customise Yes). `M-T-CARBE-2XL-YES` (Mens-T-Shirt, Carolina Blue, 2XL, Customise Yes; live row had Purple / Large, so colour and size came from the label and the order). `ACLR-5mm-A6-POR-4C` (Photo Acrylic, Clear, A6, Printing Type UV, Supplier Name DaataaDirect; cloned from live `ACLR-5mm-A5-POR-4C`). Backup `backups/custom-label/Custom_Label_Database (Areeb)_preAdd_20261009_065504.csv`. No Database Transfer sync.

**9 Oct 2026 — sorter CL file:** Order Grouping Sorter temporarily reads `Custom_Label_Database (Areeb).csv` (`cl_areeb_csv_path`) so the four Areeb columns are the filled ones. Live catalog for every other app remains `Custom_Label_Database.csv`.

**Handbook:** `AGENTS.md` · Parent: `../AGENTS.md` · **Facts:** `FINDINGS.md` · **Paths:** `WORKSPACE.md` · **Policy:** parent `.cursor/rules/custom-label-database/`  
**Dated fill log (archive):** [`../../backups/docs/custom-label-database/HANDOFF_FILL_LOG.md`](../../backups/docs/custom-label-database/HANDOFF_FILL_LOG.md)

## Live

| File | Role |
|------|------|
| `database/shared/custom_label/Custom_Label_Database.csv` | Live catalog |
| `database/custom-label-database/support/Size References.csv` | Size References (no SKU Value 2/3) |
| `database/custom-label-database/support/` | Shirts Print Sizes, Mocks, Workbook helpers |
| `Database Transfer/Workbook.xlsx` + `Configuration Workbook.xlsx` | Mirror after fill via `sync_database_transfer.py` (locked 2026-09-25) |

**8 Oct 2026 — Areeb append W696:** +1 row `W696-DUSGN-O/S-Yes` (was missing; siblings `W696-BLK` / `W696-DUSBE` already present). Colour `Dusty Green` (`dusgn` bag map). Print Front Center 520×310 mm. Supply Method `Supplier On Demand`, Printing Type `DTF`, Supplier Name `BTC Activewear`, Areeb Bags / Tote / Oversized Canvas Tote / General. Backup `backups/custom-label/Custom_Label_Database (Areeb)_preAdd_20261008_130230.csv`. Live NocoDB already has this label (id 129874) with colour `Black` and the same 520×310 print.

**8 Oct 2026 — Areeb append M256:** +134 rows `M256-{UID}` for BTC SPC `61082` (asked label `M256-56307`, Orange / 2XL). Print position Front Center (Mocks Database printing position blank; same as other FOTL Original T peers). Print sizes from Shirts Print Sizes A4 by size band (no Size References `M256 (UID)` row): Small 237×336, Medium/Large/XL/2XL 267×378, 3XL/4XL 318×450, 5XL 357×504. Supplier Product Code `61082`, Printing Type DTF, Supplier Name BTC Activewear. Backup `backups/custom-label/Custom_Label_Database (Areeb)_preAdd_20261008_045244.csv`. No Database Transfer sync. Sorter still reads live NocoDB CSV.

**8 Oct 2026 — NocoDB insert:** `W121-WHILY-L-Yes` inserted as id `129876` (cloned from `W121-WHILY-S-Yes`; Size Large; `Supplier_SKU` `201416`; `Stock_Type` `Order on Demand` to match the other W121 rows). Same row appended to live `Custom_Label_Database.csv`. Backup `backups/custom-label/Custom_Label_Database_preW121L_20261008_053038.csv`. Full `db_update.py` was not used (it deletes rows missing from the CSV). No Database Transfer sync.

**8 Oct 2026 — Areeb append (awaiting shipment unmatched):** +1 row `W121-WHILY-L-Yes` (packing `129115LG-W121-WHILY-L-Yes`). Seed from size peer `W121-WHILY-S-Yes`: BG-W121 / Soft White-Light Grey / Large / Customise Yes. Filled Supply Method `Supplier On Demand`, Supplier Name `BTC Activewear`, Printing Type `DTF`, Areeb `Bags` / `Tote` / `Cotton Ribbon Cord Bag` / `General`. Backup `backups/custom-label/Custom_Label_Database (Areeb)_preAdd_20261008_044646.csv`. Not added: `SET43875` (order `01-15285-21701`) — no CL / Plain / Packs hit; not a Custom Label. Later the same label was inserted into NocoDB (see above). `cl_standard` now also reads spaced `Gender Apparel` so Areeb fills on this CSV.

**7 Oct 2026 — Areeb reference append (supervisor):** `Custom_Label_Database (Areeb).csv` +1 row `K-SS-PRP-YXS-YES` (from unmatched packing `48811LG-K-SS-PRP-YXS-YES`). Seed: Kids-Sweatshirt / Purple / 3-4 Years / Customise Yes; filled Supply Method `Supplier On Demand`, Supplier Name `BTC Activewear`, Printing Type `DTF`, Areeb `Sweatshirts & Hoodies` / `Sweatshirt` / `Standard` / `Kids`. Backup `backups/custom-label/Custom_Label_Database_(Areeb)_preAdd_20261007_085505.csv`. Already present in Areeb (skipped): `A515`, `M407-P3-1D112`. No Database Transfer sync (that mirrors live NocoDB CSV, not Areeb). Sorter still reads live NocoDB CSV.

**7 Oct 2026 — Areeb append batch 2:** +4 rows — `BG-BG42-ORN-O/S-YES`, `BG-BG42-BRIRL-O/S-YES`, `N220-P3-138131` (cloned seed from live NocoDB row), `M260-P1-120853`. Skipped already-present `BG-BG145-FucBk-O/S-YES`. Bag colour map gained `orn`→Orange, `brirl`→Bright Royal (`add_labels_parse.py`). Backup `backups/custom-label/Custom_Label_Database_(Areeb)_preAdd_20261007_090335.csv`.

**Source of truth (4 Oct 2026 evening):** CL is managed online (NocoDB / Postgres). Local live CSV is refreshed by `scripts/cl_db_exporter.py` → `database/shared/custom_label/Custom_Label_Database.csv` (underscored headers as exported — **no remap**). Prior local copy kept as reference only: `Custom_Label_Database (Areeb).csv`.

Last NocoDB export (4 Oct 2026 ~20:11): **129,862** rows, **75** columns. Warehouse hot paths (Packing enrich, Queue print sizes, Sorter catalogs, PO stock_resolver, shared classifiers) read NocoDB names via `shared/cl_columns.py`. Stand-ins locked 2026-10-04: retired `BTC SKU` → `Supplier_SKU`; retired `Supply Method` → `Stock_Type` with `normalize_stock_type` (`Order on Demand`→`Supplier On Demand`; Seasonal/Non-Seasonal→`Warehouse Stock`; blank stays blank). Areeb taxonomy cols still spaced (`Category (Areeb)`, …). Packing PIN/Excel/PDF column names unchanged. CL app fill scripts are **not used** while CL is NocoDB-owned.

Earlier 4 Oct local fills (Areeb-era reference era): +330 PO WC append; WC `BTC Stock ID` → `BTC SKU` (324; 6 blank); `M-T-TBL-XL` → `146241` / `64000`; dedicated supplier fill **83,442** `BTC SKU` / **83,205** `BTC Product Code`. Backups under `database/shared/custom_label/backups/`.

## How fills run

No live write without **yes / fill / run**. Propose + dry-run first. Typical path: `add_labels.py` / `fill_from_seeds.py` → `fill_size_references_from_cl.py` → **`sync_database_transfer.py`**. Fast add is append-only (`add_labels.py`). `add_labels` peers (locked with 2 Oct UNMATCHED fill): `N##` mocks; `-Yes` colour-family size peers; bag `ClaPk` → Classic Pink; alnum acrylic codes without PE peer → `A515-PHOTO`. Policy and column rules live in parent `.cursor/rules/custom-label-database/` — do not re-decide them here.

## Standing do-nots (reminders)

- Apparel Image: blanks only. Duplicates: leave unless asked. NocoDB: no column-name normalization.
- Do not put Packs/Plain SKUs into CL to “fix” unmatched.
- Chat is not memory; do not copy transcripts into `docs/chats/`.

## Current leftovers (ask before acting)

1. BTC dedicated cols — **4,945** BTC Activewear rows still blank `BTC SKU` (no Supplier SKU / PE UID). Filled blank-only 2026-10-04: 83,442 BTC SKU / 83,205 BTC Product Code.
2. Non-shirt Width 1 blanks (~485 historically): stickers/mugs/caps/bags/aprons/beanies — mm until catalog/override has sizes.
3. `--all-mocks` image download (~189 `M##` files left) — does not change CSV.
4. `generate_from_mocks` — ~293 guide IDs not in DB.
5. `Tags` / `Size (Dimensions)` — blank unless asked.
6. No PE UID (~5,908) — PE Category/Department/Brand stay blank; Areeb still from Gender Apparel (`areeb-taxonomy.mdc`).
7. PE Department/Sub Department corrections — `--overwrite-pe-taxonomy` (dry-run first) when PE worksheet is fixed; Brand blank-only.
8. 24 Aug tail seed drift (29 rows) — known GA/colour/size quirks; see archive fill log.

## Useful commands

```text
export_cl_db.bat
python scripts/cl_db_exporter.py
python scripts/fill_size_references_from_cl.py --dry-run
python scripts/fill_from_seeds.py --dry-run
python scripts/fill_from_seeds.py --steps sku,pe --overwrite-pe-taxonomy --dry-run
python scripts/add_labels.py --skus …
python scripts/sync_database_transfer.py
```

Double-click repo-root `export_cl_db.bat` (or run from warehouse root) to replace live `Custom_Label_Database.csv` from NocoDB. Needs supervisor **run** / **yes**.

If the live CSV is locked: filler writes `Custom_Label_Database_write_fallback.csv`. Close the live file, then swap.
