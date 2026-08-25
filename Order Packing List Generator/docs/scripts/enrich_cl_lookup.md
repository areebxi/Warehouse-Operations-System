# enrich_cl_lookup.py — Step 2

Second step in the pipeline: **enrich** packing data by matching Item SKU to the Workbook "CL Database" sheet and appending ten columns from the matching row (or leaving them empty if no match).

**CLI:** `python scripts/enrich_cl_lookup.py` (wrapper around `scripts/pipeline_cl_lookup/enrich_cl_lookup.py`).

## Purpose

- Read step-1 output CSV (typically `Output/1_fetch_input_csv_{token}.csv`) and Data/Workbook.xlsx sheet **"CL Database"**.
- For each row, derive a **lookup key** from the **Item SKU** cell (see rule below).
- **Exact match** that key to the **Custom Label** column in "CL Database" (trimmed, **case-insensitive**).
- Append **ten columns** in this order: Process and Item Number, Gender Apparel, Size, Colour, Picture Name, Position, Customise, Prime, Apparel Image, Logo/Design Image. Fill from the matching CL Database row, or leave empty if no match.
- Write result to `Output/2_enrich_cl_lookup_{token}.csv` by default (you can override the output path).

## Lookup key from Item SKU (two-step)

Matching is **exact** and **case-insensitive**. Rows that match in an earlier step are filled and kept separate; only rows that did not match are tried in later steps.

**Step 1 — After first dash (CL Database):** For each row, take the substring **after the first dash** in Item SKU. Use this as the lookup key. Match against the "Custom Label" column in "CL Database". Rows that match are filled from the CL Database row.

- Example: `ABC-DEF-GHI` → key `DEF-GHI`
- If there is no dash in Item SKU, the key is empty and step 1 is skipped for that row.

**Step 2 — Whole Item SKU (no trimming):** For rows that did not match in step 1, use the **whole Item SKU** as the lookup key (**no trimming**). Match against "Custom Label" in "CL Database". Fill if found.

`Item SKU` in the output is **not** rewritten; it stays as in step 1.

## Column mapping (CL Database → output)

The script maps CL Database columns to the output columns by name. It tries these names in order (first existing column wins):

- **Process and Item Number** — "Process and Item Number"
- **Gender Apparel** — "Gender Apparel"
- **Size** — "Size"
- **Colour** — "Colour", "Colour Name", "Color"
- **Picture Name** — "Picture Name"
- **Position** — "Position"
- **Customise** — "Customise", "Customize"
- **Prime** — (output column only; not filled from CL Database yet; to be defined later)
- **Apparel Image** — "Apparel Image", "Apparel Picture"
- **Logo/Design Image** — "Logo/Design Image", "Design Picture", "Logo/Design"

If a column is missing in "CL Database", that output column stays empty for all rows (no crash; optional warning).

## Usage

**From the command line:**

```bash
# Required: step-1 CSV path
python scripts/enrich_cl_lookup.py Output/1_fetch_input_csv_b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv

# Optional: specify Workbook and output paths
python scripts/enrich_cl_lookup.py Output/1_fetch_input_csv_b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv Data/Workbook.xlsx Output/2_enrich_cl_lookup_b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv
```

If no workbook path is given, `Data/Workbook.xlsx` is used by default.  
If no output path is given, `Output/2_enrich_cl_lookup_{token}.csv` is used by default, where `token` is normally the original ShipStation CSV stem. For files named like `1_fetch_input_csv_{token}.csv`, the same token is used.

**Dependencies:** `pandas`, `openpyxl` (install with `pip install -r requirements.txt`).

## Unmatched Item SKUs

Matching is tried in two stages: first with the substring after the first dash, then with the whole Item SKU (no trimming). For any row where neither matches the "Custom Label" column of "CL Database", the ten new columns are left empty. The row is still written to the output CSV with the original columns and empty new columns.

## Customise from Item Name (auto)

After CL lookup, if **Item Name** contains any of these substrings (case-insensitive): `personalised`, `personalized`, `custom`, `customisable`, `customizable`, and **Customise** is not already `Yes`, the script sets **Customise** = `Yes`.

## Customise from Item Options (auto)

After CL lookup and the Item Name pass, if **Item Options** (from step 1, mapped from ShipStation **Item - Options**) contains any of these phrases (case-insensitive substring), and **Customise** is not already `Yes`, the script sets **Customise** = `Yes`:

- `message if you do need customisation`
- `back print option`

Examples: `Message if you do need customisation: Your text here` or `Back Print Option: Company Logo` → Customise = Yes.

## Where it fits

Pipeline step **2** (after fetch, before further transform/PDF). Consumes `Output/1_fetch_input_csv_{token}.csv` and produces `Output/2_enrich_cl_lookup_{token}.csv`.
