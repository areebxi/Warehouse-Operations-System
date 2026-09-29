# Order Packing List Generator — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/order-packing-list-generator/`. Details: `docs/`, `USAGE.md`, `README.md`.

Live paths via `shared/paths.py` (DB in `database/`; run I/O + GUI config in this app; Tags + SharedInbox + ShipStation shared).

## Live vs helpers

| Live | Helpers / other |
|------|-----------------|
| `packing_list_app.py` + `scripts/` pipeline | `preflight_issues_app.py`, `missing_run_app.py` |
| `database/order-packing-list-generator/Workbook.xlsx` | `New SKU Database.csv`, `All Orders.csv` |
| `database/shared/custom_label/Custom_Label_Database.csv` | Step 2 enrich |
| `database/shared/shipstation_tags/ShipStation_Tags.xlsx` | Shared tags |
| `{Input,Output,Logs,…}/` | `config/` GUI JSON |
| `config/ShipStation/.env` | ShipStation credentials |
| `runtime/SharedInbox/DTF Des/{date}/{shift}/` | Dual-write DTF Des |

## How work is done

Eight-step pipeline: fetch ShipStation CSV → enrich from CL CSV → prime/images → position codes → process number → **drop missing logos** → split by process (names remaining, no PIN gaps) → Excel (Picking, Orders Details, **DTF Des**) → packing PDFs. GUI or `pipeline_runner`. Missing-logo strip is **before** Step 6 naming (locked 2026-09-17). Missing-logo CSV is a holding file only; reprint = this app **from Step 1**.

Sorter input stems shorten to **`B#-S#`** for PIN / Excel / PDF / preflight / Output folder / missing-logo filenames (`pin_batch_shift`). Example: `B1-S1-PLAIN-2-SUPPLY ON DEMAND-R-9` → `B1-S1`, PIN `B1-S1-1 Item 1`.

SKU match today: `shared/cl_sku_match.py` — whole → after-first-dash → till-last-dash on **Custom Label** only. Preflight Unmatched SKU = blank Gender Apparel.

**Later (not built, 2026-09-17):** every packing list PDF is this app’s — including slips Purchase Order Generator still prints. Enrich/preflight also hit Plain Database + Packs (sorter keys). Catalog hit ≠ unmatched. Do not clone pack/plain SKUs into CL.

DTF Des also lands in SharedInbox for Queue Missing Logo auto-run.

## Hard do-nots

- Do not invent Gender Apparel / CL matches for unmatched rows without approval.
- Do not revive Workbook `CL Database` as the live enrich source.
- Do not move shared Tags / SharedInbox / ShipStation secrets into this app alone.
- No pipeline write to live Output without **yes / do it / fill / run**.
- Step 6 (`pipeline_split_by_process_item/service.py`) must import `_normalize_key` from `.common`. Dropping it crashes after the Step 5 CSV with `name '_normalize_key' is not defined`.
- Do not strip missing logos **after** Step 6 naming — that leaves PIN gaps. Filter after Step 5, before naming.

## Report changes

Say what ran (inputs, date, shift), what was written under Output and SharedInbox, unmatched counts, and any config touched. Log resolved bugs to `.cursor/issue-log.md`.
