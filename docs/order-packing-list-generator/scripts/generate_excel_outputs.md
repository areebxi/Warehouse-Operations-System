# generate_excel_outputs.py — Step 7 (Excel export)

Seventh step in the pipeline: **generate three Excel files** for each step-6 split CSV — Picking, Orders Details, and DTF Des. When run via the pipeline, this runs after step 6 (for each step-6 CSV) before PDF generation (step 8). Outputs are written to the same folder as the step-6 CSVs.

## Purpose

- Read a step-6 CSV (e.g. `100ANND1X.csv`).
- Write three Excel files in the output directory:
  - `{ProcessBase}-Picking.xlsx` — Picking sheet with expanded rows by quantity, two column blocks.
  - `Orders Details-P{ProcessBase}.xlsx` — Sheet1 with one row per **process+additional block**; Condition, Merge/Single, process+additional block stats, etc.
  - `DTF Des-P{ProcessBase}.xlsx` — Sheet1 with Order - Number, Item - Qty, Item - SKU, Ship To - Name, Process Num ("Process " + process number), Genre, etc.; column **N** = **Customise** (`Yes` or blank, from step-6 CSV); column P = Item Num ("Item 1", "Item 2", … from process item number). For non-custom rows, SKUs that contain multiple design IDs (each `\d+(LG|TSU|AV|HK)` start and/or **fawad**+digits start, case-insensitive on `fawad`) are split into separate segments so each design appears as its own `Item - SKU` row; for customised rows (`Customise = "Yes"`), the original combined SKU is kept and not split. **Item - SKU** values are optionally rewritten using the New SKU Database — see [DTF Des: New SKU database remap](#dtf-des-new-sku-database-remap) below.

Filenames use the CSV stem (process base). **Content** (Picking Number, Process Number in cells) uses **{seq}** (tracker display number, e.g. 31) when the step-6 CSV uses tracker format; otherwise process base and base-additional. Step-6 may write the extended code in parentheses with a space before the item number (e.g. `4200-1 1`); this script parses both that format and the legacy hyphenated form. When the pipeline is run with **Use fixed process number**, the DTF Des workbook uses **{base}{additional}** (no dash) for Process Num; the script receives this via the optional `use_fixed_process_number` argument. Full column and layout detail is in the **Output files** section below and in the script docstrings.

## Usage

**From the command line:**

```bash
python scripts/generate_excel_outputs.py <step6_csv> <output_dir> <date_dd_mm_yyyy>
```

- **step6_csv** (required): Path to a step-6 split CSV (e.g. `Output/19-02-2026/{token}/100ANND1X.csv`).
- **output_dir** (required): Directory where the three `.xlsx` files will be written (usually the same folder as the CSV).
- **date_dd_mm_yyyy** (required): Dispatch/run date (DD-MM-YYYY or YYYY-MM-DD), used for Picking Col0.

**Via pipeline:** The pipeline runner calls this for each step-6 CSV automatically after step 6 as step 7; no separate invocation needed.

**Dependencies:** `pandas`, `openpyxl` (same as other pipeline scripts).

## Output files

| File | Sheet | Content summary |
|------|--------|------------------|
| `{Base}-Picking.xlsx` | Picking | Rows expanded by Item Quantity; Col0 = date. Picking Number (first row) and Process Number in cells use **{seq}** when step-6 uses tracker format, else process base / base-additional. Block 1 and Block 2: Process Number, Item Number, Custom Label, Gender-Apparel, Color, Size, Qty, Bulk; Block 2 AB/AC = `Process ` (space) + process value and `Item-` + item index. |
| `Orders Details-P{Base}.xlsx` | Sheet1 | One row per **process+additional block**. Process Number in cells = **{seq}** when tracker format, else base-additional. Condition, gender+colour+size or "Merge Orders", distinct recipients, total quantity, Normal/Personalised(-Merge). |
| `DTF Des-P{Base}.xlsx` | Sheet1 | One row per unit (expand by Item Quantity × segments). Process Num = "Process " + **{base}{additional}** (no dash) when fixed process number; else **{seq}** when tracker format, else process (base-additional). Order - Number, Item - Qty = 1, Item - SKU, Ship To - Name, Genre; column **N** = **Customise** (`Yes` or blank); column P = Item Num ("Item 1", "Item 2", …). For **non-custom rows**, `Item - SKU` is split by design-id starts (`\d+(LG|TSU|AV|HK)` and **fawad**+digits, case-insensitive on `fawad`) so a SKU with multiple such tokens produces one row per segment; for **customised rows** (`Customise = "Yes"`), the SKU is **not** split and the combined value from step 6 is preserved. **`Item - SKU`** may be remapped from the New SKU Database (see next section). |

## DTF Des: New SKU database remap

Only **DTF Des** applies this mapping. **Picking** (Custom Label) and **Orders Details** still use the original **Item SKU** from the step-6 CSV.

**Source file:** `Data/New SKU Database.csv` (path is fixed relative to the project root in `generate_excel_outputs.py`).

**Columns used (only these two):**

| Column | Role |
|--------|------|
| `Company-Custom-Label` | Lookup key (trimmed; match is case-insensitive). |
| `Old-Company-Custom-Label` | Replacement text for the company-label part of the segment. |

Any other columns in the CSV (for example `Alternative-Company-Custom-Label`) are **ignored** for this step.

**Loading behaviour:**

- If the file **does not exist**, remapping is skipped (no error).
- If the file **exists** but either required column is missing, the script raises `ValueError`.
- Duplicate `Company-Custom-Label` keys: **first row wins**.

**How each emitted `Item - SKU` segment is rewritten**

Item SKUs often look like `{designId}-{companyLabelTail}`, where **designId** is one of:

- `[optional alphanum]digits(LG|TSU|AV|HK)` then `-` (e.g. `162547LG`, `M39553LG`, `4486HK`), or  
- `fawad` + digits then `-` (case-insensitive on `fawad`, e.g. `fawad22`), or  
- `[A-Za-z0-9]*digitsPER` then `-` (PER-style id).

The **company-label tail** after that first hyphen is what must appear in **Company-Custom-Label** in the database (e.g. `ARI-BDg-C1-D1-E3`). When a row matches, the output is **`{designId}-` + `Old-Company-Custom-Label`**, so the **design id** (LG / TSU / AV / HK / fawad+digits / PER) **is preserved** and only the tail is swapped.

If the segment has an extra token **before** the design id (e.g. `ORDER-162547LG-ARI-…`), the script strips that leading prefix, remaps the `162547LG-…` part, then puts the prefix back: `ORDER-162547LG-{old tail}`.

If there is no design-id match and the segment is still `prefix-tail` on first hyphen, it tries a direct map on the substring after the first hyphen, then on the whole segment.

If no key matches, the segment is left unchanged.

**Example**

- Item SKU segment: `162547LG-ARI-BDg-C1-D1-E3`  
- DB row: `Company-Custom-Label` = `ARI-BDg-C1-D1-E3`, `Old-Company-Custom-Label` = `M-T-NAT-M`  
- **Item - SKU** in DTF Des: `162547LG-M-T-NAT-M`  

## Required columns (step-6 CSV)

Order Number, Item Quantity, Item SKU, Item Name, Recipient Name, Process and Item Number, Gender Apparel, Size, Colour.

## Where it fits

Pipeline step **7 (Excel export)**. Runs after step 6; for each step-6 CSV, writes the three Excel files, then step 8 (PDF) runs. Consumes step-6 CSV and dispatch date; produces Picking, Orders Details, and DTF Des workbooks in the same output folder.
