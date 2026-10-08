# Queue App — Issue Resolution Log

Newest entries first. Maintained automatically per `.cursor/rules/issue-resolution-log.mdc`.

---

### 2026-10-06 17:37 UTC+1
**Issue:** Queue Run on `DTF Des-P300` showed “Processed … successfully” but loaded zero designs.
**Resolution:** Live CL CSV still had Areeb-era spaced headers (`Custom Label`, `Width 1 (mm)`, …) while Queue expected NocoDB names; `ValueError` aborted load and empty result was counted as success. `shared/cl_columns.rename_legacy_headers` + Queue `load_cl_size_table` rename before the hard check; Run exceptions re-raise so failures surface.

### 2026-10-05 18:54 UTC+1
**Issue:** SharedInbox watcher name “Missing Logo watcher” was unclear (it builds design queue PNGs from DTF Des).
**Resolution:** Full rename to Design Queues watcher — `design_queues_watcher.py` / `design_queues_{process,loop,inbox}.py`, `run_design_queues_watcher.bat`, `shared/design_queues_watcher.py`. Packing ensure-on-launch and docs/rules updated. Queue GUI Missing Logo mode and Packing missing-logo strip unchanged.

### 2026-10-04 15:56 UTC+1
**Issue:** Auto Missing Logo queue PNGs used date/time stems (`P50_20261004_154350.png`) instead of GUI names.
**Resolution:** `_output_stem` in `auto_missing_logo_process.py` now matches GUI (`P50.png` / `P50_Part N.png`); re-runs overwrite.

### 2026-10-04 15:45 UTC+1
**Issue:** Design queues not auto-made after Packing List SharedInbox dual-write.
**Resolution:** Watcher was failing (empty design folders) or stalling on Drive I/O. With folders set and a fresh watcher, SharedInbox → PNG → Processed works. Keep folders configured in Queue settings.

### 2026-10-04 13:42 UTC+1
**Issue:** GUI had one Run button but backend still kept three mode entry points (Normal / Personalised / Missing Logo) plus dead single-file UI processors.
**Resolution:** Removed dead `arrange_designs` / `arrange_personalised` / `process_folder` / `process_folder_personalised` / UI single-file processors. Keep only Run → `arrange_missing_logo_designs` → `process_folder_missing_logo` (Customise-column routing). Domain `process_single_designs` / `process_personalised_designs` unchanged.

### 2026-10-04 13:29 UTC+1
**Issue:** Multi-file Run looked like only one file arranged/saved (e.g. P50 worked; P1000/P5000 produced nothing).
**Resolution:** Not a multi-file loop bug. IronOn resize passed `apply_max_design_size` into `select_best_orientation`, which no longer accepted that kwarg after the 300×500 split; the TypeError was swallowed in `load_and_resize_design`. Restored the parameter in `image_orientation.py` / `image_orientation_select.py` (matches Working Copy).

### 2026-10-04 13:03 UTC+1
**Issue:** Queue canvas empty, design folders not restoring, progress missing on folder runs, and P100 Missing Logo crashed on Override Print Size SKUs (`NameError: OVERRIDE_MATCH_TYPE`).
**Resolution:** Incomplete façade/impl split: wired packing helpers into `canvas_arranger_impl`, size-match helpers into `size_reference_impl`, lazy-import for folder labels, stop demo/None saves from wiping Drive paths, add per-design progress in folder cores, and use `size_code_override.build_print_size_override_info` (constants live there).

### 2026-10-04 09:41 UTC+1
**Issue:** Queue GUI went “Not Responding” for ~11s on startup.
**Resolution:** Paint UI first, then load CL CSV + Configuration Workbook via `run_keeping_ui_alive` (workbook open alone ~9s). Window stays responsive while data loads.

### 2026-10-04 09:12 UTC+1
**Issue:** Queue GUI failed to start with `NameError: _warehouse_settings_path is not defined`.
**Resolution:** Import `_warehouse_settings_path` from `settings_manager_paths` into `settings_manager_impl.py` after the settings-manager split.

### 2026-09-22 05:33 UTC+1
**Issue:** Duplicate-order SKU search never set pocket/sleeve flags, so 1-SP files like `{order}-{index}-P-{sku}.jpg` next to the main PNG were ignored (legacy `{Order}-P.png` still worked only for unique orders).
**Resolution:** JPEG in 1-SP is a position hint only. Queue the matching PNG at 80×100 (`-P-`, including kids) or 100×100 (`-S-`/`-S1-`/`-S2-`). Do not queue the JPEG. JPEG-only does not invent a design. Token tables in `sku_position_hints.py`; find in `vba_file_search_core.py`; apply in `design_processing_personalised.py`. `IMAGE_EXTENSIONS` stays `['.png']`.

### 2026-09-20 07:37 UTC+1
**Issue:** Queue Missing Logo warned for `128357LG-5000-NAT-S` and `128357LG-5000-LPNK-XL` after CL path was corrected.
**Resolution:** Filled Custom Labels `5000-NAT-S` / `5000-LPNK-XL` (+2, live 132,064). Backup `Custom_Label_Database_preAdd_20260920_073706.csv`. Matcher unchanged. Verify: restart Queue, Missing Logo on `DTF Des-P50.xlsx`.

### 2026-09-20 07:32 UTC+1
**Issue:** After correcting Queue CL path, Missing Logo still warned for 2 designs: `128357LG-5000-NAT-S`, `128357LG-5000-LPNK-XL`.
**Resolution (runtime logs `debug-a28c4d.log`):** Queue matcher is correct. Live CL loaded (132,062 rows). Keys `5000-NAT-S` / `5000-LPNK-XL` are not Custom Label cells. `A3-5000-NAT-S` and `A3-5000-LPNK-XL` exist (cousin in index). No pocket override. Do **not** add an A3- prefix join. Fill those two Custom Labels from the A3-5000 peers.

### 2026-09-20 07:18 UTC+1
**Issue:** Queue Missing Logo on `DTF Des-P50.xlsx` exported “missing size reference” (`DTF Des-P50 (2026-09-20_07-18-02)`). Print sizes already come from Custom Label CSV, not Size References.
**Resolution (diagnosis):** `config/queue_app_settings.json` still had `cl_csv_path` / `config_workbook_path` under `D:\Warehouse Operations System\...` (file not on this PC). Startup log: `Print sizes: CL database not found`. Live catalog is `D:\Areeb Work\Warehouse Operations System\database\shared\custom_label\Custom_Label_Database.csv`. With that file, 3/5 P50 SKUs hit (`M-T-LPNK-L`, `M-T-NEOMT-L`, `M-T-WHI-XL`, 267×378). `128357LG-5000-NAT-S` and `128357LG-5000-LPNK-XL` still miss CL (`5000-NAT-S` / `5000-LPNK-XL` not in Custom Label; A3-5000 cousins exist). Saved path is used even when missing — no fallback to `shared.paths`.

### 2026-08-09 09:41 UTC+1
**Issue:** Size lookup still had legacy J=9/K=10 column-index fallback after the Front Print crash fix.
**Resolution:** Removed `_try_column_index_fallback` and `_row_value_at` from `size_reference.py`; width/height now use named columns only (`Size Width`, `Size Height`, etc.) in `get_size_from_reference` and `multi_position_logic.py`.

### 2026-08-09 09:40 UTC+1
**Issue:** Arrange designs failed with `could not convert string to float: 'Front Print'` (e.g. on `DTF Des-P100.xlsx` / `M96 (17257)`).
**Resolution:** In `scripts/src/core/size_reference.py` `_try_column_index_fallback`, skip obsolete J=9/K=10 fallback when named dim columns exist (index 9 is now `Printing Position`); also guard legacy `float()` against non-numeric cells.

### 2026-08-04 12:27 UTC+1
**Issue:** No standing process to record issues discussed with the agent and how they were fixed.
**Resolution:** Added always-apply rule `.cursor/rules/issue-resolution-log.mdc` and this log file (`.cursor/issue-log.md`). Future issue discussions are appended here with date/time, issue, and resolution.
