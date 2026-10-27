# Project state (built today)

Cross-app snapshot. Per-app detail: `docs/<slug>/HANDOFF.md` (index: [`README.md`](README.md)). Architecture / line-limit façades: [`ARCHITECTURE.md`](ARCHITECTURE.md). Decision owners: [`DECISIONS.md`](DECISIONS.md). Proof pointers are code/docs that show the claim.

## Apps

| App | How it runs | Gate | Proof |
|-----|-------------|------|-------|
| Custom Label Database | CLI scripts under `scripts/` (fill, NocoDB, sync); live CSV refresh `scripts/cl_db_exporter.py` | `--dry-run` opt-in; live writes need **fill** / **yes**; exporter needs **run** / **yes** | `Custom Label Database/AGENTS.md`; `shared/cl_columns.py` (NocoDB headers) |
| Order Grouping Sorter | CLI `scripts/run_sorter.py` | Default dry-run; `--run` writes | `run_sorter.py` |
| Order Packing List Generator | GUI `packing_list_app.py` + `pipeline_runner` | Policy **yes** / **run** | `pipeline_packing_list_app/app.py` |
| Production Design Queue Manager | GUI `queue_app.py`; headless Design Queues watcher | GUI needs approval; watcher does not | `queue_app.py`; `scripts/design_queues_watcher.py` |
| Shipping Label Generator | CLI (`convert` / `print` / `sample-print` / `void`) | Policy on print/void; sample-print is local only | `scripts/app/main.py`; `shipping_system.py` |
| Purchase Order Generator | GUI `Run_GUI.bat` → `run_script_gui.py` (+ CLI helpers) | Policy | `run_script_gui.py`; slips `pdf_generator.py` |

## Live handoffs

1. **Sorter → Packing Input** — on `--run`, CSVs to `Order Packing List Generator/Input/{DD-MM-YYYY}/{nth} Shift/` (`shared.paths` sorter helper). `SHIFT_PER_RUN = True`: nth `--run` of the day = nth shift (`grouping_models.py`, `run_sorter.py`). 3rd shift and later write overdue, blank, and the run-day ship-by, plus tag `1004- Personalised Design-Ready-` when ship-by is later (locked 2026-10-22). A later ship-by without that tag stays out. Chat **run the group sorter** is that `--run` on current `awaiting_shipment` only: no catalog seed, and still-awaiting orders are not skipped for an earlier shift CSV (`run_sorter.py`; locked 2026-10-14, catalog step removed 2026-10-20). **add unmatched** is `seed_catalog_misses.py` alone. Filename `{B}-S{n}-…` / `RESEND` / `UNMATCHED`; columns = sorter `CSV_FIELDNAMES` (same as Packing `orders_to_csv.py`).
2. **Packing → SharedInbox** — When Make design queues is on, Step 7 writes `DTF Des-P{base}.xlsx` to Output. After that input’s PDFs, Packing copies it to `runtime/SharedInbox/DTF Des/{date}/{shift}/` (`run_design_queues_step.py` + `copy_dtf_des_to_shared_inbox`).
3. **SharedInbox → Queue** — Packing invokes `design_queues_watcher.py --files` after that file’s PDFs. The next packing input can run while one queue job is in progress. Continuous watcher also polls (`shared/design_queues_watcher.py`). Skip Batches skips listed batch digits. Headless PNG also copies to DTF Queues folder when set. Moves to `Processed/` or `Failed/`. No approval.
4. **Shipping** — manual from app `DTF Des Files/` only. Does **not** read SharedInbox.

## Testing-mode facts

- Sorter: nth `--run` of the day = nth shift (`SHIFT_PER_RUN = True`, locked 2026-10-14). 3rd shift and later write overdue, blank, and the run-day ship-by, plus tag `1004- Personalised Design-Ready-` when ship-by is later (locked 2026-10-22). A later ship-by without that tag stays out. Chat **run the group sorter** does not seed the catalog and does not skip still-awaiting orders already written to an earlier shift CSV (2026-10-20).
- Queue Design Queues watcher is the standing approval exception (see parent `AGENTS.md` / `ARCHITECTURE.md`).

## Not built (do not implement until asked)

| Item | Proof it is still not built |
|------|----------------------------|
| Shipping auto-ingest SharedInbox | Shipping convert uses `DTF Des Files`; no SharedInbox refs in Shipping `.py` |
| Packing enrich/preflight Plain + Packs | Enrich is CL-only (`pipeline_cl_lookup` / `enrich_cl_apply.py`) |
| Packing owns all packing-list PDFs (incl. PO slips) | PO still calls `generate_packing_slips_for_tag` |
| PO EDI/stock only | EDI exists **and** slips still run (`run_script_stock_phase.py`) |

## Exceptions / size

Legacy 200-line overs cleared; façade patterns: [`ARCHITECTURE.md`](ARCHITECTURE.md) § Legacy size inventory. Checker: `python scripts/check_line_limit.py`.

## UNKNOWN

- Sorter [`order-grouping-sorter/HANDOFF.md`](order-grouping-sorter/HANDOFF.md) says last Input write **2026-09-30**; Packing `Input/02-10-2026/1st Shift/` also exists on disk — which date is current “last write” is not settled in docs (do not guess).
