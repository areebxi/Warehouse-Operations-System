# generate_packing_list_pdf.py — Step 8

Eighth step in the pipeline: **generate packing list PDFs** from step-6 CSV file(s). One logical PDF per CSV file; each PDF has **one page per unit** (rows are expanded by Item Quantity before rendering). **Page orientation: landscape.** Layout matches the reference image: **no grid lines**; plain page with colored blocks only (black banners for Recipient Name and for 1st–5th Position headers, light grey for Apparel Image and Logo/Design Image 1st–5th areas). White bold text on black; red bold for Size and Item Quantity; black normal elsewhere.

## Purpose

- Read step-6 CSV file(s) (e.g. from `Output/DD-MM-YYYY/{Shift} Shift/{token}/`).
- Expand each CSV row by **Item Quantity** so that quantity `N` produces **N pages** (one unit per page; each page shows Item Quantity = 1).
- For each expanded row, produce one PDF page with fields placed according to the fixed layout grid (22 rows × 4 columns).
- Write **one or more PDFs per CSV file**. When the expanded CSV would produce **≤ 50 pages**, a single PDF is written (e.g. `Output/2026-02-16/100ANND1X.pdf`). When it would produce **> 50 pages**, the output is split into **parts of 50 pages each**, named `{stem}_Part 1.pdf`, `{stem}_Part 2.pdf`, etc. (e.g. `100ANND1X_Part 1.pdf`, `100ANND1X_Part 2.pdf`).

## Usage

**From the command line:**

```bash
# Single CSV: output PDF alongside CSV (same path, .pdf extension)
python scripts/generate_packing_list_pdf.py Output/2026-02-16/100ANND1X.csv

# Single CSV with explicit output path
python scripts/generate_packing_list_pdf.py Output/2026-02-16/100ANND1X.csv Output/2026-02-16/100ANND1X.pdf

# Directory: one PDF per CSV in that directory (output in same directory by default)
python scripts/generate_packing_list_pdf.py Output/2026-02-16

# Directory with explicit output directory
python scripts/generate_packing_list_pdf.py Output/2026-02-16 Output/2026-02-16

# With image folders (embeds apparel and logo images; without these, slots show placeholders A/L)
python scripts/generate_packing_list_pdf.py Output/2026-02-16/100ANND1X.csv --apparel-dir "I:/Apparel" --logo-normal-dir "I:/DTF Designs" --logo-custom-dir "I:/Per Design"
```

- **input_path** (required): Path to a single step-6 CSV file or a directory containing step-6 CSV files.
- **output_path_or_dir** (optional): For a single CSV, path to the output PDF file (or a directory to place the PDF in). For a directory input, path to the directory where PDFs will be written (default: same as input directory). When a CSV would produce more than 50 pages, multiple files are written for that CSV as `{stem}_Part N.pdf`.
- **--apparel-dir**, **--logo-normal-dir**, **--logo-custom-dir** (optional): Paths to the Apparel Image, Normal Logo/Design, and Customise Logo/Design folders. When provided, the script looks up images by file stem (same rules as the pipeline) and embeds them in the PDF. If none of these are given, image slots show placeholders (red "A" for apparel, "L" for logo). Use the same folder paths as in the GUI when running the script standalone (e.g. for a missing CSV or a single step-6 file).

**Dependencies:** `pandas`, `reportlab`, `Pillow` (install with `pip install -r requirements.txt`).

## Layout

The layout is fixed in code from the reference picture (22 rows × 4 columns). Fields are mapped as follows:

- **Items** (row 0, col 0): Rendered as **"Items = "** followed by the number of pages for that Order Number (expanded row count after quantity expansion). For multi-row (merge) orders, `Items = N` is shown on **every page** for that Order Number. For single-row orders, the Items box is blank.
- **Order Number**, **Item SKU** (row 0, cols 1–2): Order Number is **displayed with merge suffixes for PDFs only**: for orders that appear on multiple rows in the step-6 CSV, the first page shows the raw value (e.g. `202-2419637-5153105`), the second page shows `202-2419637-5153105-1`, the third `202-2419637-5153105-2`, and so on, matching the customised logo image naming convention. The underlying `Order Number` column in the CSV is **not** modified; Excel exports and other steps still use the raw value.
- **Process and Item Number + total items**, **Item Name** (rows 1–2, col 1): The second header line shows the **full** `Process and Item Number` value from step-6 (including the extended code in parentheses), with a summary suffix appended like `({N} Items)`. For example, if the CSV value is `Process 100071 Item-1 (300ENCD1X-1 1)` and there are 5 rows for that process in the CSV, the PDF header shows `Process 100071 Item-1 (300ENCD1X-1 1) (5 Items)`. `{N}` is the **total number of rows in that step-6 CSV for that process** (ignoring Item-1 / Item-2 split). If the value cannot be parsed, the original **Process and Item Number** text is shown without the `(N Items)` suffix.
- **Recipient Name** (row 3, col 0): From CSV.
- **1st Position**, **2nd Position** (row 3, cols 2–3): First and second token from **Position** (comma-separated). The black banner above the Apparel Image (row 3, col 1) is intentionally left blank.
- **Apparel Image**, **Logo/Design Image (1st)**, **Logo/Design Image (2nd)** (row 4, cols 1–3): From CSV; image references rendered as text.
- **Gender Apparel**, **Size**, **Colour**, **Item Quantity** (stacked in col 0 below Recipient; conceptually rows 8, 11, 14, 17 in the 22×4 grid): From CSV. **Heights are not equal:** the **Gender Apparel** cell is taller (`LEFT_GENDER_CELL_H_PT` in code, layout pt); **Size**, **Colour**, and **Item Quantity** share the remaining vertical band in **three equal** slices (`LEFT_OTHER_CELL_H_PT`). The stack is pinned between `LEFT_FOUR_TOP_PT` (below Recipient) and `LEFT_FOUR_BOTTOM_PT` (just above Picture Name), so the Picture Name row alignment is unchanged. To change only the Gender row height, edit `LEFT_GENDER_CELL_H_PT` in [`scripts/pipeline_generate_packing_list_pdf/pdf_page_layout.py`](../../scripts/pipeline_generate_packing_list_pdf/pdf_page_layout.py).
- **Picture Name** (row 20, col 0): From CSV.
- **3rd/4th/5th Position** (row 20, cols 1–3): Third, fourth, and fifth token from **Position** (comma-separated). Row 21 has **Logo/Design Image (3rd/4th/5th)** — third, fourth, fifth token from **Logo/Design Image**, rendered as text.

**Customise = Yes:** When the optional column **Customise** is "Yes" (case-insensitive), Position and Logo/Design Image are **not** split across cells: the full Position value is shown in the **1st Position** banner only (2nd–5th position banners blank), and the full Logo/Design Image value is shown in the **1st Logo/Design Image** cell only (2nd–5th logo cells blank). When Customise is not "Yes" or the column is missing, the comma-split behaviour above applies.

**Logo/Design Image (1st–5th):** Only as many logo cells are filled as there are design IDs (same rule for both Customise and non-customise). The **Logo/Design Image** value is split by commas into up to 5 tokens; the 1st token goes in the 1st cell, the 2nd in the 2nd cell, and so on. One design ID fills only the 1st cell; two IDs fill 1st and 2nd; remaining cells stay empty unless there are 3–5 comma-separated design IDs. For **Customise = Yes**, the base custom image is looked up by the **Logo/Design Image token** for that row (which Step 6 writes as `OrderNumber`, `OrderNumber-1`, `OrderNumber-2`, … for multi-row personalised orders) and shown in the first logo box when present; for non-customise rows, each slot’s image is looked up by that slot’s token in the normal logo folder.

**Plain-order SKU rule (`plain` or `plainlg` in Item SKU):**

- When **Item SKU** contains **`plainlg`** or **`plain`** (case-insensitive substring; helper `is_plain_order_sku_impl` in `core_helpers.py`), the PDF treats the row as a plain order.
- The left-bottom **Item Image URL** image is skipped (including any **Gift Message** URL fallback).
- Logo/design image drawing is skipped for all logo slots and apparel overlays.
- In the logo boxes, only the **first** slot displays **`Plain Order`**; logo slots 2nd–5th remain blank.
- These rows are intentional plain orders and are not counted as missing-logo or missing-apparel errors (Preflight Issues uses the same helper for Missing Logo dry-run).

**Default and Position-based overlays on Apparel Image:**

- When a customised row has explicit **F/B/P/I** images (see below), **no** logo is overlaid on top of the Apparel Image cell; those rows use only the grey logo squares and their F/B/P/I banners.
- Otherwise, overlays depend on the **Position** text (from step 6) and the **Logo/Design Image** tokens:
  - The **Logo/Design Image** value is split into tokens `L1, L2, ...` and **Position** is split into tokens `P1, P2, ...` by commas. When both lists are non-empty and have the same length, each logo token `Li` is paired with `Pi`.
  - For each `(Li, Pi)` pair:
    - If `Pi` mentions **Front** (case-insensitive) and **does not** mention Pocket, `Li` is overlaid **once** in the center of the Apparel Image at the “front” size (same scale and vertical nudge as the original default overlay). The logo also still appears in its own logo square.
    - If `Pi` mentions **Pocket** but **not** Front, and **does not** also mention Back, `Li` is overlaid once at a **pocket size** (6× smaller than the Apparel cell), shifted **30 layout units to the left** from the centered position and nudged **higher than the front overlay** (an additional 35 layout units above the front baseline).
    - If `Pi` is a composite that mentions **both Front and Pocket** (e.g. `"Front Left Pocket / Back Top Center"`), this is treated as one logo going to multiple positions; in that case `Li` is overlaid **once** using the **front** behaviour (centered, front size), with no extra pocket overlay.
    - If `Pi` mentions **Pocket** and **Back** but not Front (e.g. `"Left Pocket / Back Top Center"`), no apparel overlay is drawn for that logo (back-only for a front-view garment).
  - If Position and Logo/Design Image **cannot be paired** (different counts) or if **no** mapped position token is classified as Front or Pocket under the rules above, the script falls back to the original default behaviour: when **Position Code** equals the default (e.g. `"X"`), the **first** logo is overlaid in the center of the Apparel Image cell at 1/2.5 size. The first logo continues to appear in its own Logo 1st cell as well; other logo slots are unchanged.

- **Slash-merged Position rows (`Position` contains `/`):**
  - These rows typically come from **step 6** after **Draw replace** and slash merge: e.g. Draw `Front, Back` with a single logo token becomes `Front / Back` in the step-6 CSV.
  - Step 8 shows that **Position** text in the black position banners. Step 8 also looks up **Position Code → Draw** as a fallback when the CSV still has long CL text.
  - Draw-based apparel overlay geometry still skips rows whose **Position** contains `/` (overlay uses Draw tokens from Position Code when Position has no slash).

## Required columns

The step-6 CSV is expected to contain at least: **Order Number**, **Item SKU**, **Item Name**, **Recipient Name**, **Process and Item Number**, **Gender Apparel**, **Size**, **Colour**, **Item Quantity**, **Picture Name**, **Apparel Image**, **Logo/Design Image**. **Customise** is optional; if present and "Yes", position and logo text are shown unsplit in the first cell only. Missing columns are treated as empty.

## Images

### Left-bottom item image (URL)

The cell below **Item Quantity** (left column) can show a product image downloaded from a URL in the CSV:

1. **Item Image URL** — used first when non-empty.
2. **Gift Message** — fallback when **Item Image URL** is empty or the download/draw fails. The value may be a bare URL or free text containing an `http://` or `https://` link (first match is used).

Implemented in [`draw_page_left_bottom.py`](../../scripts/pipeline_generate_packing_list_pdf/draw_page_left_bottom.py). **Plain-order** rows (`plain` / `plainlg` in Item SKU) skip this entirely.

**Pipeline vs standalone:** When you run the full app or `scripts.pipeline_runner.run_pipeline`, step 8 receives **pre-built stem maps**. The runner builds those maps with **top level only** (no subfolders) for apparel, normal logos, **Customise Single Position**, and **Customise Double Position** (single is tried before double). When you run **`python scripts/generate_packing_list_pdf.py`** alone with `--logo-custom-dir`, this script builds its own maps: **`--logo-custom-dir` is indexed recursively**; `--apparel-dir` and `--logo-normal-dir` are **top level only**.

When the pipeline or CLI provides **Apparel Image folder**, **Normal Logo/Design folder**, and/or **Customise Logo/Design folder** (GUI paths or `csv_to_pdf` dir arguments), the script looks up image files by **file stem** (name without extension) and draws them in the Apparel and Logo/Design slots. Supported extensions: `.png`, `.jpg`, `.jpeg`. Lookup behaviour:

- **Apparel Image folder:** Search **top level only** (no subdirectories). Tries Apparel Image value then Picture Name. If no exact stem match is found, a **case-insensitive** match is tried (e.g. `Only-Design-Iron-On-Sticker` matches `only-design-iron-on-sticker.png`). Place new or corrected images directly in the folder; subfolders are not searched.
- **Normal Logo/Design folder:** Search **top level only**. Each logo slot (1st–5th) is looked up by its token (e.g. `8513LG`, `fawad22`) when Customise is not "Yes". Lookup: first an **exact** stem match is tried; if none, the first file whose stem **starts with** the token is used (e.g. token `8513LG` matches `8513LG.png` or `8513LG i found this humerus.png`, but not `158513LG.png`). This avoids wrong matches when one logo ID is a substring of another. Place images directly in the folder; subfolders are not searched.
- **Multi-suffix logos from step 4:** When [split_and_assign_position_codes.md](split_and_assign_position_codes.md) expands **Logo/Design Image** via the workbook **Multiple Positions** sheet (e.g. `103671LG-f, 103671LG-b`), step 8 looks up **each** token in the Normal Logo/Design folder. Provide one image file per suffix stem (`103671LG-f.png`, `103671LG-b.png`, etc.).
- **Customise Logo/Design folder(s):** With **pre-built maps from the pipeline**, only **top-level** files in each customise folder appear in the map. With **standalone `--logo-custom-dir`**, search is **recursive** (root and all subfolders). For customised rows, the base logo for that row is looked up by its **Logo/Design Image token** (normally `OrderNumber`, `OrderNumber-1`, `OrderNumber-2`, … as written by Step 6). Side variants now use only **Front/Back** tokens:
  - `<stem>-f`, `<stem>-b` for the first unit’s stem (e.g. `22-14258-68431-f` when the stem is `22-14258-68431`).
  - For subsequent units in a multi-row personalised order, stems such as `OrderNumber-1`, `OrderNumber-2`, … are used, giving filenames like `OrderNumber-1-f`, `OrderNumber-1-b`, etc.

  When such stems exist for a row, the script:

  - Uses the base custom image (`OrderNumber` / `OrderNumber-N`) in the **first** logo box when present.
  - Fills the remaining logo boxes from left to right with any `-f` / `-b` / `-p` / `-s` images found (lookup via [`draw_page_custom_logo_context.py`](../../scripts/pipeline_generate_packing_list_pdf/draw_page_custom_logo_context.py); stems may use uppercase letters, e.g. `order-S-98765PER-….jpg`). The fbpi branch in `draw_position_banners` still draws **empty** text for **Front** / **Back** / **Pocket** / **Sleeve** in the mapped banner cells; see **Optional filename-suffix banner labels** below for a separate pass that may add those words from **resolved** file names.

  For these personalised side images, the file **stem** may include extra descriptive suffixes after the side token (example: `25-14291-20610-2-b-K-T-BLK-YM.png` is treated as the Back image for `25-14291-20610-2-b` in non-scoped lookup paths). For scoped rows (`Customise = Yes` and duplicated by `Order Number (Base)`), matching is exact-only with priority:
  - Side: `{LogoOrDesignToken}-{f|b}-{ItemSKU}` then `{LogoOrDesignToken}-{f|b}`
  - Non-side: `{LogoOrDesignToken}-{ItemSKU}` then `{LogoOrDesignToken}`

  When any of these side images are present for a row, the script uses them in the logo boxes as described above and **does not** overlay a logo on top of the Apparel Image cell for that row.

### Optional filename-suffix banner labels (`Customise = Yes`)

Implemented in [`scripts/pipeline_generate_packing_list_pdf/draw_page_logo_suffix_labels_step.py`](../../scripts/pipeline_generate_packing_list_pdf/draw_page_logo_suffix_labels_step.py), invoked at the end of each PDF page draw in `draw_page_impl` (after logos). **Plain orders** and **Customise ≠ Yes** skip this pass entirely.

**What it reads:** the **resolved** filesystem paths already chosen for the page — the same apparel lookup as the apparel square (`Apparel Image`, then `Picture Name`), and each of the five logo slots via `logo_image_for_slot`. It does **not** change lookup rules.

**How it maps:** on each path’s **filename stem** (case-insensitive), only **after** the Logo/Design Image anchor for that slot. Implemented in [`back_print_hint.py`](../../scripts/pipeline_generate_packing_list_pdf/back_print_hint.py) (`label_from_stem_after_anchor`, `label_for_logo_slot`):

- **fbpi rows** (separate front/back files): anchor = **base** token (first comma-separated Logo/Design Image value, any trailing `-f`/`-b`/… stripped). Example: base `202-3246136-6506730-13`, file `…-13-F-98765PER-…` → **Front**.
- **Other rows:** anchor = the token for that slot (e.g. Step 4 `103671LG-f`, `103671LG-b`).
- Rules on the stem after the anchor: `-f-`/`-b-`/… or legacy `-f`/`-b`/… → Front/Back/Pocket/Sleeve (order **f → b → p → s**). If the anchor token itself ends with `-f`/`-b`/…, the label is taken from the token.
- **fbpi fallback:** if the stem does not match, banner text uses the fbpi side label (Front/Back) for that slot.

Markers elsewhere in the stem (e.g. `-S-` in an Item SKU tail) are **ignored**.

Examples: base `202-3246136-6506730-13`, stem `…-13-F-98765PER-…` → **Front**; token `103671LG-f`, stem `103671LG-f` → **Front**; base `026-…-0013102`, stem `026-…-0013102-161890LG-M-T-FUC-S-YES` → no label.

**Where it draws:** white bold text in the **black banner** rectangles — the same grid as position-banner columns for logo slots (1st/2nd logo → first banner row, cols above those logo columns; 3rd–5th → second banner row). If the **apparel** file’s stem matches, the label is drawn in the **black strip above the apparel** cell (first banner row, column above apparel). Each used cell is filled **black** again before text so the label stays on the black band.

**Toggle:** set `LOGO_FILENAME_SUFFIX_LABEL_STEP_ENABLED` to `False` in that module to disable without removing the call.

**Logging:** when `pdf_asset_log` is set (e.g. pipeline/GUI), each drawn suffix label emits a short line containing `suffix banner label` and the file name.

### Back print reference in logo grid (`-b` / `-b-` filenames)

When a **resolved logo file** for a logo slot (1st–5th) has **Back** immediately after that slot’s Logo/Design Image anchor (same anchored rules as suffix **Back** above), step 8 also draws the bundled reference image **`assets/Back Print.jpg`** (“print in the back” mockup) beside that logo in the grey logo grid.

**Trigger:** the reference is pasted when the resolved file stem has **Back** after the anchor (same rules as above), **or** the slot is the fbpi **Back** image (via `logo_filename_indicates_back` in [`back_print_hint.py`](../../scripts/pipeline_generate_packing_list_pdf/back_print_hint.py)), **or** the raw **Position** column has no `/` and that slot's position token (same source as position banners — raw Position or Position Code workbook lookup) contains **Back** case-insensitively. Slash positions (e.g. `Pocket / Back`) do not trigger from position text alone; filename/fbpi rules still apply.

**Layout:**

| Logo slot | Reference placement |
|-----------|---------------------|
| 1st (top row, col above logo 1) | **Next column** — 2nd logo cell — when that cell has no logo of its own |
| 2nd (top row, right) | No column to the right → **split cell** (logo left half, reference right half) |
| 3rd–4th (bottom row) | **Next column** when the neighbour slot is empty |
| 5th (bottom-right) | No column to the right → **split cell** |

- In **next-column** mode, the back logo uses the **full** logo cell; the reference uses the **full** adjacent cell.
- In **split-cell** fallback, each half is half the cell width.
- A **red outline** is drawn around the back logo cell and around the reference cell (when the reference is drawn).
- If `assets/Back Print.jpg` is missing, the back logo still draws with a red outline; a `pdf_asset_log` line notes the missing reference.

**Code:** [`draw_page_apparel_and_logos.py`](../../scripts/pipeline_generate_packing_list_pdf/draw_page_apparel_and_logos.py) (`draw_logo_square_rows_impl`); asset path constant `BACK_PRINT_REFERENCE_IMAGE` in [`runtime_config.py`](../../scripts/pipeline_generate_packing_list_pdf/runtime_config.py). This pass is independent of the optional suffix **banner** labels (which still run for **Customise = Yes** on any `-f`/`-b`/… filename).

If no image dirs are given, or a lookup fails, the slot shows text or a placeholder (e.g. red "A" or "L").

To keep PDF size reasonable, images are **resized and recompressed** before embedding:

- Images are scaled to fit within their display boxes at a target DPI (currently 150 DPI) while preserving aspect ratio.
- Non-transparent images are written as JPEG (quality ~85); images with transparency are written as PNG.
- The resized image data is then embedded in the PDF, so large source images do not bloat the file size.

**Performance:** The pipeline builds **stem maps** (one scan per image directory) before generating PDFs and passes them into the PDF script so each page uses O(1) lookups instead of scanning the filesystem. Indexing uses a single `os.scandir` / `os.walk` pass, plus an **in-process memory cache** and an **on-disk cache** under `.cache/image_stem_maps/` (or `%LOCALAPPDATA%/PackingListApp/cache/image_stem_maps/` for frozen builds). Disk entries are keyed by folder path + recursive flag and invalidated when the folder’s `mtime` changes. If Google Drive does not bump folder mtime when files are added, delete `.cache/image_stem_maps/` to force a rescan. Font metrics are cached for vertical text centering. When there are multiple step-6 CSVs, the pipeline can generate PDFs in parallel (multiple processes).

**Multi-file GUI batches:** When the Packing List App runs **more than one** input CSV or ShipStation tag, it finishes **all Excel (steps 1–7)** first, then runs **all PDFs (step 8)**. A single input still runs the full pipeline in one pass. Stem-map memory caching means the heavy image-folder index typically runs once for the whole PDF pass.
## Where it fits

Pipeline step **8 (Export)**. Consumes step-6 CSVs from the run folder (typically `Output/DD-MM-YYYY/{Shift} Shift/{token}/`). Produces one PDF per CSV in the same directory (or specified output directory). When running the full pipeline, this runs after [split_by_process_and_item_number.py](split_by_process_and_item_number.md) and after [generate_excel_outputs.py](generate_excel_outputs.md), so Excel workbooks are generated first and PDFs last.
