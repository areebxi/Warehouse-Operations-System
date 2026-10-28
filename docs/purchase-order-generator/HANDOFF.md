# Purchase Order Generator — snapshot

**Updated:** 28 October 2026 (warehouse-root Output)  
**Handbook:** `AGENTS.md` · **Layout:** `FOLDER_LAYOUT.md`

## Continue here

- Launch: `Run_GUI.bat` (creates `.venv`, runs GUI).
- Live DB under `database/purchase-order-generator/` + shared catalogs; outputs under `Output/Purchase Order Generator/`.
- Stock CL map: `database/shared/custom_label/Custom_Label_Database.csv` (`Supplier_SKU` via `shared/cl_columns.BTC_SKU` — no `BTC Stock ID`). Areeb spaced headers (`Custom Label`, `Supplier SKU`, blank `Supplier SKU` falling back to `BTC SKU`) are accepted through `rename_legacy_headers`. Live file remains the NocoDB export.
- GUI can override Custom Label CSV, Plain Database, and Packs Database (Browse… / Remove); remembered in `database/purchase-order-generator/gui_settings.json` with PDF copy folder. Empty/Remove = shared defaults. Packs default is `database/shared/packs/Packs Database.csv`.
- **Product Images folder** is required (Browse… / Remove). Remembered as `product_images_dir` in the same `gui_settings.json`. No fallback to `assets/product_images`. Remove clears the path only; PDF product shots stay blank and `download_product_images` refuses until Browse again (or `--product-dir`). Brand logos still under `assets/brand_logos/`.
- Sync DB from BTC Product Data / download images with scripts when asked (`--dry-run` first).
- Retired 2026-10-04: `fill_btc_stock_id*` (wrote legacy `BTC Stock ID`). While CL is NocoDB-owned, do not run local CL fill scripts for stock ids.

## Watch

- **Later (not built, 2026-09-17):** packing list PDFs (including slips this app prints) move to Order Packing List Generator. This app stays tag → stock / EDI.
- Former local CL copy is under `backups/shared/`.
- FTP stock filename is configured in `config.py` only.
- GUI/CLI entrypoints import helpers from cohesive `run_*` modules (`run_ftp_settings`, `run_ftp_download`, `run_packing_rows`, …). Legacy `run_script_impl*` files are thin re-exports only — do not add new logic there.
