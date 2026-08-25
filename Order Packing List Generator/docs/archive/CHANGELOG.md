# Documentation changelog

All notable changes to the project and its documentation are recorded here.

---

## Unreleased

### Fixed (Item Quantity expand: pandas StringDtype / cross-PC Preflight crash)

- **scripts/pipeline_split_by_process_item/grouping_quantity.py** — `_expand_df_by_quantity` now sets expanded **Item Quantity** to the string `"1"` instead of the integer `1`. On pandas builds with strict string columns (`infer_string` / `dtype: str`, common on newer installs), assigning an int raised `Invalid value '1' for dtype 'str'… got 'int' instead` during Preflight step 3 (and the same helper is used by Step 6).
- **Docs:** [split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md), [preflight_issues_app.md](scripts/preflight_issues_app.md), [docs/README.md](README.md).

### Changed (Faster multi-file packing: stem-map cache + Excel-then-PDF)

- **scripts/pipeline_generate_packing_list_pdf/image_lookup.py** — Stem maps built with one-pass `os.scandir` / `os.walk`; in-process memory cache + on-disk cache (`.cache/image_stem_maps/`, or frozen `%LOCALAPPDATA%/PackingListApp/cache/image_stem_maps/`) invalidated by folder `mtime`.
- **scripts/pipeline_runtime/runner.py** — `run_pipeline(..., phases="all"|"excel"|"pdf")`; `discover_step6_csvs` shared helper. Excel phase skips Step 8; PDF phase rediscovers process CSVs and runs Step 8 only.
- **scripts/pipeline_packing_list_app/runner.py** — Multi CSV / multi ShipStation tag: all Excel first, then all PDFs. Single input unchanged (`phases="all"`).
- **Step 8 indexing** — `max_workers=4`; logs index elapsed seconds (cache reuse shows as near-instant).
- **Docs:** [USAGE.md](../USAGE.md), [docs/README.md](README.md), [generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md).
- **Tests:** `tests/test_image_stem_map.py`, `tests/test_pipeline_phases.py`.

### Added (Preflight Issues App)

- **preflight_issues_app.py** / **scripts/pipeline_preflight_issues/** — Replaces the Unmatched SKUs–only helper. Scans one or more ShipStation CSVs through steps 1–4 in memory, then dry-runs logo/apparel image lookup. Flags per row: **Unmatched SKU** (blank Gender Apparel), **Missing Logo**, **Missing Apparel**. Writes only rows with at least one **Yes** to `Preflight Issues_{DD-MM-YYYY}_{HH-MM-SS}.csv`.
- **Config:** `config/preflight_issues_config.json` (reads legacy `unmatched_skus_config.json` if the new file is missing). Default output dir is `Unmatched SKU Files/`; the GUI may override (e.g. `Preflight Issues/`).
- **Launcher:** `run_preflight_issues_app.bat`.
- **Docs:** [USAGE.md](../USAGE.md), [README.md](../README.md), [docs/README.md](README.md), [docs/scripts/preflight_issues_app.md](scripts/preflight_issues_app.md).

### Changed (Step 1: skip Discount Item Name rows)

- **scripts/pipeline_cl_lookup/fetch_input_csv.py** — Rows whose **Item Name** contains `discount` (case-insensitive substring) are skipped and never written to the step-1 CSV. Applies to the main packing pipeline and Preflight Issues (both call `fetch_input_csv`).
- **Docs:** [fetch_input_csv.md](scripts/fetch_input_csv.md), [docs/README.md](README.md).

### Changed (Step 8 / Preflight: plain order via `plain` or `plainlg`)

- **scripts/pipeline_generate_packing_list_pdf/core_helpers.py** — `is_plain_order_sku_impl` treats Item SKU as plain when it contains **`plainlg`** or **`plain`** (case-insensitive). Same helper is used by Preflight missing-logo dry-run so plain rows are not flagged.
- **Docs:** [generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md), [docs/README.md](README.md), [docs/scripts/preflight_issues_app.md](scripts/preflight_issues_app.md).

### Changed (Missing Run: PDF flat copy, Excel under shift)

- **Missing Run App** — PDF copy directory receives files **directly** in the selected folder (no `{Shift} Shift` subfolder). Excel copy directory nests under `{copy_dir}/{Shift} Shift/` (same as Packing List).
- **scripts/pipeline_runtime/runner_utils.py** — `_copy_outputs_to_shift_dirs` takes separate `nest_pdf_under_shift` / `nest_excel_under_shift` flags (replaces single `nest_under_shift`).
- **Docs:** [USAGE.md](../USAGE.md), [docs/README.md](README.md), [docs/scripts/missing_run_app.md](scripts/missing_run_app.md).

### Changed (GUI: shared theme and maximized windows)

- **scripts/gui_theme.py** — Shared ttk theme (clam, slate/teal palette, accent Run buttons, styled log Text and Listbox). Applied once at startup; no pipeline runtime cost.
- **Packing List / Missing Run / Preflight Issues** — All three GUIs use the shared theme, show a short title + subtitle, and open **maximized** (`state("zoomed")` on Windows).
- **Docs:** [USAGE.md](../USAGE.md), [README.md](../README.md), [docs/README.md](README.md), [docs/scripts/missing_run_app.md](scripts/missing_run_app.md).

### Changed (GUI polish: validation, Missing Run copy, Finished copy failures)

- **Packing List App** — Non-empty apparel/logo folder paths must be existing directories before run. **Run missing pipeline** mode requires **Shift** (same as the main pipeline).
- **Missing Run App** — **Shift** is required (label/hint no longer say optional). PDF copy directory receives files **directly** in the selected folder (no `{Shift} Shift` subfolder); Excel copies nest under `{copy_dir}/{Shift} Shift/`. Main Packing List pipeline nests both under `{copy_dir}/{Shift} Shift/`.
- **scripts/pipeline_runtime/runner_utils.py** — `_copy_outputs_to_shift_dirs` supports per-type nest flags and returns failure messages; shared `_FILENAME_UNSAFE` / `_sanitize_process_for_filename`.
- **Finished dialog** — PDF/Excel copy failures are appended to the success report (pipeline still completes).
- **Config save** — Packing List, Missing Run, and Preflight Issues GUIs print config write failures to **stderr** (no dialog).
- **Docs:** [USAGE.md](../USAGE.md), [README.md](../README.md), [docs/README.md](README.md), [docs/scripts/missing_run_app.md](scripts/missing_run_app.md).

### Added (Packing rules: modular Item Quantity correction)

- **scripts/pipeline_packing_rules/** — Config-driven rules applied after Step 1 in the main pipeline. Rules are defined in [`scripts/pipeline_packing_rules/config.py`](../scripts/pipeline_packing_rules/config.py) (`PACKING_RULES`). When **Item SKU** and **Item Name** match a rule, **Item Quantity** is set before Step 6 expansion. Initial rule: `17786LG-DTF-IronOn-A6` + name contains `Set of 5` → qty `5`.
- **scripts/pipeline_runtime/runner.py** — Calls `apply_packing_rules_to_csv` after Step 1; excludes `1b_apply_rules_{token}.csv` from Step 6/7 process CSV glob (audit snapshot only).
- **Tests:** [tests/test_packing_rules.py](../tests/test_packing_rules.py).
- **Docs:** [docs/README.md](README.md).

### Changed (Step 8: position-based back print reference)

- **scripts/pipeline_generate_packing_list_pdf/back_print_hint.py** — `slot_is_back_print` now gates position-based triggering on raw **Position** having no `/`. Per-slot position tokens (banner source) containing **Back** trigger `assets/Back Print.jpg` beside that logo.
- **scripts/pipeline_generate_packing_list_pdf/draw_page_apparel_and_logos.py** — Logo grid drawing uses `slot_is_back_print` instead of filename-only `logo_filename_indicates_back`.
- **Tests:** [tests/test_back_print_hint.py](../tests/test_back_print_hint.py).
- **Docs:** [generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md).

### Added (Step 1 and 8: Gift Message image URL fallback)

- **scripts/pipeline_cl_lookup/fetch_input_csv.py** — Pass through **Gift - Message** as **Gift Message** on the step-1 CSV.
- **scripts/pipeline_generate_packing_list_pdf/draw_page_left_bottom.py** — Left-bottom item image: use **Item Image URL** first; if empty or download fails, extract an `http(s)://` URL from **Gift Message** (bare URL or embedded in text).
- **Tests:** [tests/test_draw_page_left_bottom.py](../tests/test_draw_page_left_bottom.py), [tests/test_enrich_cl_lookup_customise.py](../tests/test_enrich_cl_lookup_customise.py).
- **Docs:** [fetch_input_csv.md](scripts/fetch_input_csv.md), [generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md).

### Added (Step 5: Design ID Process Tracker; Step 6: numeric process increment)

- **Step 5 — Design ID Process Tracker:** New isolated module [`scripts/pipeline_assign_process_number/design_id_process_tracker.py`](../scripts/pipeline_assign_process_number/design_id_process_tracker.py) reads workbook sheet **"Design ID Process Tracker"** (columns **Design ID**, **Process Number**) when **Separate by Logo ID** is enabled. Over-threshold full-logo rows **in the sheet** get the assigned Process Number (e.g. `49641LG` → `10000`). **Logo ID only:** not in sheet → normal 6-part process number. **Both + fixed process number:** not in sheet → fixed batch (same as below-threshold). Set `USE_TRACKER = False` in the module to disable without changing other pipeline code.
- **Step 6 — Pure numeric process base:** Any group whose step-5 base is digits only (e.g. `10000` from Design ID Process Tracker, or fixed `100`) formats **Process and Item Number** as `Process {display_base} Item-{item}` with `display_base` incrementing (`10000`, `10001`, `10002`, …), not `10000-1`, `10000-2`. Non-numeric bases (`49641LG`, `100A`, `200CNND1X`) keep tracker or dash format. [`grouping_assign.py`](../scripts/pipeline_split_by_process_item/grouping_assign.py), [`grouping_extended.py`](../scripts/pipeline_split_by_process_item/grouping_extended.py), [`common.py`](../scripts/pipeline_split_by_process_item/common.py): `is_pure_numeric_process_base()`, `_normalize_numeric_process_base()`.
- **Tests:** [tests/test_step6_numeric_process_format.py](../tests/test_step6_numeric_process_format.py).
- **Docs:** [assign_process_number.md](scripts/assign_process_number.md), [split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md), [README.md](README.md), [USAGE.md](../USAGE.md).

### Changed (Steps 3 and 7: HK design-token support)

- **scripts/pipeline_fill_prime_images/config.py** — `NORMAL_LOGO_TOKEN_RE` now recognises **HK** suffixes alongside LG/TSU/AV (e.g. `4486HK-White-M-T-BLK-L` → Logo ID `4486HK`).
- **scripts/pipeline_generate_excel_outputs/config.py** — `_DTF_DESIGN_HEAD_LG` includes **HK** for DTF Des design-prefix parsing and New SKU Database remapping.
- **scripts/pipeline_generate_excel_outputs/helpers.py** — `_split_item_sku_by_lg` splits on `\d+(LG|TSU|AV|HK)` so multi-design HK SKUs produce separate DTF Des rows.
- **Tests:** [tests/test_hk_design_token.py](../tests/test_hk_design_token.py).
- **Docs:** [docs/scripts/fill_prime_and_images.md](scripts/fill_prime_and_images.md), [docs/scripts/generate_excel_outputs.md](scripts/generate_excel_outputs.md), [docs/README.md](README.md).

### Changed (Step 7: DTF Des Customise column)

- **scripts/pipeline_generate_excel_outputs/writers.py** — DTF Des column **N** is now **Customise** (`Yes` or blank from the step-6 CSV). Column **P** (**Item Num**) is unchanged.
- **Tests:** [tests/test_dtf_des_customise_column.py](../tests/test_dtf_des_customise_column.py).
- **Docs:** [docs/scripts/generate_excel_outputs.md](scripts/generate_excel_outputs.md).

### Changed (Step 6/8: Draw replace before slash merge)

- **scripts/pipeline_split_by_process_item/common.py** — Step 6 rewrites **Position** using Process Info Sheet **Draw** (column R) via **Position Code** **before** slash merge. Example: `Front Top Center` + `X004` → `Front`; Draw `Front, Back` + single logo → `Front / Back`.
- **scripts/pipeline_generate_packing_list_pdf/position_draw_mapping.py** — Shared `lookup_draw_for_position_code` (case-insensitive).
- **scripts/pipeline_generate_packing_list_pdf/draw_page_banners.py**, **draw_page_overlays.py** — Step 8 always uses Draw lookup by Position Code (no longer skipped when Position contains `/`).
- **Tests:** [tests/test_step6_position_draw_replace.py](../tests/test_step6_position_draw_replace.py).
- **Docs:** [docs/scripts/split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md), [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md), [docs/README.md](README.md).

### Changed (Step 4: skip Multiple Positions expansion for personalized rows)

- **scripts/pipeline_split_position/transform_logo_design.py** — **Multiple Positions** logo suffix expansion now runs only for **non-personalized** rows (`Customise` ≠ Yes). Personalized rows keep the single **Logo/Design Image** from step 3 (typically Order Number), even when their Position Code is on the Multiple Positions sheet.
- **Tests:** [tests/test_split_position_logo_design.py](../tests/test_split_position_logo_design.py) — `test_customise_yes_skips_multiple_positions_even_when_code_on_sheet`.
- **Docs:** [docs/scripts/split_and_assign_position_codes.md](scripts/split_and_assign_position_codes.md), [docs/README.md](README.md).

### Changed (Step 2: Item Options → Customise, back print phrase)

- **scripts/pipeline_cl_lookup/enrich_cl_lookup.py** — Also set **Customise** = `Yes` when Item Options contains `back print option` (case-insensitive substring), if not already Yes (same guard as the existing customisation-message phrase).
- **Tests:** [tests/test_enrich_cl_lookup_customise.py](../tests/test_enrich_cl_lookup_customise.py).
- **Docs:** [enrich_cl_lookup.md](scripts/enrich_cl_lookup.md).

### Added (Step 1–2: Item Options → Customise)

- **scripts/pipeline_cl_lookup/fetch_input_csv.py** — Pass through **Item - Options** as **Item Options** on the step-1 CSV.
- **scripts/pipeline_cl_lookup/enrich_cl_lookup.py** — Set **Customise** = `Yes` when Item Options contains `message if you do need customisation` (case-insensitive), if not already Yes (same guard as Item Name keywords).
- **Docs:** [fetch_input_csv.md](scripts/fetch_input_csv.md), [enrich_cl_lookup.md](scripts/enrich_cl_lookup.md).

---

## 2026-05-18

### Changed (Step 8: pocket/sleeve custom logo lookup)

- **scripts/pipeline_generate_packing_list_pdf/draw_page_custom_logo_context.py** — Customise side-file lookup now includes **`-p` / `-s`** (Pocket / Sleeve) as well as **`-f` / `-b`**, via shared `FBPI_SIDE_SUFFIX_LOOKUP` in `back_print_hint.py`. Matches stems such as `202-9359504-5073928-S-98765PER-….jpg` (case-insensitive `startswith`).
- **Tests:** [tests/test_draw_page_custom_logo_context.py](../tests/test_draw_page_custom_logo_context.py); sleeve/pocket cases in [tests/test_back_print_hint.py](../tests/test_back_print_hint.py).

### Changed (Step 8: anchored suffix detection)

- **scripts/pipeline_generate_packing_list_pdf/back_print_hint.py** — `-f` / `-b` / `-p` / `-s` map to Front/Back/Pocket/Sleeve only **immediately after** the Logo/Design Image anchor (`label_from_stem_after_anchor`). For **fbpi** rows the anchor is the **base** token (first value, side suffix stripped), so files like `order-13-F-98765…` match base `order-13`. Stops false positives from SKU segments (e.g. size `-S-` in `FUC-S-YES`). **fbpi** Front/Back labels also used as fallback when the stem does not match. Helpers: `resolve_logo_anchor_for_slot`, `resolve_apparel_logo_anchor`, `label_for_logo_slot`.
- **Banner labels** and **back print reference** use the same anchored rules per slot.
- **Tests:** [tests/test_back_print_hint.py](../tests/test_back_print_hint.py).
- **Docs:** [generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md).

---

## 2026-05-16

### Added (Step 8: back print reference in logo grid)

- **scripts/pipeline_generate_packing_list_pdf/** — When a resolved logo file stem contains **`-b-`** or ends with **`-b`**, the PDF draws **`assets/Back Print.jpg`** next to that logo (next empty logo column, or split-cell fallback on the last column of a row). **Red outlines** frame the back logo and the reference image. Trigger is **filename-only** (`logo_filename_indicates_back`); position text or customise Front/Back labels alone do not paste the reference.
- **Modules:** [`back_print_hint.py`](../scripts/pipeline_generate_packing_list_pdf/back_print_hint.py), [`draw_page_apparel_and_logos.py`](../scripts/pipeline_generate_packing_list_pdf/draw_page_apparel_and_logos.py); `BACK_PRINT_REFERENCE_IMAGE` in [`runtime_config.py`](../scripts/pipeline_generate_packing_list_pdf/runtime_config.py).
- **Docs:** [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md) — new subsection **Back print reference in logo grid**; [docs/README.md](README.md) — Step 8 table row.

---

## 2026-05-15 (later)

### Removed (`-xz` / `-m` special SKU logic)

- **scripts/pipeline_split_position/transform_logo_design.py** — Removed Item SKU `-xz<number>` / `-m<number>` detection and `LogoID-PositionCode` fallback. **Logo/Design Image** is only rewritten when **Multiple Positions** returns suffixes for the row’s **Position Code**; otherwise step 3 values are kept.
- **scripts/pipeline_split_by_process_item/common.py** — Position ` / ` merge no longer skipped for special SKUs.
- **scripts/pipeline_generate_packing_list_pdf/** — Custom logo front/back lookup (`-f`/`-b`) runs for all customised rows; removed `special_sku_pattern` / `skip_fbpi`.
- **Docs:** [docs/scripts/split_and_assign_position_codes.md](scripts/split_and_assign_position_codes.md), [docs/README.md](README.md).
- **Tests:** [tests/test_split_position_logo_design.py](../tests/test_split_position_logo_design.py) — Replaced xz/m fallback test with custom order + `-M118` SKU unchanged case.

---

## 2026-05-15

### Changed (Step 4: Multiple Positions expands Logo/Design Image for all rows)

- **scripts/pipeline_split_position/transform_logo_design.py** — **Multiple Positions** lookup now runs for every matched row with a logo base (**Logo ID**, or **Order Number** when Customise = Yes), not only Item SKUs containing `-xz<number>` or `-m<number>`. When the sheet returns suffixes for the row’s **Position Code**, **Logo/Design Image** becomes comma-separated `base-suffix` tokens (example: Position Code `X002` with suffixes `f`, `b` and Logo ID `103671LG` → `103671LG-f, 103671LG-b`). When there is no sheet match, **Logo/Design Image** is left unchanged from step 3.
- **Docs:** [docs/scripts/split_and_assign_position_codes.md](scripts/split_and_assign_position_codes.md) — New **Multiple Positions** sheet section; Task 3 and rule details updated. [docs/README.md](README.md) — Step 4 table row, pipeline bullet, Data/ folder note, changelog summary.
- **Tests:** [tests/test_split_position_logo_design.py](../tests/test_split_position_logo_design.py) — Coverage for `X002` expansion, unchanged normal rows, and XZ/M fallback.

---

## 2026-05-14

### Added (Step 8: docs for filename-suffix banner labels)

- **docs/scripts/generate_packing_list_pdf.md** — New subsection **Optional filename-suffix banner labels (`Customise = Yes`)**: rules (substring `-f-`, `-b-`, `-p-`, `-s-` vs legacy `-f`/`-b`/`-p`/`-s` stem end, tie-break), placement on black banners (logo columns + apparel), toggle `LOGO_FILENAME_SUFFIX_LABEL_STEP_ENABLED`, `pdf_asset_log` lines. Clarified that the fbpi position-banner branch still draws empty text for Front/Back while this pass may add words from **resolved** file names.
- **docs/README.md** — Step 8 script table row mentions suffix labels and links to the PDF doc.

---

## 2026-04-17

### Changed (Step 4: special SKU logo suffix for default position)

- **scripts/split_and_assign_position_codes.py** — In special SKU logo/design rewrite (`-xz<number>` / `-m<number>` fallbacks), when Position Code is blank or default `X`, the script no longer appends `-X`; it keeps only `Logo ID` (for example `999123LG` instead of `999123LG-X`). Non-default codes still append as before.
- **Docs:** [docs/scripts/split_and_assign_position_codes.md](scripts/split_and_assign_position_codes.md) — Added rule details for special SKU logo/design rewrite and default-position suffix skip.

### Changed (Step 8: plain-order PDF rendering for `PLAINLG`)

- **scripts/generate_packing_list_pdf.py** — Rows whose Item SKU contains `PLAINLG` now skip Item Image URL rendering, skip logo/design image rendering (including apparel overlays), and render **`Plain Order`** only in the first logo slot (slots 2–5 blank). These rows are not treated as missing logo/apparel.
- **Docs:** [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md) — Documented `PLAINLG` plain-order behavior.

---

## 2026-04-02

### Changed (Docs: Step 7 DTF Des — New SKU Database)

- **docs/scripts/generate_excel_outputs.md** — New section **DTF Des: New SKU database remap**: default path `Data/New SKU Database.csv`, columns **Company-Custom-Label** and **Old-Company-Custom-Label** only, missing-file vs missing-column behaviour, duplicate-key rule, how design prefixes (LG / TSU / AV / fawad+digits / PER) and optional leading marketplace tokens are preserved, fallbacks, and an example (`162547LG-…` → `162547LG-M-T-NAT-M`). Purpose and output table rows point to this section.
- **docs/README.md** — Step 7 script table and pipeline **Excel export** bullet note DTF-only remap; changelog summary entry for 2026-04-02.

---

## 2026-04-01

### Changed (Step 3 / Step 7: **fawad** + digits as logo / design id)

- **scripts/fill_prime_and_images.py** — Item SKU tokens now include **`fawad` + digits** (case-insensitive on the word `fawad`), same `-` + alphanumeric suffix rule as LG/TSU/AV, merged by position with other normal tokens for **Logo ID** and non-custom **Logo/Design Image**. **PER** fallback applies only when none of LG/TSU/AV/fawad match.
- **scripts/generate_excel_outputs.py** — DTF Des design-prefix parsing and SKU splitting recognise leading **`fawad` + digits** (after LG/TSU/AV-style heads, before PER) for New SKU Database remapping and multi-segment rows.
- **Docs:** [docs/scripts/fill_prime_and_images.md](scripts/fill_prime_and_images.md), [docs/scripts/generate_excel_outputs.md](scripts/generate_excel_outputs.md), [docs/README.md](README.md) — token rules, Step 3 table, Step 7 / DTF Des, pipeline Fill step, Normal Logo example.

---

## 2026-03-25

### Changed (Step 3: Logo tokens — full LG/TSU/AV and PER text)

- **scripts/fill_prime_and_images.py** — **LG/TSU/AV** tokens extracted from Item SKU are no longer normalized by removing leading letters before the first digit; the full regex capture is used for **Logo ID** and non-custom **Logo/Design Image** (e.g. `Mehwish21LG` stays `Mehwish21LG`, not `21LG`). **PER** fallback now matches `[A-Za-z0-9]*\d+PER` so an optional alphanumeric prefix before the digits is kept in **Logo ID** (e.g. `Mehwish123PER`).
- **Docs:** [docs/scripts/fill_prime_and_images.md](scripts/fill_prime_and_images.md), [docs/README.md](README.md) — Step 3 table and pipeline Fill step.

### Changed (Step 6: Position slash merge — no Customise gate)

- **scripts/pipeline_split_by_process_item/common.py** — Before writing each step-6 CSV, **Position** is merged with `" / "` when **Logo/Design Image** has exactly one comma-separated token and **Position** has multiple comma-separated parts. **Customise = "Yes"** is no longer required. The merge step no longer requires a **Customise** column to be present.
- **Docs:** [docs/scripts/split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md) — New “Position: slash merge before export” section. [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md) — Slash-merged rows: clarify step-6 source rule and Customise. [docs/README.md](README.md) — Step 6 table and pipeline Group bullet updated.

### Changed (Step 8: PDF left column — taller Gender Apparel cell)

- **scripts/generate_packing_list_pdf.py** — The left-column **Gender Apparel** box is taller than the **Size**, **Colour**, and **Item Quantity** boxes. The three lower cells still share the remaining height equally; the full stack ends at the same bottom line as before (`LEFT_FOUR_BOTTOM_PT`). Tunable via `LEFT_GENDER_CELL_H_PT`.
- **Docs:** [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md) — Layout section documents unequal heights and the related constants. [docs/README.md](README.md) — Step 8 script summary and changelog summary updated.

---

## 2026-03-19

### Changed (Step 7: slash-position rendering)

- **scripts/generate_packing_list_pdf.py** — When `Position` contains `/`, PDFs keep the raw `Position` text in the position banners and skip `Position Code -> Draw` mapping and the Draw-based apparel overlay geometry for that row.
- **Docs:** [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md) — Documented the slash-merged `Position` rule.

---

## 2026-03-11

### Changed (Missing run: dedupe repeated order expansions)

- **missing_run_app.py** — When multiple `Missing/Missing Input.csv` rows resolve to the same **Order Number** within the same date and process, the missing-run builder now expands that order once only instead of repeating the same rows. A final row-level dedupe is also applied before output generation.
- **Docs:** [README.md](README.md), [../README.md](../README.md), and [scripts/missing_run_app.md](scripts/missing_run_app.md) — Missing run behaviour updated to note that duplicate query rows for the same order are deduped automatically, with a dedicated doc page for the tool.

---

## 2026-03-01

### Changed (Step 7: Normal Logo/Design lookup — stem starts with token)

- **scripts/generate_packing_list_pdf.py** — Normal Logo/Design folder lookup fallback no longer uses "stem contains token". After exact stem match, the first file whose stem **starts with** the token is used (e.g. `8513LG` matches `8513LG.png` or `8513LG i found this humerus.png`, but not `158513LG.png`). This prevents token `8513LG` from incorrectly matching `158513LG.png`. Helper `_find_image_normal_logo()` updated; docstring and logic use `stem.startswith(token)`.
- **Docs:** [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md) — Images section: Normal Logo/Design lookup described as exact match then stem **starts with** token, with examples.

### Changed (Step 6: alphabetical sort by Recipient Name for non-merge before additional/item assignment)

- **scripts/split_by_process_and_item_number.py** — Non-merge rows are now sorted by **Gender Apparel** → **Size** → **Colour** → **Recipient Name** (A–Z) before assigning process additional and item numbers. If the "Recipient Name" column is missing, no alphabetical tiebreaker is applied (sort remains Gender → Size → Colour only). Merge rows unchanged (already sorted by Recipient Name).
- **Docs:** [split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md) — Non-merge sort and output order updated; note on missing Recipient Name. [README.md](README.md) — Step 6 table and pipeline Group bullet updated.

---

## 2026-02-28

### Changed (Process Number Tracker: sequence starts at 10000)

- **scripts/split_by_process_and_item_number.py** — Per-day sequence numbers in the Process Number Tracker now start at **10000** when there are no rows for today (10000, 10001, …); existing rows for today still drive the next number (e.g. 10005 → 10006). Constant `TRACKER_SEQUENCE_START = 10000`.
- **Docs:** [split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md) — Tracker section updated to state sequence starts at 10000.

### Changed (Step 7 Excel content: use {seq} instead of {base})

- **scripts/generate_excel_outputs.py** — Content inside all three Excel files (Picking, Orders Details, DTF Des) now uses **{seq}** (tracker display number, e.g. 31) instead of **{base}** for Picking Number and Process Number in cells when the step-6 CSV uses tracker format (`Process 31 Item-1 (...)`). When step-6 uses simple format (no tracker), behaviour is unchanged: process base for Picking Number and base-additional for Process Number. Filenames unchanged. Helpers: `_tracker_seq_from_val()`, `_file_level_seq()`, `_process_number_for_excel_from_row()`.
- **Docs:** [generate_excel_outputs.md](scripts/generate_excel_outputs.md), [README.md](README.md) — Picking Number and Process Number in Excel use {seq} when tracker format, else {base}-{additional}.

### Changed (Fixed process number: step 6 / tracker)

- **pipeline_runner.py** — Step 6 is always called with `use_simple_process_format=False`. **Non‑numeric** fixed process values (e.g. `100A`) use the same tracker-based display format as normal runs. **Numeric-only** fixed values (e.g. `4200`) still set `use_fixed_numeric_process` so step 6 **skips the Process Number Tracker** and uses the sequential numeric display format described in [docs/README.md](README.md) (§4, Step 6).
- **Docs:** [docs/README.md](README.md) and [docs/scripts/split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md) — Clarified numeric fixed vs non‑numeric fixed behaviour.

### Changed (Process display format: hyphen to space)

- **scripts/split_by_process_and_item_number.py** — "Process and Item Number" tracker format now uses a space after "Process" instead of a hyphen: `Process 81 Item-1 (300ANCD1X-1-1)` instead of `Process-81 Item-1 (...)`.
- **scripts/generate_excel_outputs.py** — Picking Block 2 column AB (Col28) now displays `Process ` (space) + process number instead of `Process-` + process number for consistency with step 6.
- **Docs:** README, split_by_process_and_item_number.md, generate_excel_outputs.md — Tracker format and Block 2 descriptions updated to "Process " (space).

---

## 2026-02-27

### Added (Missing pipeline — validation, re-derivation, logging, warning)

- **pipeline_runner.py** — Missing pipeline now requires image-related columns (Picture Name, Apparel Image, Logo/Design Image, Customise, Position Code). Column names are normalized (whitespace stripped). If Apparel Image or Logo/Design Image columns are missing but Picture Name, Item SKU, Customise, Order Number are present, they are re-derived using step-3 logic. After PDF generation, logs image lookup stats (apparel X/Y found, logo X/Y found). Clear error messages when required columns are missing. **Diagnostic logging:** when running missing pipeline, logs each image directory path (and whether it exists) and stem map sizes (apparel, logo_custom, logo_normal). **Excel handling:** Apparel Image, Logo/Design Image, and Picture Name are forced to string after reading the Missing Logos Excel to avoid numeric conversion (e.g. `1671232LG` → 1671232).
- **scripts/fill_prime_and_images.py** — New `fill_apparel_and_logo_from_df()` for re-deriving Apparel Image and Logo/Design Image in DataFrames (e.g. Missing Logos Excel).
- **scripts/generate_packing_list_pdf.py** — New `count_image_lookup_stats()` for per-run apparel/logo lookup counts. CLI accepts optional `--apparel-dir`, `--logo-normal-dir`, `--logo-custom-dir` so standalone runs can embed images. **Apparel lookup:** if exact stem match fails, a case-insensitive stem match is tried. Normal Logo/Design lookup remains exact stem then first stem containing the token (no numeric stem fallback).
- **packing_list_app.py** — When running missing pipeline with all three image directories empty, shows a warning (messagebox) that PDFs will have placeholders only; does not populate the fields. The main pipeline no longer auto-generates the intermediate `Missing Logos (date).xlsx` file; instead it reports missing assets in the GUI completion message/log.
- **Docs:** [docs/README.md](README.md) — New "missing pipeline" section (workflow, required columns, image folder layout). [docs/scripts/generate_packing_list_pdf.md](docs/scripts/generate_packing_list_pdf.md) — Image folder top-level-only note clarified; Apparel case-insensitive fallback documented.

---

## 2026-02-25

### Changed (Step 8: DTF Des — Process Num prefix and Item Num column P)

- **scripts/generate_excel_outputs.py** — DTF Des sheet: **Process Num** (column 9) is now written with `"Process "` prefix (e.g. `Process 124476LG-1`). **Column P** has header **"Item Num"** and is filled with the process-derived item label (e.g. `Item 1`, `Item 2`) from the extended Process and Item Number; all rows from the same CSV line share the same Item Num. Headers extended to 16 columns (two empty, then Item Num in P). [docs/scripts/generate_excel_outputs.md](scripts/generate_excel_outputs.md) updated.

### Changed (Step 7: Normal Logo/Design folder — contains lookup)

- **scripts/generate_packing_list_pdf.py** — **Normal Logo/Design** folder lookup no longer uses exact stem match only. For each logo slot token (e.g. `12345LG`), the script tries an exact stem match first; if none, it uses the first file whose filename (stem) **contains** the token (e.g. `12345LG-1.png`, `Design-12345LG.jpg`). Apparel and Customise logo lookups are unchanged. New helper `_find_image_normal_logo()`. [docs/scripts/generate_packing_list_pdf.md](scripts/generate_packing_list_pdf.md), [docs/README.md](README.md) updated.

### Changed (Step 8: Picking Block 2 parse simple format; Excel process number format toggle; filenames)

- **scripts/generate_excel_outputs.py** — (1) **Simple format parsing:** When step-6 "Process and Item Number" is in the form `Process X Item-Y` (e.g. `Process 124476LG-1 Item-1`), step 8 now parses it so Block 2 column AB no longer shows "Process-Process...". (2) **Process number in Excel:** In Picking, Orders Details, and DTF Des, process number is now configurable via `EXCEL_PROCESS_NO_DASH` in `generate_excel_outputs.py`: by default it is written as **{base}-{additional}** (e.g. `124476LG-1`, `100-1`); when the flag is set to True, it becomes **{base}{additional}** (e.g. `124476LG1`, `1001`). (3) **Filenames:** Orders Details and DTF Des output files use **P{base}** in the filename (e.g. `Orders Details-P124476LG.xlsx`, `DTF Des-P124476LG.xlsx`). Picking remains `{ProcessBase}-Picking.xlsx`. Docs: [generate_excel_outputs.md](scripts/generate_excel_outputs.md).

### Changed (Logo ID threshold: unit-based with full-logo order rule)

- **Step 5 — Threshold metric:** The "Separate by Logo ID" threshold no longer uses **distinct Order Number** per Logo ID. It now uses **units** (rows × Item Quantity): for each Logo ID, only **full-logo orders** contribute (orders where all non-blank Logo ID values in that order are the same). Multi-quantity rows count their Item Quantity; missing or invalid Item Quantity is treated as 1. A Logo ID is over threshold when `unit_count >= logo_id_threshold`. This applies to **Logo ID only** (no fixed) and to **combined** (Logo ID + fixed process number) mode. [scripts/assign_process_number.py](../scripts/assign_process_number.py): added `compute_logo_id_unit_counts()` and `_item_quantity_for_row()`; `run()` now uses unit counts instead of order counts. Docs: [assign_process_number.md](scripts/assign_process_number.md), [README.md](README.md).

### Added (Combine Separate by Logo ID and Use fixed process number; Design ID lookup; Step 6 simple format)

- **Step 5 — Combined behaviour:** When **both** "Separate by Logo ID" and "Use fixed process number" are set, rows whose Logo ID has at least threshold orders get **Process and Item Number** from **Data/Design ID Process Name.csv** (Design ID column → Process Number column) when the Logo ID is listed; otherwise Logo ID (original case). All other rows get the fixed value. Process Info Sheet is **not** loaded when fixed is selected (fixed-only or both). [scripts/assign_process_number.py](../scripts/assign_process_number.py): added `load_design_id_to_process_number()`, `fixed_fallback` and `design_id_to_process_number` in `assign_process_numbers()`, and `run()` branches for both-set vs Logo-ID-only.
- **Step 6 — Simple format when fixed was selected:** When fixed process number was used in step 5, step 6 no longer loads or updates the Process Number Tracker and formats **"Process and Item Number"** as `Process {base}-{additional} Item-{item}` (e.g. `Process 300-1 Item-1`, `Process 300-1 Item-2`) instead of `Process-{seq}{additional} Item-{item} ({extended})`. [scripts/split_by_process_and_item_number.py](../scripts/split_by_process_and_item_number.py): new parameter `use_simple_process_format` in `run()` and in `_sort_and_assign_merge_first()` / `assign_extended_process_and_item_number()`.
- **Pipeline:** [pipeline_runner.py](../pipeline_runner.py) passes `use_fixed_process_number` to step 6 as `use_simple_process_format`.
- **Docs:** [docs/scripts/assign_process_number.md](scripts/assign_process_number.md) — Design ID to Process Number, combined fixed+Logo ID behaviour, Process Info Sheet not loaded when fixed. [docs/scripts/split_by_process_and_item_number.md](scripts/split_by_process_and_item_number.md) — simple format and tracker skipped when `use_simple_process_format` is True. [docs/README.md](README.md) — Step 5 and Step 6 descriptions and pipeline runner text updated.

### Changed (Step 8: Picking prefixes for Process/Item in AB/AC only)

- **scripts/generate_excel_outputs.py** — Picking Excel output now prefixes the **Process Number** and **Item Number** values with `Process-` and `Item-` respectively **only** in Block 2 columns AB and AC (Col28/Col29) of the Picking sheet (e.g. `Process-3700-1`, `Item-1`). All other Process/Item cells keep the raw process+additional and item index. Specs updated in `docs/scripts/generate_excel_outputs.md`.

### Changed (Step 6: expand by quantity before numbering; PDF one page per row)

- **scripts/split_by_process_and_item_number.py** — Step 6 now **expands** each row by Item Quantity before grouping and assigning extended codes: a row with qty=N becomes N rows with qty=1 (like DTF Des). So each unit gets its own row and a **distinct** Process and Item Number (e.g. qty=2 → 3700-1-5 and 3700-1-6). Merge detection after expansion uses Order Number 2+ rows (single-line qty>1 becomes multiple rows). Doc: `docs/scripts/split_by_process_and_item_number.md`.
- **scripts/generate_packing_list_pdf.py** — Removed the per-row expansion by Item Quantity; step-6 CSV is already one row per unit, so PDF uses one page per row and each page shows a unique item number. No more duplicate item numbers for multi-quantity orders.

### Changed (Step 6: Gender Apparel in non-merge sort and additional/item logic)

- **scripts/split_by_process_and_item_number.py** — Non-merge rows are now ordered by **Gender Apparel** (Men, then Women, then Kids when those words appear; else no gender order), then **Size sequence**, then **Colour**. **Additional** increments when Gender Apparel, Size, or Colour (normalized) changes from the previous row. Gender Apparel column is optional; if missing, sort and block logic use Size and Colour only. Doc: `docs/scripts/split_by_process_and_item_number.md`.

### Changed (Step 6: merge block 1 and Recipient Name sort)

- **scripts/split_by_process_and_item_number.py** — Merge rows (Order Number 2+ rows in group or Item Quantity > 1) are all placed in **additional block 1** and **only block 1** is sorted alphabetically by **Recipient Name** before assigning item numbers. Non-merge rows are ordered by **Size sequence** then **Colour** (no multi-row-first step); they use the existing size/colour-change logic, starting at **additional=2** when block 1 is used for merge, or **additional=1** when there are no merge rows in the process. Output row order: merge rows first (Recipient Name order), then non-merge rows (Size then Colour). Doc: `docs/scripts/split_by_process_and_item_number.md`.

### Changed (quantity-aware merge rule)

- **scripts/split_by_process_and_item_number.py** — Extended Process and Item Number assignment now treats a row as part of a *merge order* when either (a) its Order Number appears on 2+ rows in the group, or (b) its Item Quantity > 1. Merge rows are assigned to block 1 (see above); non-merge rows follow the Size/Colour change rules.
- **scripts/generate_excel_outputs.py** — Orders Details Excel output now applies the same quantity-aware merge rule at the process+additional block level: a block is merge when any of its rows has an Order Number that appears on 2+ rows in the split CSV or has Item Quantity > 1. Condition column uses "Condition 1 Merge" / "Condition 4" based on this rule; B/G/P use "Merge Orders" for merge blocks and the hyphenated combo otherwise; Type becomes Normal/Personalised or Normal-Merge/Personalised-Merge. Spec updated in `docs/scripts/generate_excel_outputs.md`.

## 2026-02-23

### Added (Logo ID separate processes)

- **Step 3 — Logo ID column:** [scripts/fill_prime_and_images.py](../scripts/fill_prime_and_images.py) now adds a **Logo ID** column: first `\d+LG` token from Item SKU, case unchanged (e.g. 121990LG); blank only when no token (set regardless of Customise). Passed through step 4 to step 5.
- **Step 5 — Optional Separate by Logo ID:** [scripts/assign_process_number.py](../scripts/assign_process_number.py) accepts `separate_by_logo_id` and `logo_id_threshold`. When enabled, rows whose Logo ID has ≥ threshold **orders** (distinct Order Number) get **Process and Item Number = Logo ID** (e.g. 123lg); others get the normal 6-part Process Number. CLI: `--separate-by-logo-id`, `--logo-id-threshold N`.
- **GUI:** Checkbox **Separate by Logo ID** and numeric **Logo ID threshold** (default 5). Settings persisted in `gui_config.json`. Pipeline runner and GUI pass these options to step 5.
- **Pipeline runner:** `run_pipeline(..., separate_by_logo_id=False, logo_id_threshold=5, log=None)`.

### Added (Use fixed process number)

- **Step 5 — Optional fixed process number:** [scripts/assign_process_number.py](../scripts/assign_process_number.py) accepts `fixed_process_number`. When non-empty, every row gets that value as **Process and Item Number**; the workbook and Logo ID logic are skipped. Step 6 then produces one CSV (and one set of PDFs) for that process. CLI: `--fixed-process-number 100A` (overrides normal and Logo ID assignment).
- **GUI:** Checkbox **Use fixed process number** and entry **Fixed process number** (e.g. 100, 100A). When enabled, the pipeline uses this value for all rows. Validation: process number required when checkbox is on. Settings persisted in `gui_config.json`.
- **Pipeline runner:** `run_pipeline(..., use_fixed_process_number=False, fixed_process_number=None, log=None)`.

### Documentation

- **docs/README.md** — Step 3 adds Logo ID; Step 5 optional Separate by Logo ID (rows over threshold get Logo ID as process number); Step 5 optional Use fixed process number (one value for all rows → one process’s PDFs); Step 6 unchanged (normal sort for all groups). Pipeline runner and GUI describe new parameters. Changelog summary: 2026-02-23.
- **docs/scripts/assign_process_number.md** — Optional "Separate by Logo ID" section; CLI `--separate-by-logo-id`, `--logo-id-threshold`; optional "Use fixed process number" and CLI `--fixed-process-number` (overrides normal and Logo ID).
- **docs/scripts/split_by_process_and_item_number.md** — Note that logo process groups use the same normal sort (merge, size, colour).

### Changed (Step 7: PDF splitting & image compression)

- **scripts/generate_packing_list_pdf.py** — When a step-6 CSV would produce **more than 50 pages**, the output is split into multiple PDFs of up to 50 pages each, named `{stem}_Part 1.pdf`, `{stem}_Part 2.pdf`, etc. (`MAX_PAGES_PER_PDF = 50`). For ≤ 50 pages, a single `{stem}.pdf` is written. Images (Apparel, Logo/Design) are now resized to fit their display boxes at a target DPI and recompressed (JPEG for non-transparent images, PNG for images with alpha) before embedding to reduce PDF file size.
- **requirements.txt** — Added `Pillow` dependency for image resizing/compression in PDF generation.
- **docs/scripts/generate_packing_list_pdf.md** — Updated to describe the 50-page split behaviour, new file naming (`{stem}_partN.pdf`), Pillow dependency, and image resize/compress behaviour.

### Changed (Step 7: quantity expansion)

- **scripts/generate_packing_list_pdf.py** — Before rendering, expands each step-6 CSV row by **Item Quantity** so that quantity `N` produces `N` pages (one unit per page, each with Item Quantity shown as 1). The 50-page splitting logic now counts **expanded pages**. Customise logo lookup continues to use `OrderNumber-Rank` based on the expanded row index.
- **docs/scripts/generate_packing_list_pdf.md** — Purpose and layout updated to state that PDFs are generated on a one-page-per-unit basis (rows expanded by Item Quantity; Items box shows the expanded page count per order).

### Changed (Step 7: customise logo lookup naming)

- **scripts/generate_packing_list_pdf.py** — Customise Logo/Design image lookup: first item per order uses Order Number only (e.g. `22-14258-68431`); second item uses `OrderNumber-1`, third `OrderNumber-2`, etc. (no suffix for the first item).
- **docs/scripts/generate_packing_list_pdf.md** — Images section: Customise Logo/Design folder lookup described as first item by Order Number, second by `OrderNumber-1`, third by `OrderNumber-2`.

---

## 2026-02-20

### Added

- **GUI progress logging** — The GUI log area shows step-by-step progress (Step 1/8: Fetching input CSV…, Step 1/8: Done., … Step 8/8: Done.) as the pipeline runs. Implemented via an optional `log` callback on `run_pipeline` and a thread-safe queue in the app so the worker thread enqueues messages and the main thread appends them to the log widget.
- **Pipeline runner `log` parameter** — `run_pipeline(..., log=None)`. When provided, `log(msg: str)` is called before/after each step with short descriptions and optional counts (rows, CSVs, pages).

### Changed

- **Image folder search (generate_packing_list_pdf.py)** — Only the **Customise Logo/Design** folder is searched recursively (subdirectories). The **Apparel Image** and **Normal Logo/Design** folders are searched **top level only** (no subdirectories). Implemented via a `recursive` parameter on the internal image lookup.
- **Fast PDF generation** — (1) **Font metrics cache:** Vertical centering in `_draw_text_in_box` uses a cached `(font, font_size)` → (ascent, descent) so ReportLab font face is not queried per draw. (2) **Stem maps:** The pipeline builds one stem→Path map per image directory (in parallel with ThreadPoolExecutor) before any PDF; `csv_to_pdf` accepts optional stem map arguments so each page does O(1) image lookup instead of scanning the directory. (3) **Row loop:** `csv_to_pdf` uses `df.iloc[i]` instead of `iterrows()`. (4) **Parallel PDFs:** When there are multiple step-6 CSVs, the pipeline uses ProcessPoolExecutor to generate PDFs in parallel; when there is one CSV, a single `csv_to_pdf` call is used. (5) `csv_to_pdf` returns the number of pages written (int); CLI and pipeline use this for logging.

### Documentation

- **docs/README.md** — "Running the pipeline": pipeline runner now documents optional `log` callback and execution order (Step 7 Excel then Step 8 PDFs); added image-folder notes for PDF generation. Changelog summary: 2026-02-20 entry for logging, folder search, fast PDFs.
- **docs/scripts/generate_packing_list_pdf.md** — "Images" section rewritten: folder behaviour (Apparel and Normal top-level only, Customise recursive), lookup rules, and a "Performance" paragraph (stem maps, font cache, parallel PDF generation from pipeline).

---

## 2026-02-19

### Added (step 8: Excel export)

- **scripts/generate_excel_outputs.py** — **Step 7 (Excel export):** For each step-6 CSV, writes three Excel files to the same folder: `{ProcessBase}-Picking.xlsx`, `Orders Details-P{ProcessBase}.xlsx`, `DTF Des-P{ProcessBase}.xlsx`. Picking: rows expanded by Item Quantity, two column blocks, dispatch date in Col0, full Process and Item Number in both Process Number and Item Number columns. Orders Details: one row per **process+additional block** (not per CSV line); Condition 1 Merge / Condition 4; Type = Normal / Personalised or Normal-Merge / Personalised-Merge (from Customise); B/G/P = hyphenated Gender-Apparel-Colour-Size or "Merge Orders"; Merge/Single columns = numeric (distinct Recipient count, total quantity). DTF Des: one row per unit (expand by Item Quantity; each row Item - Qty = 1), or per design ID when Item SKU has multiple LGs; Order - Number, Item - Qty, Item - SKU, Ship To - Name, Process Num, Genre; Notes, Postal Code, Source, Order Type, Condition left empty. CLI: `python scripts/generate_excel_outputs.py <step6_csv> <output_dir> <date_dd_mm_yyyy>`. Spec: `docs/scripts/generate_excel_outputs.md`.
- **pipeline_runner.py** — After step 6, for each step-6 CSV calls `run_generate_excel_outputs(csv_path, output_root, dispatch_date)` before generating PDFs (**step 8**).
- **docs/scripts/generate_excel_outputs.md** — Purpose, usage, output files summary, required columns, where it fits.
- **docs/README.md** — Script table: added row for `generate_excel_outputs.py`. Pipeline: eight steps; step 7 Excel export; step 8 PDFs; pipeline runner runs steps 1–8.

### Documentation

- **docs/README.md** — Step 4 output: corrected unmatched filename to `unmatched_orders_{token}.csv` (was `4_unmatched_split_and_assign_position_codes_{token}.csv`). Pipeline section rewritten: "Pipeline (planned)" → "Pipeline" with the actual 7-step flow; added "Running the pipeline" (CLI, pipeline_runner, GUI). Step 6 and Step 7 table rows updated (output path, Process Number Tracker, landscape). Added "Project layout (root)" table (docs, scripts, Input, Output, Workbook, pipeline_runner, gui, gui_config). Changelog section now references CHANGELOG.md with a short summary including 2026-02-19.
- Renamed `gui.py` to `packing_list_app.py`; updated README project layout and Running the pipeline (GUI) to use the new name.
- **docs/scripts/split_and_assign_position_codes.md** — Unmatched output filename corrected to `unmatched_orders_{token}.csv` in Purpose, Rules, and Where it fits.
- **docs/scripts/split_by_process_and_item_number.md** — Output path clarified: writes to `output_dir` (CLI default `Output/`; pipeline uses `Output/DD-MM-YYYY/{token}/`). Added "Output location" note under Usage.

### Changed

- **Orders Details (generate_excel_outputs.py):** Single = **total quantity** (sum of Item Quantity per process+additional block), not row count, so multi-quantity lines are reflected correctly. Spec: docs/scripts/generate_excel_outputs.md (Orders Details).
- **DTF Des (generate_excel_outputs.py):** Expand by quantity: when Item Quantity is N, emit N rows each with Item - Qty = 1 (e.g. 3 quantities → 3 rows, each quantity 1). Spec: docs/scripts/generate_excel_outputs.md (DTF Des).
- **Removed:** `Target/` folder, `scripts/inspect_target_excel.py`, `scripts/inspect_target_excel_short.py`, and generated `target_excel_structure.txt` files. Excel output behaviour is fully defined in `docs/scripts/generate_excel_outputs.md`; no reference Excel templates are required at runtime.
- **Project layout:** `Workbook.xlsx` and `New SKU Database.csv` moved into **`Data/`** folder. Default paths in scripts, GUI, and docs updated to `Data/Workbook.xlsx` and `Data/New SKU Database.csv`. Root folder simplified.

---

## 2026-02-16

### Added (packing list PDF step; later numbered step 8)

- **scripts/generate_packing_list_pdf.py** — Reads step-6 CSV file(s) (single file or directory). Produces one PDF per CSV; pages expand by Item Quantity. Layout is fixed in code from PDF Layout Example.xlsx (script does not read the Excel at runtime). Image slots initially rendered as text only. CLI: `python scripts/generate_packing_list_pdf.py <path_to_step6_csv_or_directory> [output_path_or_dir]`. Dependencies: pandas, reportlab.
- **Layout refinements (2026-02-16)** — No box outlines; Items box shows `"Items = N"` only on the first page of multi-row orders (blank otherwise); Recipient block is black with centered, wrapped name on single-row orders and on the first page of multi-row orders, and red with no name on subsequent pages of multi-row orders.
- **docs/scripts/generate_packing_list_pdf.md** — Purpose, usage, layout mapping, required columns, images-as-text note.

### Changed (step 6: extended Process and Item Number)

- **scripts/split_by_process_and_item_number.py** — After sorting each group, assigns extended Process and Item Number per row: format `{base}{additional}-{item}` (e.g. 100ANND1X1-1, 100ANND1X2-1). Merge orders (Order Number with 2+ rows in file): additional unchanged, item increments. Other rows: additional increments when Size or Colour changes; item increments when both match previous. Requires Order Number, Size, Colour in step-5 CSV.
- **docs/scripts/split_by_process_and_item_number.md** — Documented extended format and rules; required columns now include Order Number, Colour.

---

## 2026-02-15

### Added (step 6: split by process and item number)

- **scripts/split_by_process_and_item_number.py** — Step 6: Reads step-5 CSV and optionally Workbook "Process Info Sheet" column "Sequence by Size" (AD). Groups rows by Process and Item Number, sorts each group by Size (sizes not in the list go to the end), writes one CSV per value to `Output/YYYY-MM-DD/{ProcessAndItemNumber}.csv`. Blank Process and Item Number → `_blank.csv`.
- **docs/scripts/split_by_process_and_item_number.md** — Purpose, Sequence by Size column, CLI, required columns, edge cases.

---

## 2026-02-14

### Added (step 5: assign process number)

- **scripts/assign_process_number.py** — Step 5: Reads step-4 matched CSV and Workbook "Process Info Sheet". Assigns a 6-part Process Number (process start number + shift code + prime code + customise code + dispatch code + position code) to each row and writes it into Process and Item Number. Lookups: Gender Apparel → col B; user shift (1st–5th) → col D/E; Prime Yes/No → col G/H; Customise Yes/No → col J/K; Ship By vs today → col M/N; Position Code from CSV. Output: `Output/5_assign_process_number_{token}.csv`. Default workbook: `Workbook.xlsx`.
- **docs/scripts/assign_process_number.md** — Purpose, Process Info Sheet columns A–N, CLI usage, required columns.

### Changed (step 5: simple rules for Prime, Customise, Dispatch)

- **scripts/assign_process_number.py** — Process Info Sheet used only for Gender Apparel (Process Start, col B) and Shift (Code, col E). Prime: Yes→P, else N. Customise: Yes→C, else N. Dispatch: Ship By date is today→D, else D1. Removed build_prime_lookup, build_customise_lookup, build_dispatch_lookup and fallback constants.
- **docs/scripts/assign_process_number.md** — States that Prime, Customise, and Dispatch use fixed codes; only Gender Apparel and Shift use the Process Info Sheet.

---

## 2026-02-13

### Added (step 4: split and assign position codes)

- **scripts/split_and_assign_position_codes.py** — Step 4: Splits step-3 output by Gender Apparel; writes unmatched rows (blank Gender Apparel) to `Output/4_unmatched_split_and_assign_position_codes_{token}.csv`; on matched rows, inserts Position Code column from Workbook.xlsx "Process Info Sheet" (columns P and Q: Default Position and Position Combination 1, 2, …); writes matched rows to `Output/4_matched_split_and_assign_position_codes_{token}.csv`.
- **docs/scripts/split_and_assign_position_codes.md** — Purpose, Process Info Sheet layout, CLI usage, required columns.

---

## 2026-02-06

### Added

- **Project setup**
  - Main project doc: `docs/README.md` — purpose, data formats (§2), pipeline outline, script index.
  - This changelog: `docs/CHANGELOG.md`.

- **Input sample**
  - Documented sample: `Input/b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv` (44 data rows, 20 columns).
  - Noted: one row per line item; same order can repeat; dates DD-MM-YYYY; weight with " g"; Item SKU sometimes multiple per cell.

- **Target**
  - Target schema from `300ANP Packing List (Demo).csv`: 12 columns; direct mappings identified for Order Number, Item Quantity, Item SKU, Item Name, Recipient Name; rest pending (Process and Item Number, Gender Apparel, Size, Colour Name, Picture Name, Apparel Picture, Design Picture).
  - Reference: `Data Needed in Packing List PDFs.xlsx` for business rules.

- **Pipeline (planned)**
  - Load CSV → Validate/Clean → Transform to packing list → Group by order → Render → Export PDF.

### Added (fetch script)

- **scripts/fetch_input_csv.py** — Step 1: Fetches data from ShipStation CSV (Current View).
  - Reads CSV; keeps only six columns with renames: Order # → Order Number, Quantity → Item Quantity, Recipient → Recipient Name; keeps Tags, Item SKU, Item Name.
  - Strips whitespace from string values. Returns `list[dict]` for use by other scripts.
  - When run as main: writes to `Output/1_fetch_input_csv_{token}.csv` by default (e.g. `Output/1_fetch_input_csv_b03aede9-f1b4-4a6e-95a7-7576f1273bf2.csv`; creates `Output/` if needed). Default input is no longer assumed; the input CSV path is required on the CLI.
  - Missing columns in CSV are treated as empty string with a one-time warning per column.

### Added (step 2: enrich CL lookup)

- **scripts/enrich_cl_lookup.py** — Step 2: Enriches packing data from Workbook.xlsx sheet "CL Database".
  - Reads step-1 CSV and "CL Database" (pandas + openpyxl). Extracts custom label from Item SKU: first "LG", then first "-" after it, then whole substring to end of string. Exact match (trimmed, case-insensitive) to "Custom Label" column.
  - Appends nine columns in order: Process and Item Number, Gender Apparel, Size, Colour, Picture Name, Position, Customise, Apparel Image, Logo/Design Image. Fills from matching CL Database row or leaves empty if no match.
  - Default output: `Output/2_enrich_cl_lookup_{token}.csv`, where `token` normally matches the original ShipStation CSV stem (derived from the step-1 filename). Dependencies: `pandas`, `openpyxl` (see `requirements.txt`).

### Next steps

- Add more scripts (transform, PDF, etc.) as directed; update this changelog with each.
