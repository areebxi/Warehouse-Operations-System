# data/

Shared tabular files used by more than one app:

- `product_export/ProductExport.csv` — CL + Purchase Order
- `shipstation/ShipStation_Tags.xlsx` — Packing + Purchase Order
- `archive/` — shared backups / former local copies

App-owned workbooks, stock CSVs, and images live inside each app folder.
Custom Label live CSV stays under `Custom Label Database/`.

Resolve via `shared/paths.py`. Do not commit live files (see root `.gitignore`).
