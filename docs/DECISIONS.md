# Decisions — owner map

Where locked decisions live. **Do not copy** locks here; link to the owner. Chat is never authoritative (see `.cursor/rules/global/session-independence.mdc`). Rules map: [`.cursor/rules/README.md`](../.cursor/rules/README.md).

## Owners by area

| Area | Owner |
|------|--------|
| Grouping locks + standing terms | [`Order Grouping Sorter/order-grouping-locks.md`](../Order%20Grouping%20Sorter/order-grouping-locks.md); `.cursor/rules/order-grouping-sorter/standing-terms.mdc` |
| Grouping lock persist hook (chat) | `.cursor/rules/global/supervisor-chat.mdc` (always-on: write locks + progress xlsx same turn) |
| Sorter app policy / live paths | `.cursor/rules/order-grouping-sorter/` |
| Custom Label policy / fills | `.cursor/rules/custom-label-database/` |
| Packing policy | `.cursor/rules/order-packing-list-generator/` |
| Queue policy | `.cursor/rules/production-design-queue-manager/` |
| Shipping policy | `.cursor/rules/shipping-label-generator/` (reprint + Batch Summary locked 2026-10-20 in `reprint.mdc`) |
| Purchase Order policy | `.cursor/rules/purchase-order-generator/` |
| Proven joins + approval + pipeline map | Parent [`AGENTS.md`](../AGENTS.md) |
| Architecture (200-line, layers, boundaries) | `.cursor/rules/global/architecture.mdc`; [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| SharedInbox handoff | `.cursor/rules/global/shared-inbox.mdc` |
| ShipStation shared client | `.cursor/rules/global/shipstation.mdc`; `shared/shipstation/`; secrets `config/ShipStation/` |
| SKU match | `.cursor/rules/global/cl-sku-match.mdc`; `shared/cl_sku_match.py` (case-sensitive entire-cell; locked 2026-10-27) |
| Live CL CSV column names (NocoDB) | `shared/cl_columns.py`; `.cursor/rules/custom-label-database/nocodb.mdc` + `live-files.mdc` (locked 2026-10-04: underscored headers; `BTC SKU`→`Supplier_SKU`; `Supply Method`→`Stock_Type`) |
| Supply Method | `.cursor/rules/custom-label-database/supply-method.mdc`; `shared/supply_method.py` |
| Printing Type | `.cursor/rules/custom-label-database/printing-type.mdc`; `shared/printing_type.py` |
| Print sizes (hoodies, sleeve, ISO A3–A6, F/P-F8, B4) | `.cursor/rules/custom-label-database/print-sizes.mdc` (hoodies 2026-10-22; sleeve 100×100 + F/P-F8/B4 on Areeb 2026-10-23; ISO paper A3–A6 Front/Back Center on Areeb 2026-10-27) |
| Areeb Custom Label dedupe keep-rule | `.cursor/rules/custom-label-database/duplicates.mdc` (locked 2026-10-27: token match → long supplier GA → fill count → first; `scripts/dedupe_areeb_cl.py`) |
| Supplier Name | `.cursor/rules/custom-label-database/supplier-name.mdc`; `shared/supplier_name.py` |
| UID vs product file | `.cursor/rules/custom-label-database/fill-pipeline.mdc` (locked 2026-10-23: colour, garment, image, and product code come from the product file for that UID, not a peer clone) |
| Taxonomy pick-list | `.cursor/rules/order-grouping-sorter/taxonomy-picklist.mdc`; `shared/taxonomy_*.py`; `database/order-grouping-sorter/taxonomy_picklists.csv` |
| Fixed batches criteria | `database/order-grouping-sorter/fixed_batches.csv` (+ locks / sorter rules) |
| Session truth / verify / persist | `.cursor/rules/global/session-independence.mdc` |
| Docs-first read + same-turn doc sync | `.cursor/rules/global/docs-first.mdc` |
| Built state (cross-app) | [`PROJECT_STATE.md`](PROJECT_STATE.md); per-app `docs/HANDOFF.md` |
| Packing / Queue resolved bugs | `Order Packing List Generator/.cursor/issue-log.md`; `Production Design Queue Manager/.cursor/issue-log.md` |
| Requirement gate before implement | `.cursor/rules/global/requirement-understanding.mdc` |
| YAGNI / reuse ladder | `.cursor/rules/global/ponytail.mdc` |
| Advise best path | `.cursor/rules/global/best-advice-first.mdc` |
| App routing stub | `.cursor/rules/global/warehouse-system-map.mdc` |
| Rule place + LLM-clear writing | `.cursor/rules/global/rule-writing.mdc`; [`.cursor/rules/README.md`](../.cursor/rules/README.md) |

## Handoff contracts

No `docs/contracts/` — shapes already owned elsewhere:

- Sorter → Packing CSV: filename / path in `.cursor/rules/order-grouping-sorter/live-files.mdc` + standing terms; columns = `CSV_FIELDNAMES` in `Order Grouping Sorter/scripts/grouping_models.py` (matches Packing `orders_to_csv.py`).
- Packing → SharedInbox `DTF Des-P*.xlsx`: `.cursor/rules/global/shared-inbox.mdc`; columns in `Order Packing List Generator/docs/scripts/generate_excel_outputs.md` + `writers_impl.py`.

## Duplicate homes (report only — do not merge yet)

- Parent `AGENTS.md` ↔ `global/warehouse-system-map.mdc`: map is the **always-on router stub**; `AGENTS.md` holds layout / pipeline / joins / apps (slimmed 2026-10-02 — do not re-expand the map).
- Parent `AGENTS.md` ↔ `docs/ARCHITECTURE.md` (pipeline, not-built, approval).
- Grouping glossary / history: `standing-terms.mdc` ↔ `Order Grouping Sorter/order-grouping-locks.md` (glossary vs decision log — both intentional; do not merge).

## Cross-app architecture locks with no other owner

- **2026-10-04 — Live CL CSV is NocoDB underscored.** Readers use `shared/cl_columns.py`. No exporter header remap. Stand-ins: `BTC SKU`→`Supplier_SKU`, `Supply Method`→`Stock_Type` with `normalize_stock_type` (Order on Demand→Supplier On Demand; Seasonal/Non-Seasonal→Warehouse Stock; blank stays blank). Owner: `.cursor/rules/custom-label-database/nocodb.mdc` + `supply-method.mdc` + `Custom Label Database/docs/HANDOFF.md`.
- **2026-10-27 — CL SKU match is case-sensitive.** Entire-cell Custom Label join no longer casefolds. Owner: `.cursor/rules/global/cl-sku-match.mdc`; `shared/cl_sku_match.py`. Sorter CL finish keys use the same case rule (stricter key order unchanged).
