# fetch_input_csv.py — Step 1

First step in the pipeline: **fetch** data from a ShipStation CSV (Current View), keep selected columns with renames, and expose the result for downstream scripts (and optionally write to CSV).

## Purpose

- Read a ShipStation CSV from `Input/` (or a given path).
- Keep: Order #, Ship By, Tags, Quantity, Item SKU, Item Name, Item - Options, Item - Image URL, Gift - Message, Recipient (with renames where noted below).
- Rename: Order # → **Order Number**, Quantity → **Item Quantity**, Recipient → **Recipient Name**, Item - Name → **Item Name**, Item - SKU → **Item SKU**, Item - Options → **Item Options**, Item - Image URL → **Item Image URL**, Gift - Message → **Gift Message** (Ship By, Tags unchanged when present under those names).
- Strip whitespace from string values (e.g. Recipient often has trailing space).
- Return a list of dicts so other scripts can import and reuse the data (see **As a module** below).
- When run as main: write the same data to `Output/1_fetch_input_csv_{token}.csv` by default (the `1_` prefix indicates step 1; you can override the output path).

## Column mapping

Output column order: **Order Number, Ship By, Item Quantity, Item Image URL, Gift Message, Item SKU, Item Name, Item Options, Recipient Name, Tags.**

| ShipStation column   | Output key       |
|----------------------|------------------|
| Order # / Order - Number | Order Number |
| Ship By              | Ship By          |
| Quantity / Item - Qty| Item Quantity    |
| Item - Image URL     | Item Image URL   |
| Gift - Message       | Gift Message     |
| Item SKU / Item - SKU| Item SKU         |
| Item Name / Item - Name | Item Name     |
| Item - Options       | Item Options     |
| Recipient / Ship To - Name | Recipient Name |
| Tags                 | Tags             |

## Usage

**As a module (for other scripts):**

```python
from scripts.fetch_input_csv import fetch_input_csv  # wrapper; implementation in pipeline_cl_lookup

rows = fetch_input_csv("Input/your_export.csv")
# rows is list[dict] with keys from OUTPUT_COLUMNS (see table above)
```

**From the command line:**

```bash
# Required: input CSV path
python scripts/fetch_input_csv.py Input/b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv

# Optional: specify output CSV path
python scripts/fetch_input_csv.py Input/b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv Output/1_custom_name.csv
```

If no output path is given, output is written to `Output/1_fetch_input_csv_{token}.csv` (e.g. `Output/1_fetch_input_csv_b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv`; UTF-8). The `Output/` directory is created if it does not exist.

## Behaviour

- **Skip Discount rows:** After mapping, any row whose **Item Name** contains `discount` (case-insensitive substring) is dropped and never written to the step-1 CSV. This keeps promotional/discount line items out of the packing pipeline and Preflight Issues.
- **Missing columns:** If the CSV does not contain a mapped column, that value is an empty string and a warning is printed once per missing ShipStation column name.
- **Encoding:** Input is read with `utf-8-sig` (handles BOM if present); output CSV is UTF-8.

## Where it fits

Pipeline step **1 (Load)**. Next steps will consume the list of dicts or the `1_fetch_input_csv_{token}.csv` file for transform and PDF generation.
