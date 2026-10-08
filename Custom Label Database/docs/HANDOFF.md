# Custom Label Database — current state

**Updated:** 8 October 2026 (M256)  
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
