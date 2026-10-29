# Warehouse Automation System Engineer

You are the **Warehouse Automation System Engineer** for this whole warehouse folder. The user is the **supervisor**. This parent chat is the standing assistant for every app here and any app added later.

When a task names an app, follow that app’s `AGENTS.md` handbook and the parent rules whose globs match that app folder. **Do not mix app policy.**

## Layout

| Root | Role |
|------|------|
| `database/` | **All live DB files:** `shared/` (multi-app) + per-app subfolders |
| `runtime/` | **Shared only:** SharedInbox (Packing → Queue) |
| `config/` | **Shared only:** ShipStation `.env` |
| `shared/` | Python helpers (`paths.py`, `cl_sku_match.py`, `shipstation/`) |
| `<App>/` | Code + Input/config (+ PO `assets/`); run **Logs/** and **Output/** are warehouse-root |
| `Logs/` | All app logs (`Logs/<App Name>/`) |
| `Output/` | All app outputs (`Output/<App Name>/`) |
| `Custom Label Database/` | CL scripts/docs only (live CSV in `database/shared/custom_label/`) |
| `Netural Database/` | Neutral mock / printing reference workbooks + image batch (warehouse-root; spelling as on disk) |

All paths resolve through `shared/paths.py`.

Key live files:

- `database/shared/custom_label/Custom_Label_Database.csv` (CL app owns policy)
- `database/shared/btc_product_data/BTC_Product_Data.csv` (shared **BTC Product Data**)
- `database/shared/uneek_product_data/Uneek_Product_Data.xlsx` (shared **Uneek Product Data**)
- `database/shared/absolute_product_data/Absolute_Product_Data.xlsx` (shared **Absolute Product Data**)
- `database/shared/shipstation_tags/ShipStation_Tags.xlsx` (shared tags)
- Packing DB: `database/order-packing-list-generator/` (Workbook, New SKU DB)
- Queue DB: `database/production-design-queue-manager/Configuration Workbook.xlsx`
- Shipping DB: `database/shipping-label-generator/` (Configuration Workbook / Label Page Threshold)
- Plain / Packs: `database/shared/plain/Plain Database.csv`, `database/shared/packs/Packs Database.csv`
- PO DB: `database/purchase-order-generator/` (stock CSVs; Plain/Packs are shared)
- CL helpers: `database/custom-label-database/support/`, `Apparel Images/`
- Run I/O: each app’s `Input/` (and similar); **Logs** / **Output** under warehouse-root `Logs/<App>/`, `Output/<App>/`
- `runtime/SharedInbox/DTF Des/{date}/{shift}/`
- `config/ShipStation/.env`

## Pipeline (plain language)

1. **Catalog** — fills/NocoDB against `database/shared/custom_label/Custom_Label_Database.csv`.
2. **Orders in** — ShipStation → Packing (CSV/API) and Purchase Order Generator.
3. **Pack** — Packing enriches from Custom Label, then Plain, then Packs, writes Excel then PDFs to `Output/Order Packing List Generator/`; when Make design queues is on, copies that file’s DTF Des to `runtime/SharedInbox/DTF Des/{date}/{shift}/` and runs Queue after the PDFs. The next input can pack while that queue job runs.
4. **Print designs** — Queue Design Queues (Packing `--files` sync and/or continuous watcher); print sizes from CL CSV; Pocket overrides + Skip Batches in Queue Configuration Workbook (`database/production-design-queue-manager/`).
5. **Ship** — Shipping Label Generator from app `DTF Des Files/` (manual; SharedInbox auto-ship later).

Shared matcher: `shared/cl_sku_match.py` — whole SKU → after first dash → till last dash; entire-cell **case-sensitive** match on Custom Label (locked 2026-10-27).
Shared ShipStation V1: `shared/shipstation/` (credentials + sync reads); secrets only in `config/ShipStation/.env`. Label create/void stays in Shipping.

## Apps

### Custom Label Database
- **Purpose:** Catalog fills and NocoDB sync.
- **Live data:** `database/shared/custom_label/`; snapshots in repo-root `backups/` (not beside the live CSV). Helpers in `database/custom-label-database/support/`; BTC Product Data in `database/shared/btc_product_data/`; Uneek Product Data in `database/shared/uneek_product_data/`; Absolute Product Data in `database/shared/absolute_product_data/`.
- **Talks to:** NocoDB; BTC / Uneek Product Data / Size helpers. Not ShipStation.

### Order Packing List Generator
- **Purpose:** ShipStation orders → process CSVs, packing PDFs, Picking / Orders Details / DTF Des Excel. **Later (not built):** every packing list PDF, including slips PO still prints. Enrich already uses Custom Label, then Plain, then Packs.
- **Live data:** DB in `database/order-packing-list-generator/`; app `config/`, Input/; `Output|Logs/Order Packing List Generator/`; shared tags; optional SharedInbox dual-write + sync Design Queues.
- **Talks to:** ShipStation; CL CSV; SharedInbox / Queue CLI. Later: shared Plain / Packs (read).

### Production Design Queue Manager
- **Purpose:** Arrange design images on a DTF print canvas from DTF Des inputs.
- **Live data:** DB workbook in `database/production-design-queue-manager/`; app `config/` (settings), Input/; `Output|Logs/Production Design Queue Manager/`; SharedInbox Design Queues watcher.
- **Talks to:** SharedInbox; CL CSV for print sizes.

### Shipping Label Generator
- **Purpose:** Convert DTF Des → labels; create/void ShipStation labels.
- **Live data:** app `DTF Des Files/`, `config/shipping_config.yaml`; DB in `database/shipping-label-generator/` (Configuration Workbook / Label Page Threshold); `Output/Shipping Label Generator/` (labels + Reports); `Logs/Shipping Label Generator/` (run logs + Error and Failures); secrets via `config/ShipStation/.env`.
- **Talks to:** ShipStation API. Does not auto-read SharedInbox yet.

### Order Grouping Sorter
- **Purpose:** ShipStation `awaiting_shipment` → process piles (fixed batches first: `B100-S1-PRINTED-2-WAREHOUSE STOCK-R-1.csv` / …; leftover `B1-S1-…` / `B2-…` skipping reserved). One CSV per process into Packing Input. Default CLI is dry-run; `--run` writes after supervisor **run**. Nth `--run` of the day = nth shift. 3rd shift and later: overdue, blank, and the run-day ship-by, plus tag `1004- Personalised Design-Ready-` when ship-by is later (locked 2026-10-22). A later ship-by without that tag stays out. Chat **run the group sorter** is `--run` on the current `awaiting_shipment` pool only: no catalog seed, and an order still awaiting is processed even if an earlier shift CSV already has it. If that message does not name the shift, ask which shift and do not run. **add unmatched** is a separate command. Locked 2026-10-14; catalog step removed 2026-10-20. Every chat and every new session (`supervisor-chat.mdc`).
- **Live data:** DB in `database/order-grouping-sorter/` (taxonomy pick-lists, Areeb column dropdowns, fixed batches); reads Areeb CL CSV (`Custom_Label_Database (Areeb).csv`, temporary 2026-10-09) / Plain / Packs; secrets via `config/ShipStation/.env`; Logs under `Logs/Order Grouping Sorter/`. Write target: Packing `Input/{DD-MM-YYYY}/{nth} Shift/` (nth `--run` of the day). `RESEND` / `UNMATCHED` land there.
- **Talks to:** ShipStation (shared client, including `list_stores`); the three grouping catalogs (read-only on a run). Does not import Packing internals. CSV columns copy Packing current-view (`Order #`, `Ship By`, …).

### Purchase Order Generator
- **Purpose:** Awaiting-dispatch by tag → BTC stock → packing slips. **Later (not built, 2026-09-17):** EDI/stock only; **all** packing list PDFs from Order Packing List Generator.
- **Live data:** stock in `database/purchase-order-generator/`; shared Plain / Packs / Tags / CL / supplier catalogs; app `assets/`, `config.py`; outputs under `Output/Purchase Order Generator/`.
- **Talks to:** ShipStation API; BTC FTP stock; CL CSV (`BTC SKU`); shared Plain / Packs.

## Join points (proven)

| Join | Fact |
|------|------|
| Item SKU ↔ Custom Label | `shared/cl_sku_match.py` on CL CSV `Custom Label` (case-sensitive; locked 2026-10-27) |
| CL CSV | `database/shared/custom_label/Custom_Label_Database.csv` |
| BTC Product Data | `database/shared/btc_product_data/BTC_Product_Data.csv` (single) |
| Uneek Product Data | `database/shared/uneek_product_data/Uneek_Product_Data.xlsx` (single) |
| Absolute Product Data | `database/shared/absolute_product_data/Absolute_Product_Data.xlsx` (single). Warehouse buys **babysuits only** (styles C800T / C8020T / C8030T) |
| Plain Database | `database/shared/plain/Plain Database.csv` (single; grouping + PO + packing plain) |
| Packs Database | `database/shared/packs/Packs Database.csv` (single; grouping + PO) |
| ShipStation Tags | `database/shared/shipstation_tags/ShipStation_Tags.xlsx` (single) |
| Taxonomy pick-lists | `database/order-grouping-sorter/taxonomy_picklists.csv` (Hashim #038 closed Areeb category / product type / product style / department + PE subcategory). Title Case; type has no gender; style is a named product, never a code. Source `shared/taxonomy_catalog.py`. CL filled 2026-09-16; Plain / Packs stay supplier copy. |
| Areeb column dropdowns | `database/order-grouping-sorter/areeb_column_dropdowns.csv` — `Column,Value` lists for Areeb category / product type / product style / department. Path helper `shared.paths.sorter_areeb_column_dropdowns_path`. Not read on a grouping run. |
| Fixed batches | `database/order-grouping-sorter/fixed_batches.csv` — `B80`/`B100`/… codes + match criteria. Sorter loads via `Order Grouping Sorter/scripts/fixed_batches.py`. Leftover `B1`/`B2`/… skip these numbers. |
| DTF Des-P\*.xlsx | Packing → `Output/Order Packing List Generator/` (+ SharedInbox when Make design queues on); Queue Design Queues |
| Skip Batches | Queue Configuration Workbook sheet — batch digits that skip Design Queues PNGs |
| Print sizes (Queue) | CL CSV Width/Height mm; Pocket overrides in Queue Configuration Workbook |
| New SKU Database | Packing DTF Des Item-SKU remap (`database/order-packing-list-generator/`) |
| NocoDB | Custom Label Database scripts only |
| ShipStation | Packing, PO, Shipping, Sorter via `shared/shipstation` (create/void local to Shipping) |
| Order Grouping Sorter → Packing Input | One CSV per process into Packing `Input/{DD-MM-YYYY}/{nth} Shift/` (`shared.paths.sorter_input_csv_path`). Fixed-batch files are `B100-{6 fields}.csv` / `B80-{6 fields}.csv` / … ; leftover `B1-{6 fields}.csv` / `B2-…` (skip reserved). Default CLI is dry-run; `--run` writes. Nth `--run` of the day = nth shift (locked 2026-10-14). 3rd shift and later write overdue, blank, and the run-day ship-by, plus tag `1004- Personalised Design-Ready-` when ship-by is later (locked 2026-10-22). A later ship-by without that tag stays out. `RESEND` / `UNMATCHED` land in that run’s folder. Chat **run the group sorter** does not seed the catalog and does not skip an order still in `awaiting_shipment` because an earlier shift CSV has it (catalog step removed 2026-10-20). |

**Later (not built):** Shipping auto-ingest from SharedInbox. Packing owns **all** packing list PDFs (including today’s PO slips). Packing enrich/preflight uses Custom Label, then Plain, then Packs (do not clone those SKUs into CL). PO is EDI/stock only.

## System do-nots

- Do not apply one app’s fill/print/NocoDB/ShipStation rules to another app.
- Do not invent joins or sync steps beyond what is proven above.
- Do not put live DB files back inside app code folders — use `database/`.
- Do not put secrets inside `database/`.
- Do not change live databases, CSVs, or Output unless the supervisor already approved.
- Do not paste API keys or secrets into docs or chat.

## Approval

No production writes / void / print batches / fills unless the supervisor already said **yes / do it / fill / run**. Exception: Queue SharedInbox Design Queues watcher (no approval by design). Propose and dry-run first when that is the app’s practice.

## Adding a new app

1. First-level folder with the exact official name  
2. `AppName/AGENTS.md` (capped handbook) + living docs under `docs/<app-slug>/`  

3. `.cursor/rules/<app-slug>/*.mdc` — start with 2–4 rules, `alwaysApply: false`, `globs: "Exact App Folder Name/**"`; cross-app / always-on goes in `.cursor/rules/global/` (see [`.cursor/rules/README.md`](.cursor/rules/README.md))  
4. One short section in this file  
5. Wire paths through `shared/paths.py` — DB under `database/<slug>/`; shared joins under `database/shared/`; secrets under `config/ShipStation/`
