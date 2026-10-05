# Custom Label Database — current state

**Updated:** 5 October 2026  
**Handbook:** `AGENTS.md` · Parent: `../AGENTS.md` · **Facts:** `FINDINGS.md` · **Paths:** `WORKSPACE.md` · **Policy:** parent `.cursor/rules/custom-label-database/`  
**Dated fill log (archive):** [`../../backups/docs/custom-label-database/HANDOFF_FILL_LOG.md`](../../backups/docs/custom-label-database/HANDOFF_FILL_LOG.md)

## Live

| File | Role |
|------|------|
| `database/shared/custom_label/Custom_Label_Database.csv` | Live catalog |
| `database/custom-label-database/support/Size References.csv` | Size References (no SKU Value 2/3) |
| `database/custom-label-database/support/` | Shirts Print Sizes, Mocks, Workbook helpers |
| `Database Transfer/Workbook.xlsx` + `Configuration Workbook.xlsx` | Mirror after fill via `sync_database_transfer.py` (locked 2026-09-25) |

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
