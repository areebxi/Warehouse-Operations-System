# CL Database Maker - Work Summary

## What you asked for

You wanted a simple Python script to bring values from `ProductExport.csv` into `CL DatabaseX.csv`, based on placeholders written in `{}` inside the CL template file.

## Files involved

- Input source: `ProductExport.csv`
- Template: `CL DatabaseX.csv`
- Script created: `fill_cl_database.py`
- Outputs generated:
  - `CL DatabaseX_filled.csv`
  - `CL DatabaseX_filled_v2.csv` (newer output with updated `Picture Name` logic)

## Clarifications captured

1. Output should be a **new CSV file**.
2. `{UID}` uses the `UID` column from `ProductExport.csv`.
3. Existing non-template/example rows in `CL DatabaseX.csv` are kept as instructed.
4. Placeholder template rows are replaced/expanded by generated rows.
5. Embedded newlines inside quoted CSV cells must be preserved (to match your sample format).
6. `Picture Name` should be derived from filled values:
   - `Gender Apparel` + `Colour Name`
   - whitespace (spaces/newlines) converted to `-`
   - example: `GILDAN-Softstyle-Adult-T-Shirt-Antique-Cherry-Red`

## Script behavior implemented

The script `fill_cl_database.py` now:

- Reads `ProductExport.csv` with `csv.DictReader`.
- Reads `CL DatabaseX.csv` with `csv.reader` using proper newline handling.
- Detects template rows by checking for `{...}` tokens.
- Replaces placeholders like `{UID}`, `{Brand}`, `{Description}`, `{Colour Name}`, `{Size}` with matching source values.
- Expands each template row to one output row per product row.
- Preserves quoted multi-line cell formatting.
- Computes `Picture Name` when template value is `(Gender Apparel)-(Colour Name)` by converting whitespace/newlines to dashes and joining both parts.

## Verification performed

- Python availability confirmed.
- Script executed successfully to generate output files.
- First-row check confirmed:
  - `Gender Apparel`: contains embedded newline
  - `Colour Name`: filled correctly
  - `Picture Name`: computed as dashed combined value

## Notes

- One run failed to overwrite `CL DatabaseX_filled.csv` due to file lock/permission (`Errno 13`), so output was written to `CL DatabaseX_filled_v2.csv`.
- No linter errors were reported for `fill_cl_database.py`.

## Apparel image download

Script: `download_apparel_images.py`

- Joins Custom Label Database mock rows → ProductExport `UID` (label suffix) → **`colour image 01`**
- Saves files under `Apparel Images/` using the **exact `Apparel Image` name** from the database (+ URL extension)
- Default: only mocks added by `generate_from_mocks` (vs `preGenerate` backup). Use `--all-mocks` for every `M##` row.

```powershell
python "d:\Custom Label Database\Custom Label Database Maker\download_apparel_images.py"
python "d:\Custom Label Database\Custom Label Database Maker\download_apparel_images.py" --dry-run
python "d:\Custom Label Database\Custom Label Database Maker\download_apparel_images.py" --all-mocks
```

Legacy: `download-images.ps1` still names files from Brand-Description-Colour on ProductExport alone (not DB Apparel Image).

## Run command

```powershell
python "d:\Cursor\CL Database Maker\fill_cl_database.py" --product "d:\Cursor\CL Database Maker\ProductExport.csv" --template "d:\Cursor\CL Database Maker\CL DatabaseX.csv" --out "d:\Cursor\CL Database Maker\CL DatabaseX_filled.csv"
```

