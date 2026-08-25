# assign_process_number.py — Step 5

Fifth step in the pipeline: **assign** a 6-part Process Number to each row and write it into **Process and Item Number** using the step-4 matched CSV and Workbook "Process Info Sheet" (columns A–N).

## Purpose

- Read step-4 matched CSV (typically `Output/4_matched_split_and_assign_position_codes_{token}.csv`) and Data/Workbook.xlsx sheet **"Process Info Sheet"**.
- **Process Number** is the concatenation of 6 parts (no separator):  
  **{process_start}{shift_code}{prime_code}{customise_code}{dispatch_code}{position_code}**  
  Examples: `100APCDX`, `200APCDX`, `400BNND1X2`.
- **Step 1 — Process start number (Process Info Sheet):** Match CSV **Gender Apparel** (strip, case-insensitive) to column **A**; take **Process Start Number** from column **B** (e.g. 100, 200, 300, 400).
- **Step 2 — Shift (Process Info Sheet):** User provides shift (e.g. `1st`, `2nd`, `3rd`, `4th`, `5th`). Match to column **D** "Shift" (e.g. "1st Shift", "2nd Shift", …). Take **Code** from column **E** (e.g. A, B, C, D, E).
- **Step 3 — Prime (fixed rule):** If CSV **Prime** = "Yes" → **P**; else → **N**.
- **Step 4 — Customise (fixed rule):** If CSV **Customise** = "Yes" → **C**; else → **N**.
- **Step 5 — Dispatch (fixed rule):** If **Ship By** date equals **today** → **D**; else → **D1**.
- **Step 6 — Position:** Use existing **Position Code** column from the step-4 CSV (e.g. X, X1, X2).
- Write all rows with **Process and Item Number** filled to `Output/5_assign_process_number_{token}.csv`. Rows where Gender Apparel has no match in the sheet keep Process and Item Number blank.

### Optional: Separate by Logo ID

When **separate_by_logo_id** is True (GUI checkbox or CLI `--separate-by-logo-id`), the step-4 CSV must contain **Logo ID** and **Order Number** (Logo ID is added in step 3). This logic applies both when fixed process number is off (Logo ID only) and when **both** options are on (combined mode).

- **Threshold metric — units per Logo ID:** For each Logo ID, count **units** (rows × Item Quantity). Only **full-logo orders** contribute: an order contributes to a Logo ID L only when **all** non-blank Logo ID values in that order equal L (multi-line orders with mixed or other logos contribute 0 for L). Multi-quantity rows count their Item Quantity (e.g. qty 3 → 3 units). Missing or invalid Item Quantity is treated as 1.
- **Assignment:** A row is eligible for logo separation only if (1) its Logo ID’s unit count is **≥ logo_id_threshold**, and (2) **the row’s order is a full-logo order for that Logo ID** (all non-blank Logo IDs in that order are the same). Rows in mixed-logo orders never get a logo process, even if that Logo ID is over threshold from other orders; they get the 6-part number or fixed value instead.
- **Design ID Process Tracker lookup:** When eligible, the Logo ID is looked up in workbook sheet **"Design ID Process Tracker"** (columns **Design ID**, **Process Number**). Logic is implemented in [`design_id_process_tracker.py`](../../scripts/pipeline_assign_process_number/design_id_process_tracker.py) (`USE_TRACKER = True` to enable; set `False` to restore legacy logo assignment without changing other pipeline code).
  - **Logo ID only** (fixed process off): if the Logo ID is **in the tracker**, set **Process and Item Number** to the assigned **Process Number** (e.g. `49641LG` → `10000`). If **not in the tracker**, use the normal **6-part Process Number** (no separate logo process).
  - **Both options on** (fixed + Separate by Logo ID): if **in the tracker**, use the assigned **Process Number**; if **not in the tracker**, use the **fixed process number** (same batch as below-threshold rows).
- Rows that qualify with a tracker match do **not** apply prime/customise/dispatch/position logic.
- All other rows get the 6-part Process Number (logo-only, not in tracker) or the fixed value (combined mode, not in tracker or below threshold).
- The **Logo ID** column is retained in the step-5 output for step 6.

### Optional: Use fixed process number

When **fixed_process_number** is non-empty (GUI “Use fixed process number” + entry, or CLI `--fixed-process-number`), this **overrides** normal assignment and Separate by Logo ID.

- **If only fixed is set:** Every row gets the given value; workbook and Logo ID not used. Step 6 has one group to one CSV.
- **If both** are set: over-threshold full-logo rows **in Design ID Process Tracker** get the assigned Process Number; over-threshold rows **not in the tracker** get the **fixed value**; all other rows get the fixed value. Process Info Sheet is not loaded.
- When fixed is selected (fixed-only or both), **Process Info Sheet is not loaded**.

### Design ID Process Tracker (workbook sheet)

Sheet **"Design ID Process Tracker"** in `Data/Workbook.xlsx` (same file as Process Info Sheet and Process Number Tracker).

| Column | Purpose |
|--------|---------|
| Design ID | Logo ID to match (e.g. `49641LG`) |
| Process Number | Process base assigned in step 5 (e.g. `10000`) |

Only Logo IDs listed in this sheet get a separate process when over threshold. Step 6 then formats purely numeric bases with sequential integers (`Process 10000 Item-1`, `Process 10001 Item-1`, …); see [split_by_process_and_item_number.md](split_by_process_and_item_number.md).

## Process Info Sheet (Data/Workbook.xlsx)

Only **Gender Apparel** (process start number) and **Shift** (code) use the Process Info Sheet. Prime, Customise, and Dispatch use **fixed codes** from the CSV columns and Ship By date: **P**/**N**, **C**/**N**, **D**/**D1**.

- **Sheet name:** "Process Info Sheet" (exact).
- **Columns used by this script:**
  - **A:** Gender Apparel (match key).
  - **B:** Process Start Number (100, 200, 300, 400, …).
  - **D:** Shift label (e.g. "1st Shift", "2nd Shift", …, "5th Shift").
  - **E:** Code for Shift (A, B, C, D, E).

Column indices (0-based) are used as fallback when headers are missing or layout differs. Matching is case-insensitive after strip.

## Rules in detail

### 1. Missing Gender Apparel match

- If a row’s **Gender Apparel** does not match any value in column A, **Process and Item Number** for that row is left blank; the script continues.

### 2. Ship By and Dispatch

- **Ship By** is parsed as DD-MM-YYYY or D/M/YYYY. If empty or invalid, the row is treated as "Dispatch Other".
- Comparison with "today" uses local date (`date.today()`).

### 3. Position Code

- Taken from the step-4 CSV column **Position Code** (already assigned by step 4). No lookup in the sheet for this step.

## Usage

**From the command line:**

```bash
# Required: step-4 matched CSV path and shift
python scripts/assign_process_number.py Output/4_matched_split_and_assign_position_codes_902b934a-7d72-40a4-a371-65c40c2f21e5.csv 1st

# Optional: workbook and output directory
python scripts/assign_process_number.py Output/4_matched_split_and_assign_position_codes_902b934a-7d72-40a4-a371-65c40c2f21e5.csv 2nd Data/Workbook.xlsx Output/

# Optional: separate by Logo ID when a Logo ID has at least N units (full-logo orders only)
python scripts/assign_process_number.py step4.csv 1st --separate-by-logo-id --logo-id-threshold 5

# Optional: use a fixed process number for all rows (overrides normal and Logo ID when used alone)
python scripts/assign_process_number.py step4.csv 1st --fixed-process-number 100A

# Optional: combine both — threshold Logo IDs in Design ID Process Tracker get assigned Process Number; rest get fixed value
python scripts/assign_process_number.py step4.csv 1st --separate-by-logo-id --fixed-process-number 100
```

- **step4_matched_csv** (required): Path to step-4 matched output CSV.
- **shift** (required): One of `1st`, `2nd`, `3rd`, `4th`, `5th`.
- **workbook_path** (optional): Default `Data/Workbook.xlsx` in the Data/ folder.
- **output_dir** (optional): Default `Output/`. Token is derived from the step-4 filename stem (e.g. `4_matched_split_and_assign_position_codes_902b934a-...` → token `902b934a-...`).
- **--separate-by-logo-id** (optional): When set, over-threshold full-logo rows are looked up in workbook **Design ID Process Tracker**; see assignment rules above.
- **--logo-id-threshold** (optional): Min **units** per Logo ID (from full-logo orders; rows × Item Quantity) before a Logo ID is considered for tracker lookup (default: 5). Used only when `--separate-by-logo-id` is set.
- **--fixed-process-number** (optional): When set alone, every row gets this value. When set **with** `--separate-by-logo-id`, tracker-listed threshold Logo IDs get the assigned Process Number; threshold rows not in the tracker and all other rows get this fixed value. Process Info Sheet is not loaded when fixed is used.

**Dependencies:** `pandas`, `openpyxl` (install with `pip install -r requirements.txt`).

## Required columns

The step-4 CSV must contain: **Gender Apparel**, **Prime**, **Customise**, **Ship By**, **Position Code**, **Process and Item Number**. If any are missing, the script exits with an error. When **separate_by_logo_id** is True (with or without fixed), the step-4 CSV must also contain **Logo ID** and **Order Number** (Logo ID is added in step 3). When **fixed_process_number** is set (fixed-only or both), the Process Info Sheet is not loaded. If the workbook is missing, "Process Info Sheet" is missing, or the given shift does not match any row in column D (and fixed process number is not set), the script fails with a clear error.

## Where it fits

Pipeline step **5 (Transform)**. Consumes `Output/4_matched_split_and_assign_position_codes_{token}.csv` and Workbook "Process Info Sheet". Produces `Output/5_assign_process_number_{token}.csv`. Runs after [split_and_assign_position_codes.py](split_and_assign_position_codes.md), before grouping and PDF generation.
