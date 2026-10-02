# Decisions — owner map

Where locked decisions live. **Do not copy** locks here; link to the owner. Chat is never authoritative (see `.cursor/rules/global/session-independence.mdc`). Rules map: [`.cursor/rules/README.md`](../.cursor/rules/README.md).

## Owners by area

| Area | Owner |
|------|--------|
| Grouping locks + standing terms | [`order-grouping-locks.md`](../order-grouping-locks.md); `.cursor/rules/order-grouping-sorter/standing-terms.mdc` |
| Grouping lock persist hook (chat) | `.cursor/rules/global/supervisor-chat.mdc` (always-on: write locks + progress xlsx same turn) |
| Sorter app policy / live paths | `.cursor/rules/order-grouping-sorter/` |
| Custom Label policy / fills | `.cursor/rules/custom-label-database/` |
| Packing policy | `.cursor/rules/order-packing-list-generator/` |
| Queue policy | `.cursor/rules/production-design-queue-manager/` |
| Shipping policy | `.cursor/rules/shipping-label-generator/` |
| Purchase Order policy | `.cursor/rules/purchase-order-generator/` |
| Proven joins + approval + pipeline map | Parent [`AGENTS.md`](../AGENTS.md) |
| Architecture (200-line, layers, boundaries) | `.cursor/rules/global/architecture.mdc`; [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| SharedInbox handoff | `.cursor/rules/global/shared-inbox.mdc` |
| ShipStation shared client | `.cursor/rules/global/shipstation.mdc`; `shared/shipstation/`; secrets `config/ShipStation/` |
| SKU match | `.cursor/rules/global/cl-sku-match.mdc`; `shared/cl_sku_match.py` |
| Supply Method | `.cursor/rules/custom-label-database/supply-method.mdc`; `shared/supply_method.py` |
| Printing Type | `.cursor/rules/custom-label-database/printing-type.mdc`; `shared/printing_type.py` |
| Supplier Name | `.cursor/rules/custom-label-database/supplier-name.mdc`; `shared/supplier_name.py` |
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
- Grouping glossary / history: `standing-terms.mdc` ↔ `order-grouping-locks.md` (glossary vs decision log — both intentional; do not merge).

## Cross-app architecture locks with no other owner

None added. Existing cross-app locks already sit under `AGENTS.md`, `ARCHITECTURE.md`, `global/shared-inbox.mdc`, or `global/session-independence.mdc`.
