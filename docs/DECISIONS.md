# Decisions — owner map

Where locked decisions live. **Do not copy** locks here; link to the owner. Chat is never authoritative (see `.cursor/rules/global/session-independence.mdc`). Rules map: [`.cursor/rules/README.md`](../.cursor/rules/README.md).

## Owners by area

| Area | Owner |
|------|--------|
| Grouping locks + standing terms | [`docs/order-grouping-sorter/order-grouping-locks.md`](order-grouping-sorter/order-grouping-locks.md); `.cursor/rules/order-grouping-sorter/standing-terms.mdc` |
| Grouping lock persist hook (chat) | `.cursor/rules/global/supervisor-chat.mdc` (always-on: write locks same turn) |
| Sorter app policy / live paths | `.cursor/rules/order-grouping-sorter/` (2026-10-28: no `Manually Made Files` / `Missed Orders` / `Today's Manually Made Files` under the sorter app; `Netural Database/` at warehouse root) |
| Custom Label policy / fills | `.cursor/rules/custom-label-database/` |
| Packing policy | `.cursor/rules/order-packing-list-generator/` |
| Packing operator I/O folders | Locked 2026-10-29: `Input/`, `Missing Logos/`, `Missing Apparels/`, `Unmatched SKUs/`, `Preflight Issues/` under the Packing app (via `shared.paths.packing_*`). Not warehouse `Output/`. Each tracks only `README.md`; runtime CSVs gitignored. Owner: `live-files.mdc` + `missing-logo-before-naming.mdc` |
| Queue policy | `.cursor/rules/production-design-queue-manager/` |
| Shipping policy | `.cursor/rules/shipping-label-generator/` (reprint + Batch Summary locked 2026-10-20 in `reprint.mdc`) |
| Shipping Configuration Workbook | Locked 2026-10-29: `database/shipping-label-generator/Configuration Workbook.xlsx` via `shared.paths.shipping_config_workbook_path` (Label Page Threshold only; not Queue’s workbook) |
| Shipping app tuneables YAML | Locked 2026-10-29: `Shipping Label Generator/config/shipping_config.yaml` via `shared.paths.shipping_yaml_path` (app config, not database) |
| Shipping Reports / failures paths | Locked 2026-10-29: `Output/Shipping Label Generator/Reports/`; `Logs/Shipping Label Generator/Error and Failures/` — not under the Shipping app folder |
| Purchase Order policy | `.cursor/rules/purchase-order-generator/` |
| Shared brand logos | Locked 2026-10-29: `database/shared/brand_logos/` via `shared.paths.shared_brand_logos_dir` (PO packing slips now; Packing later when it owns all packing-list PDFs). App-local PO `assets/fonts` removed. Owner: `live-files.mdc` + `database/README.md` |
| Proven joins + approval + pipeline map | Parent [`AGENTS.md`](../AGENTS.md) |
| Architecture (200-line, layers, boundaries) | `.cursor/rules/global/architecture.mdc`; [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| SharedInbox handoff | `.cursor/rules/global/shared-inbox.mdc` |
| ShipStation shared client | `.cursor/rules/global/shipstation.mdc`; `shared/shipstation/`; secrets `config/ShipStation/` |
| Single warehouse `.env` | Locked 2026-10-28: only `config/ShipStation/.env` (template `config/ShipStation/.env.example`). No app-local `.env` / `.env.example` under Shipping or elsewhere. One root `.gitignore` only (no nested app `.gitignore`). |
| SKU match | `.cursor/rules/global/cl-sku-match.mdc`; `shared/cl_sku_match.py` (case-sensitive entire-cell; locked 2026-10-27) |
| Live CL CSV column names (NocoDB) | `shared/cl_columns.py`; `.cursor/rules/custom-label-database/nocodb.mdc` + `live-files.mdc` (locked 2026-10-04: underscored headers; `BTC SKU`→`Supplier_SKU`; `Supply Method`→`Stock_Type`) |
| Supply Method | `.cursor/rules/custom-label-database/supply-method.mdc`; `shared/supply_method.py` |
| Printing Type | `.cursor/rules/custom-label-database/printing-type.mdc`; `shared/printing_type.py` |
| Print sizes (hoodies, sleeve, ISO A3–A6, F/P-F8, B4) | `.cursor/rules/custom-label-database/print-sizes.mdc` (hoodies 2026-10-22; sleeve 100×100 + F/P-F8/B4 on Areeb 2026-10-23; ISO paper A3–A6 Front/Back Center on Areeb 2026-10-27; no-pos-token → Front Center + `A3-B-M-T-*` → Back Center on Areeb 2026-10-28) |
| Mock Print Positions always from Mocks DB | `.cursor/rules/custom-label-database/fill-pipeline.mdc` + `print-sizes.mdc` (locked 2026-10-29: `M{digits}…` → Mocks `Printing Position` via `PRINT_POS_MAP`; never peer-clone; never default mock PP to Front Center; repair `scripts/fix_areeb_mock_pos_from_mocks.py`) |
| Areeb Custom Label dedupe keep-rule | `.cursor/rules/custom-label-database/duplicates.mdc` (locked 2026-10-27: token match → long supplier GA → fill count → first; `scripts/dedupe_areeb_cl.py`) |
| Database Transfer retired | Removed 2026-10-27: no `Database Transfer/` folder, no fill sync, no `sync_database_transfer.py`. Live = CSVs under `database/` only ([`custom-label-database/HANDOFF.md`](custom-label-database/HANDOFF.md)). Local leftover `Old Workbooks/` (retired Excel mirrors) removed 2026-10-28 — not part of the live tree |
| Living docs home | Locked 2026-10-27: all living app docs under root `docs/<app-slug>/`; `AGENTS.md` stays in each app folder; archives in `backups/docs/`; policy in `.cursor/rules/` ([`README.md`](README.md)) |
| Root Logs/ and Output/ | Locked 2026-10-28: all app run logs under `Logs/<App Name>/`; all run outputs under `Output/<App Name>/` via `shared.paths` (`logs_root` / `output_root`). Input and similar stay in app folders. Owner: parent [`AGENTS.md`](../AGENTS.md) + each app `live-files.mdc` / HANDOFF |
| Demo Images Database/ | Removed from warehouse tree 2026-10-28 (placeholders live outside the project). Demo-mode helpers (`shared.demo_images` / `shared.paths.demo_images_*`) stay; they resolve when that folder exists again. Note: [`database/README.md`](../database/README.md) |
| Supplier Name | `.cursor/rules/custom-label-database/supplier-name.mdc`; `shared/supplier_name.py` |
| UID vs product file | `.cursor/rules/custom-label-database/fill-pipeline.mdc` (locked 2026-10-23: colour, garment, image, and product code come from the product file for that UID, not a peer clone) |
| Taxonomy pick-list | `.cursor/rules/order-grouping-sorter/taxonomy-picklist.mdc`; `shared/taxonomy_*.py`; `database/order-grouping-sorter/taxonomy_picklists.csv` |
| Fixed batches criteria | `database/order-grouping-sorter/fixed_batches.csv` (+ locks / sorter rules) |
| Session truth / verify / persist | `.cursor/rules/global/session-independence.mdc` |
| Docs-first read + same-turn doc sync | `.cursor/rules/global/docs-first.mdc` |
| Built state (cross-app) | [`PROJECT_STATE.md`](PROJECT_STATE.md); per-app `docs/<slug>/HANDOFF.md` |
| Packing / Queue resolved bugs | `Order Packing List Generator/.cursor/issue-log.md`; `Production Design Queue Manager/.cursor/issue-log.md` |
| Requirement gate before implement | `.cursor/rules/global/requirement-understanding.mdc` |
| YAGNI / reuse ladder | `.cursor/rules/global/ponytail.mdc` |
| Advise best path | `.cursor/rules/global/best-advice-first.mdc` |
| App routing stub | `.cursor/rules/global/warehouse-system-map.mdc` |
| Rule place + LLM-clear writing | `.cursor/rules/global/rule-writing.mdc`; [`.cursor/rules/README.md`](../.cursor/rules/README.md) |

## Handoff contracts

No `docs/contracts/` — shapes already owned elsewhere:

- Sorter → Packing CSV: filename / path in `.cursor/rules/order-grouping-sorter/live-files.mdc` + standing terms; columns = `CSV_FIELDNAMES` in `Order Grouping Sorter/scripts/grouping_models.py` (matches Packing `orders_to_csv.py`).
- Packing → SharedInbox `DTF Des-P*.xlsx`: `.cursor/rules/global/shared-inbox.mdc`; columns in [`order-packing-list-generator/scripts/generate_excel_outputs.md`](order-packing-list-generator/scripts/generate_excel_outputs.md) + `writers_impl.py`.

## Duplicate homes (report only — do not merge yet)

- Parent `AGENTS.md` ↔ `global/warehouse-system-map.mdc`: map is the **always-on router stub**; `AGENTS.md` holds layout / pipeline / joins / apps (slimmed 2026-10-02 — do not re-expand the map).
- Parent `AGENTS.md` ↔ `docs/ARCHITECTURE.md` (pipeline, not-built, approval).
- Grouping glossary / history: `standing-terms.mdc` ↔ `docs/order-grouping-sorter/order-grouping-locks.md` (glossary vs decision log — both intentional; do not merge).

## Cross-app architecture locks with no other owner

- **2026-10-04 — Live CL CSV is NocoDB underscored.** Readers use `shared/cl_columns.py`. No exporter header remap. Stand-ins: `BTC SKU`→`Supplier_SKU`, `Supply Method`→`Stock_Type` with `normalize_stock_type` (Order on Demand→Supplier On Demand; Seasonal/Non-Seasonal→Warehouse Stock; blank stays blank). Owner: `.cursor/rules/custom-label-database/nocodb.mdc` + `supply-method.mdc` + [`custom-label-database/HANDOFF.md`](custom-label-database/HANDOFF.md).
- **2026-10-27 — CL SKU match is case-sensitive.** Entire-cell Custom Label join no longer casefolds. Owner: `.cursor/rules/global/cl-sku-match.mdc`; `shared/cl_sku_match.py`. Sorter CL finish keys use the same case rule (stricter key order unchanged).
- **2026-10-27 — Living docs under root `docs/<app-slug>/`.** App `AGENTS.md` stays in the app folder. Archives stay in `backups/docs/`. Owner: [`README.md`](README.md).
