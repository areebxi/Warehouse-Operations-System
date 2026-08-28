# preflight_issues_app.py — Preflight Issues App

Helper GUI (and package) that audits ShipStation CSVs **before** a full packing run. It reports unmatched SKUs and dry-runs missing logo/apparel image lookups without writing packing PDFs or Excel.

Implementation: [`scripts/pipeline_preflight_issues/`](../../scripts/pipeline_preflight_issues/). Launcher: [`preflight_issues_app.py`](../../preflight_issues_app.py). End-user fields: [USAGE.md](../../USAGE.md).

## Purpose

For each selected ShipStation CSV:

1. **Fetch** (Step 1) — same column mapping as the main pipeline, including **skip Discount** rows (`Item Name` contains `discount`).
2. **Enrich** (Step 2) — Custom Label Database CSV lookup (not Workbook).
3. **Fill** (Step 3) — Prime, Apparel Image, Logo/Design Image, Logo ID.
4. **Position** (Step 4) — Position Code + Multiple Positions logo expansion (in memory; no unmatched file move).
5. **Expand by Item Quantity** — same helper as Step 6 (`_expand_df_by_quantity`): each unit becomes its own row with Item Quantity `"1"` (string, for pandas StringDtype compatibility).
6. **Duplicate-order logo tokens** — same as Step 6 merge suffixing: when an Order Number appears on 2+ rows in that CSV (or Item Quantity > 1), rewrite `Order Number` / Customise `Logo/Design Image` to `base`, `base-1`, `base-2`, … so Missing Logo checks the same custom image stems as packing PDFs.
7. **Flag** each row:
   - **Unmatched SKU** = Yes when **Gender Apparel** is blank.
   - **Missing Logo** / **Missing Apparel** = Yes when a token/name is present but no matching image file is found (same top-level stem rules as Step 8). Plain-order SKUs (`plain` / `plainlg` in Item SKU) are not flagged for Missing Logo.
8. **Write** only rows with at least one Yes to a single combined CSV.

## Output

- Filename: `Preflight Issues_{DD-MM-YYYY}_{HH-MM-SS}.csv`
- Default directory: `Unmatched SKU Files/` at the project root (GUI **Output directory** can override, e.g. `Preflight Issues/`).
- Columns: enriched packing columns plus `Unmatched SKU`, `Missing Logo`, `Missing Apparel` (`Yes` / `No`).

If no rows have issues, the app reports success and does not write a CSV.

## Config

- `config/preflight_issues_config.json` — workbook (process sheets), **Custom Label Database CSV**, output dir, image folders.
- Falls back to reading `config/unmatched_skus_config.json` if the new file is missing (legacy Unmatched SKUs App).

**Workbook vs CL CSV:** Workbook feeds Process Info / Multiple Positions / Logo IDs. Custom Label enrich always uses the separate **Custom Label Database (CSV)** path (default live `Custom_Label_Database.csv`).

## Usage

```bash
python preflight_issues_app.py
# or
run_preflight_issues_app.bat
```

## Where it fits

Optional **pre-run** check. Fix CL Database entries and/or add missing image files, then run the main Packing List pipeline. Does not write under `logs/` (GUI Text only).
