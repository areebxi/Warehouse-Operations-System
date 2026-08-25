# Order Packing List Generator — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/order-packing-list-generator/`. Details: `docs/`, `USAGE.md`, `README.md`.

## Live vs helpers

| Live | Helpers / other |
|------|-----------------|
| `packing_list_app.py` + `scripts/` pipeline | `preflight_issues_app.py`, `missing_run_app.py` |
| `Data/Workbook.xlsx` (process sheets; CL Database sheet archive-only) | `Data/New SKU Database.csv` (DTF Des remap) |
| `../Custom Label Database/Custom_Label_Database.csv` | Step 2 enrich |
| `Input/` ShipStation CSVs | `Unmatched SKU Files/`, `Preflight Issues/` |
| `Output/DD-MM-YYYY/{Shift} Shift/{token}/` | Config under `config/` |
| `../Shared Inbox/DTF Des/{date}/{shift}/` | Dual-write DTF Des |

## How work is done

Eight-step pipeline: fetch ShipStation CSV → enrich from CL CSV → prime/images → position codes → process number → split by process → Excel (Picking, Orders Details, **DTF Des**) → packing PDFs. GUI or `pipeline_runner`.

SKU match: `shared/cl_sku_match.py` — whole → after-first-dash → till-last-dash on **Custom Label**. Column maps in code (not CSV renames).

DTF Des also lands in Shared Inbox for Queue Missing Logo auto-run.

## Hard do-nots

- Do not invent Gender Apparel / CL matches for unmatched rows without approval.
- Do not revive Workbook `CL Database` as the live enrich source.
- Do not mix this app’s image-folder rules with Queue’s design folders.
- No pipeline write to live Output without **yes / do it / fill / run**.

## Report changes

Say what ran (inputs, date, shift), what was written under Output and Shared Inbox, unmatched counts, and any config touched. Log resolved bugs to `.cursor/issue-log.md`.
