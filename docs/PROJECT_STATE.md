# Project state (built today)

Cross-app snapshot. Per-app detail: each app’s `docs/HANDOFF.md`. Architecture / line-limit façades: [`ARCHITECTURE.md`](ARCHITECTURE.md). Decision owners: [`DECISIONS.md`](DECISIONS.md). Proof pointers are code/docs that show the claim.

## Apps

| App | How it runs | Gate | Proof |
|-----|-------------|------|-------|
| Custom Label Database | CLI scripts under `scripts/` (fill, NocoDB, sync) | `--dry-run` opt-in; live writes need **fill** / **yes** | `Custom Label Database/AGENTS.md`; e.g. `scripts/fill_from_seeds.py` |
| Order Grouping Sorter | CLI `scripts/run_sorter.py` | Default dry-run; `--run` writes | `run_sorter.py` |
| Order Packing List Generator | GUI `packing_list_app.py` + `pipeline_runner` | Policy **yes** / **run** | `pipeline_packing_list_app/app.py` |
| Production Design Queue Manager | GUI `queue_app.py`; headless Missing Logo watcher | GUI needs approval; watcher does not | `queue_app.py`; `scripts/auto_missing_logo_watcher.py` |
| Shipping Label Generator | CLI (`convert` / `print` / `void`) | Policy on print/void | `scripts/app/main.py`; `shipping_system.py` |
| Purchase Order Generator | GUI `Run_GUI.bat` → `run_script_gui.py` (+ CLI helpers) | Policy | `run_script_gui.py`; slips `pdf_generator.py` |

## Live handoffs

1. **Sorter → Packing Input** — on `--run`, CSVs to `Order Packing List Generator/Input/{DD-MM-YYYY}/1st Shift/` (`shared.paths` sorter helper). Testing: `SHIFT_PER_RUN = False` → every write is **1st Shift** (`Order Grouping Sorter/scripts/grouping_models.py`, `run_sorter.py`). Filename `{B}-S{n}-…` / `RESEND` / `UNMATCHED`; columns = sorter `CSV_FIELDNAMES` (same as Packing `orders_to_csv.py`).
2. **Packing → SharedInbox** — Step 7 writes `DTF Des-P{base}.xlsx` to Output and copies to `runtime/SharedInbox/DTF Des/{date}/{shift}/` (`pipeline_generate_excel_outputs/service.py` + `copy_dtf_des_to_shared_inbox`).
3. **SharedInbox → Queue** — Missing Logo auto-watcher (`shared/missing_logo_watcher.py`; Packing GUI ensures it on launch). Moves to `Processed/` or `Failed/`. No approval.
4. **Shipping** — manual from app `DTF Des Files/` only. Does **not** read SharedInbox.

## Testing-mode facts

- Sorter: every `--run` rewrites Packing `1st Shift` (`SHIFT_PER_RUN = False`). Production later: nth `--run` of the day = nth shift.
- Queue Missing Logo watcher is the standing approval exception (see parent `AGENTS.md` / `ARCHITECTURE.md`).

## Not built (do not implement until asked)

| Item | Proof it is still not built |
|------|----------------------------|
| Shipping auto-ingest SharedInbox | Shipping convert uses `DTF Des Files`; no SharedInbox refs in Shipping `.py` |
| Packing enrich/preflight Plain + Packs | Enrich is CL-only (`pipeline_cl_lookup` / `enrich_cl_apply.py`) |
| Packing owns all packing-list PDFs (incl. PO slips) | PO still calls `generate_packing_slips_for_tag` |
| PO EDI/stock only | EDI exists **and** slips still run (`run_script_stock_phase.py`) |
| Sorter `SHIFT_PER_RUN` production rotation | Flag false in `grouping_models.py` |

## Exceptions / size

Legacy 200-line overs cleared; façade patterns: [`ARCHITECTURE.md`](ARCHITECTURE.md) § Legacy size inventory. Checker: `python scripts/check_line_limit.py`.

## UNKNOWN

- Sorter `docs/HANDOFF.md` says last Input write **2026-09-30**; Packing `Input/02-10-2026/1st Shift/` also exists on disk — which date is current “last write” is not settled in docs (do not guess).
