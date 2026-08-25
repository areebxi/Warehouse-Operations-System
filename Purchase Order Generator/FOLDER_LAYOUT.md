# Plain Orders App — folder layout

## Root (launch & config)

| Item | Purpose |
|------|---------|
| `Run_GUI.bat` | Start the GUI (creates `.venv`, installs deps, runs app) |
| `config.py` | API & FTP credentials |
| `config_example.py` | Template for `config.py` |
| `requirements.txt` | Python dependencies |

## `scripts/` — all Python code

| File | Purpose |
|------|---------|
| `run_script_gui.py` | GUI entry point (started by `Run_GUI.bat`) |
| `run_script.py` | CLI / shared logic |
| `shipstation_orders.py` | ShipStation API |
| `pdf_generator.py` | Packing slip PDFs |
| `stock_resolver.py` | Custom label → stock ID |
| `app_paths.py` | Path helpers for `data/`, `assets/`, `output/` |
| `fill_btc_stock_id.py`, `validate_btc_product_codes.py`, `sync_database_from_product_export.py`, `download_product_images.py`, etc. | Maintenance tools |

Run any script from the app root, for example:

```bat
.venv\Scripts\python.exe scripts\run_script_gui.py
.venv\Scripts\python.exe scripts\validate_btc_product_codes.py
.venv\Scripts\python.exe scripts\sync_database_from_product_export.py
```

### Sync `Database.xlsx` from ProductExport

Packing slip PDFs look up product details in `data/Database.xlsx` by **SKU** (same as BTC **UID** / stock id). After you receive an updated `ProductExport.csv`, append any missing SKUs:

```bat
.venv\Scripts\python.exe scripts\sync_database_from_product_export.py
```

Options: `--dry-run` (counts only), `--no-backup`, `--output path\to\Database.xlsx`. A backup is written to `data/archive/Database.xlsx.bak_YYYYMMDD_HHMMSS` before overwrite. Existing rows are unchanged; **Package** is left blank for newly added SKUs.

### Download product images for PDFs

`Database.xlsx` stores image **filenames** only; packing slips load files from `assets/product_images/` and `assets/brand_logos/`. After syncing the database, download any missing images from ProductExport URLs:

```bat
.venv\Scripts\python.exe scripts\download_product_images.py --database-only
```

Use `--dry-run` to preview, `--sku 218408` for one stock id, or `--no-brands` for product images only.

## `data/` — databases & stock files

- `Packs Database.xlsx`, `Database.xlsx`, `ShipStation Tags.xlsx`
- `Custom Label Database.csv`, `ProductExport.csv`, `stock_levels_stock_id_fully_quoted.csv`
- `outlet_products.xlsx`, `invalid_btc_product_codes.csv`
- `archive/` — backups (e.g. `.bak` copies)

FTP/SFTP downloads the configured stock CSV into `data/` automatically (see below).

### Changing the BTC stock file

If BTC changes the stock file name or folder, update **only** `config.py`:

```python
FTP_REMOTE_FILE = "WebData/stock_levels_stock_id_fully_quoted.csv"  # path on BTC server
FTP_LOCAL_FILE = "stock_levels_stock_id_fully_quoted.csv"           # saved under data/
```

| Setting | Meaning |
|---------|---------|
| `FTP_REMOTE_FILE` | Remote path on BTC FTP/SFTP (e.g. `WebData/your_file.csv`) |
| `FTP_LOCAL_FILE` | Local filename under `data/` — the app reads this for stock checks |

The CSV must include columns **`stock_id`** and **`free_stock`**. No code changes are needed if you only change these two settings.

Logs show the configured remote and local paths on download and load, e.g.  
`[INFO] Stock file: remote=WebData/... → local=data/...`

Previous file: `free_stock.csv` (root of FTP). Current file: `WebData/stock_levels_stock_id_fully_quoted.csv`.

## `assets/` — images & fonts

- `product_images/`, `brand_logos/`, `fonts/`

## `output/` — new tag runs

Each run creates a folder like `Tag_007-N-03-Plain-2000_Orders_YYYYMMDD_HHMMSS/` with JSON, CSV, EDI, and PDF files.

## `00-Done/` — archived completed runs

Move finished folders from `output/` here when done (manual step, same as before).

## Generated / do not edit

- `.venv/` — Python virtual environment (created by `Run_GUI.bat`)
- `__pycache__/` — Python bytecode cache (safe to delete; recreated automatically)

The app runs from source via `Run_GUI.bat` and `.venv`. An old PyInstaller `_internal/` bundle was removed; it is not needed for this workflow.
