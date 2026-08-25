## Packing List App – Usage

End-user guide for the three GUIs. For pipeline steps, column specs, and CLI commands, see **[docs/README.md](docs/README.md)**.

### 1. Prerequisites
- **Python**: Installed and available on your PATH (Python 3.10+ recommended).
- **Dependencies**: From a terminal in the project folder, install:

```bash
pip install -r requirements.txt
```

- **Project files** (expected structure):
  - `Data/Workbook.xlsx` – CL lookup workbook.
  - `Data/ShipStation Tags.xlsx` – tag name / Tag ID / per-shift process-number mapping. Used when tag-mode process number is left blank. Sync from ShipStation with `python scripts/sync_shipstation_tags.py` (close the Excel file first).
  - `API KEY.txt` – ShipStation API credentials at the project root (`REAL_API_BASE_URL`, `REAL_API_KEY`, `REAL_API_SECRET`) for tag-based order fetch.
  - `Output/` – output folder (created automatically if missing).
  - Optional image folders for PDFs (top-level files only; no subfolders are scanned):
    - Apparel images
    - Normal Logo/Design images
    - Customise **Single Position** Logo/Design images
    - Customise **Double Position** Logo/Design images

### 2. Starting the Packing List App
From the project root (`Packing List App - Testing`), double-click **`run_packing_list_app.bat`** (recommended). That installs dependencies if needed, then starts the app with **no persistent CMD window** alongside the GUI (a short console may appear only during `pip install`, then it closes).

Alternatively, from a terminal:

```bash
python packing_list_app.py
```

This opens the **Packing List App** Tkinter window (maximized). Full run transcripts are written under **`logs/`**; step progress also appears in the on-screen log area.

All three GUIs share a common look from `scripts/gui_theme.py` (applied at startup only).

### 3. Main fields and options
- **Input source** (top of the form):
  - **CSV file(s)** – use local ShipStation CSV(s) via **Add files…**.
  - **ShipStation tag(s)** – fetch awaiting-shipment orders from ShipStation; disables the CSV list.
  - Selecting CSV files switches to CSV mode and clears selected tags; adding a tag switches to tag mode and clears the file list.
  - **Run missing pipeline** forces **CSV file(s)** mode (tag radio disabled).
- **ShipStation tag(s)** (when Input source is ShipStation tag(s)):
  - Pick a tag from the dropdown, click **Add** (repeat for multiple). Tags appear as a wrapping chip grid — click **×** on a chip to remove it, or **Remove all**.
  - **Refresh tags** reloads from ShipStation.
  - Selected tags are saved in `config/gui_config.json` so the next open can **Run pipeline** without re-picking.
  - Requires **Date** and **Shift**.
  - **One tag:** **Fixed process number** is forced on — enter a value, or leave blank to use the matching **Process No** column for that shift from `Data/ShipStation Tags.xlsx` (manual entry always wins).
  - **Multiple tags:** the process field is **disabled and ignored**; each tag uses its own process from `Data/ShipStation Tags.xlsx` for the current shift. Two tags with the same process for that shift is an error.
  - On Run, for each selected tag the app fetches **awaiting_shipment** orders and writes:
    - `Input/{Date}/{Shift} Shift/{Process}.csv`
  - Orders that also have the **`post-order-designs`** tag are excluded.
  - Then runs the normal pipeline (sequentially per tag, like multi-file). Outputs go to:
    - `Output/{Date}/{Shift} Shift/{Process}/...`
  - Credentials: project-root `API KEY.txt` (not stored in `gui_config.json`).
- **Input CSV(s)**: ShipStation CSV file(s) to process (when Input source is CSV file(s)).
  - Use **Add files…** to add one or more CSVs; **Remove selected** / **Remove all** to manage the list.
  - To process **multiple CSVs at once**, **Use fixed process number** must be enabled (adding 2+ files turns it on automatically); each filename (without extension) is used as that file’s process number.
  - **Multi-file / multi-tag order:** when more than one CSV or ShipStation tag is selected, the app runs **all Excel outputs (steps 1–7) first**, then **all PDFs (step 8)**. A single input still runs Excel and PDF together in one pass.
- **Date (DD-MM-YYYY)**: Dispatch date for this run (e.g. `13-03-2026`).
- **Shift**: Required; choose one of `1st`, `2nd`, `3rd`, `4th`, `5th`.
- **Output directory**: Root folder where all outputs are created (default `Output`).
- **Workbook path**: Path to `Data/Workbook.xlsx` (or your workbook file).
- **Apparel Image folder**: Folder containing product/apparel images (files in the top level only).
- **Normal Logo/Design folder**: Folder for standard logo/design images (files in the top level only).
- **Customise Single Position Logo/Design folder**:
  - Folder for customise/variable logo images used for **single-position** designs.
  - Only files in the top level are scanned (no subfolders).
- **Customise Double Position Logo/Design folder**:
  - Folder for customise/variable logo images used for **double/multi-position** designs.
  - Only files in the top level are scanned (no subfolders).
  - When looking up customise logos, the app first searches the **Single** folder; if not found there, it then searches the **Double** folder.
- **PDF copy directory (optional)**: If set, PDFs are copied under:
  - `{PDF copy dir}/{Shift} Shift/` (main Packing List pipeline and Packing List **Run missing pipeline** mode).
- **Excel copy directory (optional)**: If set, Excels are copied under:
  - `{Excel copy dir}/{Shift} Shift/` (same nesting as PDF for the main app).
  - Copy failures are logged and included in the **Finished** dialog; the run still completes.
- **Separate by Logo ID**:
  - When enabled, logo IDs that reach a minimum **unit** count (from **full-logo orders** only) are checked against workbook sheet **Design ID Process Tracker** (`Data/Workbook.xlsx`, columns Design ID / Process Number).
  - **In tracker** → separate process using the assigned Process Number (e.g. `10000`).
  - **Not in tracker** → **Logo ID only:** normal 6-part process (same batch PDF as other orders). **With fixed process number:** fixed batch (e.g. `100`), same as below-threshold rows.
- **Logo ID threshold**:
  - Minimum **units** (rows × Item Quantity, summed only for orders where every line shares the same Logo ID) before a Logo ID is considered for tracker lookup (default `5`). Passing the threshold alone is not enough — the Logo ID must also be listed in **Design ID Process Tracker** to get its own process (unless combined with fixed and not listed, in which case it joins the fixed batch).
- **Use fixed process number**:
  - When **off** (default): the system assigns process numbers automatically per run.
  - When **on**:
    - **Single CSV**: you may type a **Fixed process number**; if left blank, the app uses the CSV filename stem.
    - **Multiple CSVs**: each file is run with its own fixed process number = filename stem.
  - Always forced **on** when Input source is ShipStation tag.
- **Fixed process number**:
  - Only enabled when **Use fixed process number** is checked (or single-tag mode).
  - Used as the process name and output folder name.
  - In **single-tag** mode, if left blank, the app looks up `Data/ShipStation Tags.xlsx` (`Process No - {Shift} Shift` for the selected tag). If that cell is empty, you must enter a process number.
  - In **multi-tag** mode the field is disabled; each tag’s process comes only from the Tags sheet.
- **Run missing pipeline**:
  - When **off** (default): runs the **main 8‑step packing pipeline** from a normal input CSV or ShipStation tag.
  - When **on**: the app expects a **missing Excel/CSV file** instead of a ShipStation CSV/tag and runs the missing helper pipeline (see below).

### 4. Running the main pipeline (normal use)
1. **Open** the app (`python packing_list_app.py`).
2. Choose **Input source**:
   - **ShipStation tag(s):** add one or more tags, set **Date** and **Shift**, and optionally **Fixed process number** when only one tag is selected (blank uses `Data/ShipStation Tags.xlsx`), or
   - **CSV file(s):** click **Add files…** and select one or more ShipStation CSVs (multiple files require **Use fixed process number**).
3. **Choose Date** in `DD-MM-YYYY` format.
4. **Select Shift** (required).
5. **Set Workbook path** (usually `Data/Workbook.xlsx`).
6. Optionally set **Apparel**, **Normal Logo/Design**, **Customise Single Position**, and **Customise Double Position** folders to embed real images into PDFs. If a folder path is filled in, it must be an existing directory. If all are empty, the app will warn that only placeholders will be used.
7. Optionally set **PDF copy directory** and **Excel copy directory**.
8. Optionally enable **Separate by Logo ID** and adjust **Logo ID threshold**.
9. Optionally enable **Use fixed process number** and set **Fixed process number** (forced on for a single tag; blank uses the Tags sheet; disabled when multiple tags are selected).
10. Click **Run pipeline**.

The log area at the bottom shows progress through all 8 steps (CSV fetch, enrichment, split, Excel creation, PDF creation, etc.).

When finished:
- A message box summarises:
  - **Output folder(s)** created.
  - Any **Unmatched orders file** paths.
  - Any **missing report** text.
  - Any **PDF/Excel copy failure** messages (if a copy directory was set but the copy failed).
- The **Output** folder structure is:
  - `Output/{Date}/{Shift} Shift/{Process}/...`

Settings are saved to `config/gui_config.json` on close / after a successful run. If the file cannot be written, the failure is printed to **stderr** (no dialog).

### 5. Outputs, personalised naming, and unmatched SKUs
- For each process, the app writes:
  - One consolidated CSV (step‑6 shaped).
  - Three Excel workbooks.
  - One packing list PDF (with or without images).
- **Personalised multi‑row orders (same Order Number)**:
  - When `Customise` is `Yes` and an order has multiple rows in Step 5, Step 6 treats them as a merge block.
  - In the step‑6 CSV, `Logo/Design Image` is normalised so that each unit gets a distinct stem based on **Order Number**:
    - First unit: `OrderNumber`
    - Second unit: `OrderNumber-1`
    - Third unit: `OrderNumber-2`
    - and so on.
  - The **Customise Logo/Design** image folder should therefore contain files named using these stems (e.g. `09-14343-68842.png`, `09-14343-68842-1.png`, `09-14343-68842-2.png`, …). The PDF generator will look up each personalised unit by its `Logo/Design Image` stem.
- During Step 4, any rows that cannot be matched to CL lookup rules are written to an **unmatched_orders** CSV and moved under:
  - `Unmatched SKU Files/{Date}/{Shift} Shift/`
- These unmatched SKUs can then be investigated or processed via the **Preflight Issues App** (see below).

### 6. Running the missing pipeline from the Packing List App
Use this when you already have a **Missing Logos (date).xlsx** (or equivalent CSV) and want to regenerate packing outputs with images fixed.

1. In the main app, tick **Run missing pipeline**.
2. In **Input**, pick the **Missing Logos Excel or CSV file** (not the original ShipStation CSV).
3. Set **Date**, **Shift** (required), **Output directory**, **Apparel/Logo** image folders, and copy directories as usual. Non-empty image folder paths must be existing directories.
4. Optionally set **Fixed process number**; if left blank, the app will use the Missing Logos filename stem as the process name.
5. Click **Run pipeline**.

Results:
- A single process folder under:
  - `Output/{Date}/{Shift} Shift/{ProcessName}/`
- One CSV, three Excel workbooks, and one PDF (with updated image matching).
- Optional PDF/Excel copies still go under `{copy dir}/{Shift} Shift/` (same as the main pipeline).

Note: the main pipeline no longer auto-generates the `Missing Logos (date).xlsx` intermediate file; you need to supply it (or an equivalent CSV) yourself if you want to re-run missing items.

---

## Missing Run App – Usage

The **Missing Run App** recreates outputs for specific orders that were previously logged in `Missing/All Orders.csv`, based on queries in `Missing/Missing Input.csv`.

### 1. Prerequisites
- The main Packing List App must have been used before, so that:
  - `Missing/All Orders.csv` exists and contains history.
  - `Missing/Missing Input.csv` has been prepared with the orders you want to regenerate (columns: **Date**, **Process**, **Item Number** at minimum).
- Python dependencies installed (`pip install -r requirements.txt`).

### 2. Running via GUI (recommended)
From the project root, double-click **`run_missing_run_app.bat`** (recommended). That installs dependencies if needed, then starts the app with **no persistent CMD window** (a short console may appear only during `pip install`, then it closes).

Alternatively, from a terminal:

```bash
python missing_run_app.py
```

This opens the **Missing Run App** window (maximized). Full run transcripts are written under **`logs/`**; step progress also appears in the on-screen log area.

### 3. GUI fields
- **Date (DD-MM-YYYY)**: Date of the original dispatch (must match the **Date** column in `All Orders`).
- **Shift**: Required. Outputs are placed under `Output/{Date}/{Shift} Shift/{ProcessName}/`.
- **Process name**: Name for this missing run (e.g. `4201-missing`). Used as the output folder and file stem.
- **Missing Input CSV**: Path to `Missing/Missing Input.csv` (or another CSV with the same structure). Click **Browse…** to select.
- **All Orders CSV**: Path to `Missing/All Orders.csv`. Click **Browse…** to select.
- **Apparel / Normal Logo/Design / Customise Single / Customise Double** folders:
  - Same meaning as in the main app; used to embed images (pipeline uses **top-level-only** stem maps for all four).
- **PDF copy directory / Excel copy directory (optional)**:
  - **PDF**: copied **directly into the selected folder** (not under a `{Shift} Shift` subfolder).
  - **Excel**: copied under `{Excel copy dir}/{Shift} Shift/` (same nesting as the main Packing List pipeline).

### 4. Steps to run
1. Open the app (`run_missing_run_app.bat` or `python missing_run_app.py`).
2. Fill in **Date**, **Shift**, and **Process name**.
3. Point **Missing Input CSV** to your query file.
4. Point **All Orders CSV** to `Missing/All Orders.csv`.
5. Set image folders and optional copy directories (or leave blank to use placeholders).
6. Click **Run missing pipeline**.

The log box shows step progress; detail lines are also saved under `logs/`. On success, a message box confirms and shows the output folder.

Outputs:
- One step‑6 shaped CSV, three Excel files, and one PDF in:
  - `Output/{Date}/{Shift} Shift/{ProcessName}/`

Settings are saved to `config/missing_run_config.json`. If the file cannot be written, the failure is printed to **stderr** (no dialog).

You can then treat these outputs exactly like those from the main Packing List App.

---

## Preflight Issues App – Usage

The **Preflight Issues App** (launcher: `preflight_issues_app.py`) audits ShipStation CSVs before a full packing run. It reports:

1. **Unmatched SKU** — blank **Gender Apparel** after CL Database lookup
2. **Missing Logo** — Logo/Design token present but no matching image file (dry-run)
3. **Missing Apparel** — Apparel/Picture Name present but no matching apparel image (dry-run)

Discount line items (**Item Name** contains `discount`) are skipped in Step 1, same as the main pipeline. Rows whose Item SKU contains `plain` or `plainlg` are not flagged for Missing Logo. Full behaviour: [docs/scripts/preflight_issues_app.md](docs/scripts/preflight_issues_app.md).

### 1. Prerequisites
- `Data/Workbook.xlsx` – main CL workbook (includes **CL Database**, Process Info Sheet, Multiple Positions).
- Optional image folders (same as the main Packing List App) for logo/apparel dry-run checks.
- Python dependencies installed (`pip install -r requirements.txt`).

### 2. Starting the app
From the project root, double-click **`run_preflight_issues_app.bat`** (recommended). That installs dependencies if needed, then starts the app with **no persistent CMD window** (a short console may appear only during `pip install`, then it closes).

Alternatively, from a terminal:

```bash
python preflight_issues_app.py
```

This opens the **Preflight Issues App** window (maximized). Progress appears in the on-screen log area.

### 3. GUI fields
- **Input source**:
  - **CSV file(s)** – use **Add files…** (tag controls disabled).
  - **ShipStation tag(s)** – fetch from API (file list buttons disabled). Adding a tag clears the file list.
- **ShipStation tag(s)** (when Input source is ShipStation tag(s)):
  - Pick a tag, click **Add** (repeat for multiple). Tags appear as a wrapping chip grid — click **×** on a chip to remove it, or **Remove all**. **Refresh tags** reloads from ShipStation.
  - Selected tags are saved in `config/preflight_issues_config.json`.
  - Requires **Date** and **Shift**.
  - **One tag:** **Process number** may be left blank to use `Data/ShipStation Tags.xlsx`; manual entry wins if set.
  - **Multiple tags:** process field is disabled; each tag uses Tags.xlsx for the current shift (duplicate process numbers across tags are an error).
  - On Run, fetches **awaiting_shipment** orders per tag into `Input/{Date}/{Shift} Shift/{Process}.csv`, then audits all fetched files together.
  - Orders that also have the **`post-order-designs`** tag are excluded.
  - Issues CSV is written under `{Output directory}/{Date}/{Shift} Shift/Preflight Issues_{timestamp}.csv`.
  - Credentials: project-root `API KEY.txt`.
- **Date (DD-MM-YYYY)** / **Shift** / **Process number**:
  - **Date** and **Shift** required in tag mode. **Process number** required for a single tag unless the Tags sheet has a value; ignored when multiple tags are selected.
  - In **CSV file(s)** mode the process field is disabled — each file’s filename stem is used as Process Number.
- **Input CSV(s)**:
  - List of ShipStation CSV files to scan (when Input source is CSV file(s)).
  - Use **Add files…** to add one or more CSVs.
  - **Remove selected** / **Remove all** to manage the list.
- **Workbook**:
  - Path to `Data/Workbook.xlsx` (or your workbook).
- **Output directory**:
  - Where the **Preflight Issues** CSV will be written (default `Unmatched SKU Files` at the project root; you can point this at e.g. `Preflight Issues/`).
  - Tag mode nests under `{output}/{Date}/{Shift} Shift/`.
- **Apparel Image / Normal Logo/Design / Customise Single / Customise Double** folders:
  - Optional. Used for missing logo/apparel dry-run (same rules as Step 8 PDF image lookup).
  - Non-empty paths must be existing directories. If all are empty, only Unmatched SKU is reported.
- **Log**:
  - Text area that shows per-file progress and errors.

The app remembers Workbook, output directory, image folders, date/shift/process, and selected tags in `config/preflight_issues_config.json` (falls back to reading `unmatched_skus_config.json` if the new file is missing). If the file cannot be written, the failure is printed to **stderr** (no dialog).

### 4. Steps to run a preflight audit
1. Open the app (`python preflight_issues_app.py`).
2. Choose **Input source**:
   - **ShipStation tag(s):** add one or more tags, plus Date and Shift (Process number optional for a single tag if Tags.xlsx has it), or
   - **CSV file(s):** click **Add files…** and select one or more ShipStation CSV files.
3. Confirm **Workbook** path is correct.
4. Optionally set the four image folders.
5. Set **Output directory** (or use the default `Unmatched SKU Files`).
6. Click **Run**.

For each input CSV, the app:

- Fetches rows and runs CL enrich (step 2), fill Apparel/Logo (step 3), and position/logo expansion (step 4).
- Flags every row for Unmatched SKU / Missing Logo / Missing Apparel.
- Keeps only rows with at least one **Yes**.

Results:

- If **no issues** are found:
  - The log shows “No preflight issues found.” and a message box confirms.
- If issues are found:
  - A combined CSV is written as:
    - `Preflight Issues_{DD-MM-YYYY}_{HH-MM-SS}.csv`
  - Columns include the enriched row data plus `Unmatched SKU`, `Missing Logo`, `Missing Apparel` (Yes/No).
  - The finished dialog shows counts for each flag and the output path.

You can then fix CL Database entries and/or add missing image files, and re-run the main Packing List pipeline.

