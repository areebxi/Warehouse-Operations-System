# Order Packing List Generator — key findings

- Input: ShipStation CSV Current View (and optional API tags). Skip Item Name containing `discount`.
- Enrichment: `Custom Label Database/Custom_Label_Database.csv` via `shared/cl_sku_match.py` (whole → after-first-dash → till-last-dash). Workbook `CL Database` sheet is archive-only for lookup. Plain / Packs are **not** searched today — preflight Unmatched SKU = blank Gender Apparel (e.g. Packs `SET5722` still flags). **Later (not built, 2026-09-17):** also Plain + Packs; this app owns **all** packing list PDFs including PO slips. Do not clone pack/plain into CL.
- Column maps in `enrich_cl_lookup.py` (Position ← Print Positions, Picture Name ← Apparel Image, Prime ← Amazon Prime). Logo/Design Image has no CL column — left blank.
- Step 7 writes `DTF Des-P{process}.xlsx` under packing Output **and** copies to `SharedInbox/DTF Des/{date}/{shift}/`.
- DTF Des may remap Item-SKU via `Data/New SKU Database.csv`.
- Image folders for PDFs: Apparel, Normal Logo/Design, Customise Single/Double (pipeline indexes top-level only).
- **Missing logos (locked 2026-09-17):** strip after Step 5, **before** Step 6 process/item naming. Lookup still expands qty and applies custom `base` / `base-1` stems so merge siblings and second units are not missed. Naming the keepers after the drop means packing-list PIN has no holes. Do not move the filter back after Step 6. The missing-logo CSV is a **holding file** — no Item numbers. Reprint = main packing app **from Step 1**.
- Issue resolutions: `.cursor/issue-log.md`.
