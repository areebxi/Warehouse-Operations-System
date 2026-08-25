## Packing List App – Project Overview

This folder contains your full packing list pipeline, the main GUI app, and the helper tools for missing runs and preflight issues.

**Usage (GUI fields, options, outputs):** see **[USAGE.md](USAGE.md)**.  
**Pipeline spec (steps 1–8, columns, script reference):** see **[docs/README.md](docs/README.md)**.

### Top‑level structure

- **`packing_list_app.py`** – Main GUI application for running the full 8‑step packing pipeline.
- **`missing_run_app.py`** – GUI/CLI tool to re‑run a single process/item using `Missing/All Orders.csv` + `Missing/Missing Input.csv`.
- **`preflight_issues_app.py`** – **Preflight Issues App**: unmatched SKUs + dry-run missing logo/apparel review CSV.
- **`scripts/`** – Pipeline step CLIs (`scripts/fetch_input_csv.py`, … `scripts/generate_packing_list_pdf.py`), modular implementations under `scripts/pipeline_*`, `scripts/pipeline_runner.py` (`run_pipeline`), and shared GUI theme `scripts/gui_theme.py`.
- **`config/`** – JSON config files for the GUIs (`gui_config.json`, `missing_run_config.json`, `preflight_issues_config.json`).
- **`Data/`** – Input workbook(s) and reference data used by the pipeline.
- **`Output/`** – All generated CSVs, Excels, and PDFs, organised as `Output/{date}/{shift} Shift/{process}/`.
- **`logs/`** – Image lookup logs and diagnostic logs for PDF generation.
- **`Missing/`** – Files that power the missing‑run tool:
  - `All Orders.csv` – consolidated log of step‑6 split runs.
  - `Missing Input.csv` – queries for the missing‑run pipeline.
- **`Unmatched SKU Files/`** – Per‑day, per‑shift CSVs of unmatched SKUs moved out of step 4; also default output for Preflight Issues CSVs.
- **`Versions/`** – Older versions of the main GUI app kept for reference.

### Running the main app

1. Open a terminal in this folder.
2. Start the main GUI (opens maximized; shared theme from `scripts/gui_theme.py`):
   ```bash
   python packing_list_app.py
   ```
3. In the GUI:
   - Set **Input**, **Date**, **Shift**, **Output directory**, **Workbook path**.
   - Optionally set **Apparel Image**, **Normal Logo/Design**, **Customise Logo/Design**, and copy directories.
   - Click **Run pipeline** and follow the on‑screen log and completion dialog.

### Running the missing‑run app

1. Open a terminal in this folder.
2. Start the Missing Run GUI (opens maximized; same shared theme):
   ```bash
   python missing_run_app.py
   ```
3. In the GUI:
   - Set **Date**, **Shift** (required), and **Process name**.
   - Confirm `Missing Input CSV` and `All Orders CSV` paths.
   - Optionally set **Apparel Image**, **Normal Logo/Design**, **Customise Logo/Design**, and **PDF/Excel copy directories**.
   - PDF copies (if set) go **directly into** the selected folder; Excel copies nest under `{Shift} Shift/`.
   - If multiple `Missing Input.csv` rows resolve to the same **Order Number** within the same date and process, the app expands that order only once.
   - Click **Run missing pipeline**.
4. The log window and a final popup will show where outputs were written.

### CLI usage (advanced)

- **Main pipeline** runs primarily through `packing_list_app.py`; for custom automations, import `run_pipeline` from `scripts.pipeline_runner` (alias for `scripts.pipeline_runtime.runner`).
- **Missing run** can be run from the command line via:
  ```bash
  python missing_run_app.py DD-MM-YYYY PROCESS_NAME --shift 3rd
  ```
  with optional `--missing-input` and `--all-orders` arguments. As in the GUI, duplicate query rows that point to the same order in the same date and process are deduped automatically.

## Packaging pipeline (summary)

Takes a **ShipStation CSV (Current View)** and, through eight scripted steps, produces **per-process CSVs**, **Excel workbooks** (Picking, Orders Details, DTF Des), and **packing list PDFs**. See **[docs/README.md](docs/README.md)** for column reference, pipeline order, CLI examples, and script links.

## Reference layout (abbreviated)

```
├── packing_list_app.py       ← Main GUI
├── missing_run_app.py        ← Missing-run helper GUI/CLI
├── preflight_issues_app.py   ← Preflight Issues App (unmatched + missing images)
├── scripts/                  ← Steps 1–8, pipeline_runner, gui_theme, helpers
├── config/                   ← gui_config.json, missing_run_config.json, preflight_issues_config.json
├── USAGE.md                  ← GUI usage (main, missing run, preflight issues)
├── docs/                     ← README (full spec), CHANGELOG, per-script notes
├── Input/                    ← ShipStation CSV exports
├── Output/                   ← Date / shift / process outputs
├── Data/                     ← Workbook.xlsx, design/process CSVs, etc.
├── Missing/                  ← All Orders.csv, Missing Input.csv (missing run)
├── Unmatched SKU Files/      ← Step-4 unmatched + Preflight Issues CSVs
└── logs/                     ← PDF / image diagnostic logs
```
