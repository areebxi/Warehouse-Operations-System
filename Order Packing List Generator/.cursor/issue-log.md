# Issue Log

Issues discussed with the AI agent, newest first.

## 2026-10-05 18:43

**Issue:** Batch PDF phase crashed after `Step 8/8: Done.` with `name 'lc' is not defined` when PDF copy directory was set.

**Resolution:** `run_pdf_only_phase` used `lc` without receiving it; pass `lc=ctx["lc"]` from `runner_impl1` (same as excel/full finish paths).

## 2026-10-04 10:43

**Issue:** Packing pipeline crashed with a chain of NameErrors after an imported façade→impl split (`_emit`, `_FONT_METRICS_CACHE`, `_pdf_asset_log_line`, then `Path`).

**Resolution:** Step 5 imports helpers from `service_assign`; font metrics cache lives in `draw_text_impl`; apparel/logo façade rewired to clean `logo_rows`/`logo_cell`/`apparel_square`/`image_primitives`/`back_layout`; `reporting_format` imports `Path`; also wired orphans in `orders_to_csv_impl` and missing-run `core_impl`.

## 2026-10-04 09:12

**Issue:** Packing List, Preflight, and Missing Run GUIs failed to start (`pipeline_*` / `shared` ModuleNotFoundError; Preflight then crashed on config load).

**Resolution:** Entry points add `scripts/` (and warehouse for Missing) to `sys.path`. Restored missing `self` on `PreflightConfigMixin._parse_saved_input_files`.

## 2026-09-25 14:40

**Issue:** Output folders and `missing_logo_orders_*.csv` still used the full sorter stem after PIN/Excel/PDF were shortened to `B#-S#`.

**Resolution:** Pipeline `token` is now `pin_batch_shift(input stem)` — Output/`{B#-S#}/` and `missing_logo_orders_{B#-S#}.csv` match.

## 2026-09-25 13:40

**Issue:** Long sorter input stems (`B1-S1-PLAIN-2-SUPPLY ON DEMAND-R-9`) broke PDF naming/display; Excel was fine.

**Resolution:** Packing visible process base is batch+shift only (`B1-S1`) via `pin_batch_shift` — Step 5 fixed, Step 6/7/8 stems, PIN, preflight. (Folders/missing-logo names shortened in the follow-up fix same day.)

## 2026-09-17 14:04

**Issue:** Missing logos were stripped **after** Step 6 process/item naming, so packing lists kept PIN gaps (e.g. Item-12 then process `-7`, no `-6`).

**Resolution:** Filter runs after Step 5, before Step 6. Lookup still expands quantity and applies custom `base` / `base-1` stems; keepers stay unexpanded so Step 6 names remaining rows with no holes. Missing-logo CSV is the expanded excluded units for reprint.

## 2026-09-15 08:19

**Issue:** Packing Step 6 crashed with `name '_normalize_key' is not defined` after reading the Step 5 CSV.

**Resolution:** Restored the missing `_normalize_key` import from `.common` in `scripts/pipeline_split_by_process_item/service.py`.

## 2026-09-14 14:46

**Issue:** Leftover Graph process filenames were longer than Windows MAX_PATH, so Packing skipped Step 1. Process Number Tracker still ran for non-numeric names.

**Resolution:** Sorter on-disk names are six fields (`PRINTED-1-WAREHOUSE STOCK-P-S1-1`); named families prefix the first-shift number (`80-…`). Packing no longer writes Process Number Tracker; PIN/PDF is `Process {filename}-{N} Item-{item}` and the parser allows spaces in the name.

## 2026-08-09 10:38

**Issue:** Packing List process field label said "Fixed process number" instead of matching Preflight's "Process number".

**Resolution:** Renamed the label to "Process number:" in `scripts/pipeline_packing_list_app/ui.py`.

## 2026-08-07 05:45

**Issue:** Packing List GUI field order differed from Preflight; fixed process number was near the bottom instead of below Shift.

**Resolution:** Reordered fields in `scripts/pipeline_packing_list_app/ui.py` to match Preflight (Date → Shift → fixed process → Input CSV → Workbook → Output → folders), keeping Packing-only options after the shared path block.
