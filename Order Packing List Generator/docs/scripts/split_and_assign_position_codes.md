# split_and_assign_position_codes.py — Step 4

Fourth step in the pipeline: **split** rows by Gender Apparel (matched vs unmatched), **fill Position from Logo ID** when the **Logo IDs to Positions** sheet matches, **assign** a Position Code from the Process Info Sheet, and optionally **expand** **Logo/Design Image** using the **Multiple Positions** sheet.

## Purpose

- Read step-3 output CSV (typically `Output/3_fill_prime_and_images_{token}.csv`) and Data/Workbook.xlsx sheets **"Process Info Sheet"**, **"Logo IDs to Positions"** (optional), and **"Multiple Positions"** (optional).
- **Task 1 — Separate unmatched:** Rows where **Gender Apparel** is missing or blank are written to `Output/unmatched_orders_{token}.csv` and removed from the main dataset. Rows with non-empty Gender Apparel are "matched" and kept for Task 2.
- **Task 1.5 — Logo ID to Position:** On matched rows, look up **Logo ID** on the **Logo IDs to Positions** sheet. When a match exists, set **Position** from the sheet’s **Positions** column (overrides any Position from CL Database). If the sheet is missing or the Logo ID is not listed, **Position** is left unchanged.
- **Task 2 — Assign position codes:** On matched rows only, insert a column **"Position Code"** immediately after **"Position"**. Rows with empty/blank Position get the code from the Process Info row where column P = **"Default Position"** (e.g. "X"). Rows with non-empty Position: the script **matches** the Position value to the **actual position text** in column P (after strip, case-insensitive); the corresponding column Q is the Position Code (e.g. "Front Top Center, Back Top Center" → X1, "Front Top Center" → X2). If no row in the sheet matches the CSV Position value, the default code is used.
- **Task 3 — Expand Logo/Design Image (Multiple Positions):** On matched **non-personalized** rows with a **Logo ID**, look up **Position Code** on the **Multiple Positions** sheet. When one or more suffixes are returned, rewrite **Logo/Design Image** to comma-separated `base-suffix` tokens (e.g. `103671LG-f, 103671LG-b` for Position Code `X002`). Rows with **Customise = Yes** are skipped; **Logo/Design Image** stays as step 3 wrote it (typically the Order Number).
- Write matched rows (with Position Code and any updated Logo/Design Image) to `Output/4_matched_split_and_assign_position_codes_{token}.csv`.

## Process Info Sheet (Data/Workbook.xlsx)

- **Sheet name:** "Process Info Sheet" (exact).
- **Column P:** Position combination **text** (and one row **"Default Position"**). P holds the actual strings that appear in the CSV Position column, e.g. "Front Top Center, Back Top Center", "Front Top Center", "Back Top Center", "Front, Pocket". If the sheet has fewer than 17 columns, the script finds the P/Q columns by a column containing "Default Position" and the next column for codes.
- **Column Q:** Code for that row (e.g. "X", "X1", "X2", "X3", "X4").
- One row must have P = **"Default Position"**; its Q value is used for rows with empty Position and for any CSV Position value that does not match a row in P.
- Other rows: P = the exact position text (e.g. "Front Top Center, Back Top Center"); Q = the code. Matching is **by normalized equality** (strip and case-insensitive). Duplicate P values: the last row’s Q wins.

## Logo IDs to Positions sheet (Data/Workbook.xlsx)

- **Sheet name:** `"Logo IDs to Positions"` (exact). If the sheet is missing, empty, or has no valid rows, this step is skipped; Position Code assignment (Task 2) still runs using whatever **Position** Step 2/3 provided.
- **Column `Logo IDs`:** Logo ID to match against each row’s **Logo ID** column (case-insensitive), e.g. `159731LG`.
- **Column `Positions`:** Position **text** to write into **Position** before codes are assigned, e.g. `Front Top Center` or `Front Top Center, Back Top Center`. Use the same strings as Process Info column P (not codes like `X2`).
- **Override rule:** When a Logo ID matches, the sheet value **replaces** any existing **Position** from CL Database.
- **Duplicate Logo IDs:** Last row wins (same as Process Info P/Q).

## Multiple Positions sheet (Data/Workbook.xlsx)

- **Sheet name:** `"Multiple Positions"` (exact). If the sheet is missing or empty, Task 3 is skipped; Position Code assignment (Task 2) still runs.
- **Column `abbreviation`:** Must match the row’s **Position Code** from the Process Info Sheet (case-insensitive), e.g. `X002`, `xz1`.
- **Columns `position-1` … `position-5`:** Logo filename suffixes appended after a hyphen to the logo base (non-empty cells only, in column order). Example row: `X002` → `f`, `b` produces **Logo/Design Image** `103671LG-f, 103671LG-b` when **Logo ID** is `103671LG`.
- **Suffix values:** Use the same text you use in image file stems (e.g. `f`, `b`, `x93`). The script does not translate Position Code into `-f`/`-b` automatically; those letters must appear in the sheet.
- **Step 8 image files:** For non-customise rows, place files such as `103671LG-f.png` and `103671LG-b.png` in the **Normal Logo/Design** folder (top level). Step 8 looks up each comma-separated token separately.

## Rules in detail

### 1. Unmatched vs matched

- **Unmatched:** Gender Apparel is missing, empty string, or whitespace-only (rows that did not match in step-2 CL Database lookup). Written to `unmatched_orders_{token}.csv` with the same columns as the step-3 CSV (no new columns).
- **Matched:** Gender Apparel is non-empty. Only these rows receive the Position Code column and are written to `4_matched_split_and_assign_position_codes_{token}.csv`.

### 2. Logo ID to Position (Logo IDs to Positions sheet)

- Applies to **matched** rows only, after the Gender Apparel split and **before** Position Code assignment.
- **Logo ID match:** Set **Position** from the sheet’s **Positions** column (overrides CL Position).
- **No match:** Keep existing **Position** (from CL Database or blank).

### 3. Position Code — empty Position

- If Position is empty/blank (NaN or whitespace-only), Position Code = value in column Q from the Process Info row where column P = "Default Position" (match after strip, case-insensitive).

### 4. Position Code — non-empty Position

- The script **looks up** the row’s Position value in the Process Info Sheet: find the row where column P equals that text (after strip and lowercase). Use that row’s column Q as the Position Code. Example: "Front Top Center, Back Top Center" → X1, "Front Top Center" → X2, "Back Top Center" → X3, "Front, Pocket" → X4.
- If the CSV Position value does not match any row in column P, the **default code** (from the "Default Position" row) is used.

### 5. Logo/Design Image suffix expansion (Multiple Positions sheet)

Applies to **non-personalized** matched rows that have a **Logo ID**. **Customise = Yes** rows are skipped entirely.

1. **Customise = Yes:** Leave **Logo/Design Image** unchanged from step 3 (example: `07-14642-83277` stays `07-14642-83277`).
2. **Multiple Positions match:** Look up **Position Code** on the **Multiple Positions** sheet. If one or more suffixes are returned, set **Logo/Design Image** to comma-separated `base-suffix` tokens (example: `103671LG-f, 103671LG-b`).
3. **No sheet match:** Leave **Logo/Design Image** unchanged from step 3 (example: `103671LG` stays `103671LG`).

## Usage

**From the command line:**

```bash
# Required: step-3 CSV path
python scripts/split_and_assign_position_codes.py Output/3_fill_prime_and_images_902b934a-7d72-40a4-a371-65c40c2f21e5.csv

# Optional: workbook and output directory
python scripts/split_and_assign_position_codes.py Output/3_fill_prime_and_images_902b934a-7d72-40a4-a371-65c40c2f21e5.csv Data/Workbook.xlsx Output/
```

- **step3_csv** (required): Path to step-3 output CSV.
- **workbook_path** (optional): Default `Data/Workbook.xlsx` in the Data/ folder.
- **output_dir** (optional): Default `Output/`. Token is derived from the step-3 filename stem (e.g. `3_fill_prime_and_images_902b934a-...` → token `902b934a-...`).

**Dependencies:** `pandas`, `openpyxl` (install with `pip install -r requirements.txt`).

## Required columns

The step-3 CSV must contain: **Gender Apparel**, **Position**. If any are missing, the script exits with an error. If the workbook is missing, "Process Info Sheet" is missing, or there is no row with P = "Default Position", the script fails with a clear error.

## Where it fits

Pipeline step **4 (Transform)**. Consumes `Output/3_fill_prime_and_images_{token}.csv` and Data/Workbook.xlsx (**Process Info Sheet** required; **Logo IDs to Positions** and **Multiple Positions** optional). Produces `Output/unmatched_orders_{token}.csv` and `Output/4_matched_split_and_assign_position_codes_{token}.csv`. Runs after [fill_prime_and_images.md](fill_prime_and_images.md), before grouping and PDF generation. Step 8 uses the comma-separated **Logo/Design Image** tokens produced here when matching Normal Logo/Design files.

When run via the main pipeline (GUI or `pipeline_runner.run_pipeline`), any non-empty unmatched CSV is **moved** to `Unmatched SKU Files/{date}/{shift}/` at the project root (e.g. `Unmatched SKU Files/04-03-2026/1st Shift/unmatched_orders_{token}.csv`), and the pipeline reports that path. The Step 4 CLI alone does not move files; it only writes to the given output directory.
