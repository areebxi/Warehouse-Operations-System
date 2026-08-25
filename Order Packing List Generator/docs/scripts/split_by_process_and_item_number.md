# split_by_process_and_item_number.py — Step 6

Sixth step in the pipeline: **split** the step-5 CSV by **Process and Item Number**, **sort** each group by **Size** using the Process Info Sheet column **"Sequence by Size"** (column AD), **maintain a per-day Process Number Tracker in the workbook**, and **assign per-row Process/Item display values** before writing one CSV per value into the given **output_dir** (e.g. `Output/` for CLI default, or `Output/DD-MM-YYYY/{token}/` when run via pipeline).

## Purpose

- Read step-5 CSV (e.g. `Output/5_assign_process_number_{token}.csv`) and optionally Workbook "Process Info Sheet".
- **Group** all rows by **Process and Item Number** (each distinct value becomes one group).
- **Sort** each group by **Order Number** (only for orders with **more than one row**: same order together, most rows first), then by **Size** (Process Info Sheet "Sequence by Size"), then by **Colour** alphabetically (A–Z). Orders with exactly one row appear after all multi-row orders, sorted by Size then Colour. Rows whose Size is not in that column are placed at the **end** of the file.
- For each group, **compute extended item codes** based on merge orders and Size/Colour changes (e.g. `100ANND1X-1-1`, `100ANND1X-1-2`, `100ANND1X-2-1`), and then, when the workbook is available, format the visible value as `Process {seq}{additional} Item-{item} ({extended})`, where the number after `Process ` is the concatenation of the per-day sequence from the tracker and the per-file additional index. The parenthetical part uses a **space** before the item number (e.g. `Process 31 Item-1 (100ANCD1X-1 1)` for seq=3, additional=1).
- Write each (sorted and renumbered) group to **output_dir/{ProcessAndItemNumber}.csv**. When run from the **CLI** with default args, `output_dir` is `Output/` (all CSVs in that folder). When run via **pipeline_runner** or GUI, `output_dir` is `Output/DD-MM-YYYY/{token}/` (e.g. `Output/19-02-2026/902b934a-.../`). Filename = Process and Item Number (base), sanitized for the filesystem; blank values use `_blank.csv`.

**Logo / tracker process groups:** When step 5 assigns a process base from **Design ID Process Tracker** (e.g. `10000`) or a fixed numeric value (e.g. `100`), those rows form a separate group/CSV. Step 6 uses the **same normal sort** (merge, then size, then colour) for all groups; no special sort for logo IDs.

## Process Info Sheet — Sequence by Size

- **Sheet:** "Process Info Sheet" (same as step 5).
- **Column AD** (0-based index 29), or first column whose header is **"Sequence by Size"**: lists size values in the desired order (top to bottom = first to last). E.g. XS, S, M, L, XL or 5-6 Years, 7-8 Years, etc.
- **Matching:** CSV **Size** is compared to sheet values after strip and case-insensitive. Sizes not in the list are assigned a rank so they sort to the end.

## Behaviour

1. Require columns **"Process and Item Number"**, **"Size"**, **"Order Number"**, and **"Colour"** in the step-5 CSV.
2. **Expand by Item Quantity:** Each row with Item Quantity N is replaced by N rows with Item Quantity **`"1"`** (string, not int) via [`grouping_quantity._expand_df_by_quantity`](../../scripts/pipeline_split_by_process_item/grouping_quantity.py) (like DTF Des). So each unit gets its own row and later a distinct extended Process and Item Number. Using a string keeps compatibility with pandas **StringDtype** / `infer_string` (avoids `Invalid value '1' for dtype 'str'` on stricter installs). If the column is missing, no expansion is done.
3. If a workbook path is given, load **"Process Info Sheet"** and build the size sequence from **"Sequence by Size"**. If the workbook is missing or the column is not found, no sorting is applied (original row order within each group).
4. Group rows by **Process and Item Number** (blank/empty normalized to one group).
5. Build per-group metadata for the **Process Number Tracker** using the step-5 data:
   - `process_name` = base Process and Item Number (the CSV filename stem, e.g. `100ANCD1X`, sanitized for the filesystem).
   - `Prime` flag: **Prime = Yes** (case-insensitive) in any row of the group.
   - `Dispatch today` flag: any row whose **Ship By** date equals **today’s date** (DD-MM-YYYY, D/M/YYYY, or ISO YYYY-MM-DD).
5. Load or create a **"Process Number Tracker"** sheet in the workbook:
   - **Columns:** A = Date, B = Process Number, C = Sequence Number.
   - Consider **only rows whose Date equals today**; find today’s maximum numeric Sequence Number. If there are no rows for today, start at 10000.
   - From the current run’s groups, build a list of today’s processes sorted as:
     - Prime processes first (Prime = Yes), alphabetically by Process Number.
     - Then dispatch-today processes (Ship By = today), alphabetically.
     - Then the rest, alphabetically.
   - For this sorted list, **skip any Process Number that already exists for today’s date** in the tracker (to avoid duplicates on reruns).
   - Assign per-day sequence numbers to the **new** processes only (continuing after today’s max): 10000, 10001, 10002, … for the day. Append one row per new process to the tracker: `Date = today`, `Process Number = process_name`, `Sequence Number = assigned sequence`.
7. For each group (after expansion, each row has Item Quantity `"1"`; merge = Order Number on 2+ rows):
   - **Merge rows** = rows where **Order Number** appears **2 or more times** in the group (multi-row orders; single-line qty>1 became multiple rows in step 2). All merge rows are assigned to **additional block 1** (e.g. `{base}-1-1`, `{base}-1-2`, …). **Only these rows** are sorted alphabetically by **Recipient Name** (A–Z) before assigning their `item` numbers. For personalised merge rows (`Customise = "Yes"`), Step 6 also normalises the `Logo/Design Image` stem **per unit** so the first customised row for a given Order Number keeps `Logo/Design Image = OrderNumber`, the second becomes `OrderNumber-1`, the third `OrderNumber-2`, and so on; these stems are later used by the PDF generator to locate per-row custom logo files in the **Customise Logo/Design** folder.
   - **Non-merge rows** = orders with exactly one row in the group (after expansion). They are ordered by **Gender Apparel** (Men, then Women, then Kids when those words appear in the value; otherwise no gender order), then **Size sequence** (from Process Info Sheet), then **Colour** (A–Z), then **Recipient Name** (A–Z). If "Recipient Name" is missing, no alphabetical tiebreaker is applied. No "multi-row orders first" step (merge rows are already in block 1). Their `additional`/`item` values increment when **Gender Apparel**, Size, or Colour (normalized) changes from the previous row: when the group **has** merge rows, non-merge start at **additional=2**; when there are **no** merge rows, **additional starts at 1** (first block is `{base}-1-*`, etc.).
   - **Internal extended code:** `{base}-{additional}-{item}`; `base` = original Process and Item Number from step 5 (e.g. `3700`). Output row order: merge rows first (Recipient Name order), then non-merge rows (Gender Apparel → Size → Colour → Recipient Name order).
  - When a per-day sequence number exists for that `process_name`, the visible value written into **"Process and Item Number"** is formatted as:  
     - `Process {seq}{additional} Item-{item} ({extended})`  
     - The number after `Process ` is the concatenation of: **seq** = per-day sequence from the Process Number Tracker, and **additional** = the per-file block index.  
     - The parenthetical extended code uses a **space** before the item number (e.g. `Process 31 Item-1 (100ANCD1X-1 1)` for seq=3, additional=1). The parentheses always contain the full extended code for reference.  
   - If no workbook / tracker is available, the script falls back to writing just the internal extended code (`{base}-{additional}-{item}`) as before.
   - **When use_simple_process_format is True** (optional; not used by the pipeline for fixed process number runs): the Process Number Tracker is **not** loaded or updated, and **"Process and Item Number"** is formatted as `Process {base}-{additional} Item-{item}` instead of `Process {seq}{additional} Item-{item} ({extended})`. The pipeline always passes `use_simple_process_format=False` for normal runs.
   - **Pure numeric process base** (digits only, e.g. `10000`, `100`, `4200`): **"Process and Item Number"** is formatted as `Process {display_base} Item-{item}`, where `display_base` starts at the base value for `additional=1` and increments by 1 for each additional block (`10000`, `10001`, `10002`, …). This applies to **any** group whose step-5 base is purely numeric — including **Design ID Process Tracker** assignments (e.g. `49641LG` → `10000`) and fixed numeric process runs — not only when the fixed process number matches the group base.
   - **Non-numeric process base** (e.g. `49641LG`, `100A`, `200CNND1X`): use tracker format `Process {seq}{additional} Item-{item} ({extended})` when the Process Number Tracker is available, or simple format `Process {base}-{additional} Item-{item}` when `use_fixed_numeric_process` is True but the group base is not numeric.
   - **When use_fixed_numeric_process is True** (fixed process number selected and the value is **numeric-only**, e.g. `4200`): the Process Number Tracker is **skipped** for this run. Numeric-base groups use the increment format above; non-numeric groups in the same run use `Process {base}-{additional} Item-{item}`.
   - Write the result to **output_dir/{sanitized_name}.csv**. Invalid filename characters are replaced with `_`; empty Process and Item Number → `_blank.csv`.

## Position: Draw replace, then slash merge

When writing each step-6 CSV, the script may rewrite **Position** in two stages (when **Position**, **Logo/Design Image**, and **Item SKU** columns are present):

### 1. Draw replace (Process Info Sheet column R)

When the workbook is available, each row’s **Position Code** is looked up on the **Process Info Sheet** (column **Q** → **Draw**, column **R**). If a non-empty Draw value exists, **Position** is replaced with that Draw text before any slash merge. Example: CL text `Front Top Center` with code `X004` and Draw `Front` → **Position** becomes `Front`. Multi-position codes may use comma-separated Draw values (e.g. `Front, Back`).

- **Default Position Code** (`X`): **Position** is set to blank (same as Step 8 PDF banners).
- **No Draw match:** CL **Position** text is kept unchanged.
- Lookup is **case-insensitive** (`x004` matches `X004`).

### 2. Slash merge (single-logo rows only)

After Draw replace, when **Logo/Design Image** splits into **exactly one** comma-separated token and the (possibly Draw-replaced) **Position** has **two or more** comma-separated parts, those parts are joined with **` / `** (space–slash–space). Example: Draw `Front, Back` with one logo → **Position** becomes `Front / Back`.

- A single Draw part (or **Position** already written with slashes but no commas) is left as-is.
- **Customise** is **not** required for either stage.

## Usage

**From the command line:**

```bash
# Required: step-5 CSV path
python scripts/split_by_process_and_item_number.py Output/5_assign_process_number_902b934a-7d72-40a4-a371-65c40c2f21e5.csv

# Optional: workbook and output directory
python scripts/split_by_process_and_item_number.py Output/5_assign_process_number_902b934a-7d72-40a4-a371-65c40c2f21e5.csv Data/Workbook.xlsx Output/
```

- **step5_csv** (required): Path to step-5 output CSV.
- **workbook_path** (optional): Default `Data/Workbook.xlsx` in the Data/ folder. Used for both "Sequence by Size" and the **Process Number Tracker** (if present).
- **output_dir** (optional): Default `Output/`. One CSV per process is written **directly** under this folder (e.g. `Output/100ANND1X.csv`).

**Dependencies:** `pandas`, `openpyxl` (for workbook; install with `pip install -r requirements.txt`).

**Output location:** With default `output_dir` (`Output/`), CSVs are written to `Output/{ProcessAndItemNumber}.csv`. When the pipeline runner or GUI is used, they pass `Output/DD-MM-YYYY/{Shift} Shift/{token}/` so all step-6 CSVs, Excel files, and PDFs for that run live in one folder.

## Required columns

The step-5 CSV must contain: **Process and Item Number**, **Size**, **Order Number**, **Colour**. If any are missing, the script exits with an error. **Recipient Name** is used to sort merge rows (block 1) alphabetically when present; if missing, merge rows keep their original order.

## Edge cases

- **Empty Process and Item Number:** Rows are grouped together and written to `_blank.csv`.
- **Size not in "Sequence by Size":** Those rows appear at the end of the file (after all sequenced sizes).
- **No workbook or missing "Sequence by Size":** Script runs without sorting; row order within each group is unchanged.

## Where it fits

Pipeline step **6 (Transform / Group)**. Consumes `Output/5_assign_process_number_{token}.csv` and optionally Workbook "Process Info Sheet" plus **Process Number Tracker**. Produces one CSV per Process and Item Number under the given `output_dir`, with the **"Process and Item Number"** column formatted as `Process {seq}{additional} Item-{item} ({extended})` when the tracker is available; the parenthetical extended code uses a space before the item number (e.g. `4200-1 1`). Runs after [assign_process_number.md](assign_process_number.md), before [generate_excel_outputs.md](generate_excel_outputs.md) and [generate_packing_list_pdf.md](generate_packing_list_pdf.md).
