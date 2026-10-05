# Purchase Order Generator — snapshot

**Updated:** 5 October 2026 (CL stock id = `Supplier_SKU`; NocoDB stand-in for retired `BTC SKU`)  
**Handbook:** `AGENTS.md` · **Layout:** `FOLDER_LAYOUT.md`

## Continue here

- Launch: `Run_GUI.bat` (creates `.venv`, runs GUI).
- Live DB under `database/purchase-order-generator/` + shared catalogs; outputs under `output/`.
- Stock CL map: `database/shared/custom_label/Custom_Label_Database.csv` (`Supplier_SKU` via `shared/cl_columns.BTC_SKU` — no `BTC Stock ID`).
- Sync DB from BTC Product Data / download images with scripts when asked (`--dry-run` first).
- Retired 2026-10-04: `fill_btc_stock_id*` (wrote legacy `BTC Stock ID`). While CL is NocoDB-owned, do not run local CL fill scripts for stock ids.

## Watch

- **Later (not built, 2026-09-17):** packing list PDFs (including slips this app prints) move to Order Packing List Generator. This app stays tag → stock / EDI.
- Former local CL copy is under `backups/shared/`.
- FTP stock filename is configured in `config.py` only.
- GUI/CLI entrypoints import helpers from cohesive `run_*` modules (`run_ftp_settings`, `run_ftp_download`, `run_packing_rows`, …). Legacy `run_script_impl*` files are thin re-exports only — do not add new logic there.
