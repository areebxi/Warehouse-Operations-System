# Purchase Order Generator — snapshot

**Updated:** 4 October 2026 (CL stock id = `BTC SKU` only; legacy fill retired)  
**Handbook:** `AGENTS.md` · **Layout:** `FOLDER_LAYOUT.md`

## Continue here

- Launch: `Run_GUI.bat` (creates `.venv`, runs GUI).
- Live DB under `database/purchase-order-generator/` + shared catalogs; outputs under `output/`.
- Stock CL map: `database/shared/custom_label/Custom_Label_Database.csv` (`BTC SKU` only — no `BTC Stock ID`).
- Sync DB from BTC Product Data / download images with scripts when asked (`--dry-run` first).
- Retired 2026-10-04: `fill_btc_stock_id*` (wrote legacy `BTC Stock ID`). CL dedicated cols fill via Custom Label `fill_from_seeds.py --steps suppliers`.

## Watch

- **Later (not built, 2026-09-17):** packing list PDFs (including slips this app prints) move to Order Packing List Generator. This app stays tag → stock / EDI.
- Former local `data/Custom Label Database.csv` is under `data/archive/`.
- FTP stock filename is configured in `config.py` only.
- GUI/CLI entrypoints import helpers from cohesive `run_*` modules (`run_ftp_settings`, `run_ftp_download`, `run_packing_rows`, …). Legacy `run_script_impl*` files are thin re-exports only — do not add new logic there.
