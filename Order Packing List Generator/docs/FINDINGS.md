# Order Packing List Generator — key findings

- Input: ShipStation CSV Current View (and optional API tags). Skip Item Name containing `discount`.
- Enrichment: `Custom Label Database/Custom_Label_Database.csv` via `shared/cl_sku_match.py` (whole → after-first-dash → till-last-dash). Workbook `CL Database` sheet is archive-only for lookup.
- Column maps in `enrich_cl_lookup.py` (Position ← Print Positions, Picture Name ← Apparel Image, Prime ← Amazon Prime). Logo/Design Image has no CL column — left blank.
- Step 7 writes `DTF Des-P{process}.xlsx` under packing Output **and** copies to `SharedInbox/DTF Des/{date}/{shift}/`.
- DTF Des may remap Item-SKU via `Data/New SKU Database.csv`.
- Image folders for PDFs: Apparel, Normal Logo/Design, Customise Single/Double (pipeline indexes top-level only).
- Issue resolutions: `.cursor/issue-log.md`.
