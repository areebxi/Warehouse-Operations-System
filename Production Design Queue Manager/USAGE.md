# Queue App — Usage Guide

A practical guide for day-to-day use of **Queue App**: arranging design images on a printable canvas from DTF Des order files.

For technical architecture, API details, and change history, see [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md).

---

## Table of Contents

1. [What Queue App Does](#what-queue-app-does)
2. [Quick Start](#quick-start)
3. [Before You Begin](#before-you-begin)
4. [Application Layout](#application-layout)
5. [First-Time Setup](#first-time-setup)
6. [Choosing a Processing Mode](#choosing-a-processing-mode)
7. [Normal Mode](#normal-mode)
8. [Personalised Mode](#personalised-mode)
9. [Missing Logo Mode](#missing-logo-mode)
10. [Design File Naming](#design-file-naming)
11. [Configuration Workbook](#configuration-workbook)
12. [Canvas Settings](#canvas-settings)
13. [Preview and Save](#preview-and-save)
14. [Output Files and RAR Archives](#output-files-and-rar-archives)
15. [Logs and Diagnostics](#logs-and-diagnostics)
16. [Troubleshooting](#troubleshooting)
17. [Quick Reference](#quick-reference)

---

## What Queue App Does

Queue App reads **DTF Des** files (Excel or CSV order lists), finds matching design images in your folders, resizes them using a **Size Reference** table, and packs them onto a **print canvas** (default 570 mm × 3000 mm at 300 DPI). You preview the layout, then save high-quality PNG files (and optionally a RAR archive for upload). The 570 mm width is the usable DTF area on a 600 mm PET film after 15 mm silver hold plates on each side — see [Canvas Settings](#canvas-settings).

**Typical workflow:**

1. Select your input file or folder.
2. Select the design folder(s) for your mode.
3. Click a processing button (**Normal**, **Personalised**, or **Missing Logo**).
4. Review the preview.
5. Click **Save PNG(s)**.

---

## Quick Start

### Windows (recommended)

1. Double-click **`run_queue_app.bat`** in the project root  
   (or in PowerShell: `.\run_queue_app.bat`; in CMD: `run_queue_app.bat`).
2. The script checks Python, installs dependencies from `requirements.txt`, then starts the GUI with **`pythonw`** (no black CMD window stays open with the app).
3. The setup window closes after launch; only the Queue App window remains.

### Manual launch

```bash
pip install -r requirements.txt
pythonw queue_app.py
```

Use `python queue_app.py` only if you want a visible console for live print output (debug). Normal use should prefer `run_queue_app.bat` or `pythonw`.

The window opens **maximized**. Paths you select are saved automatically in `config/queue_app_settings.json` for the next session. All run output is still written to **`Logs/`** either way.

---

## Before You Begin

### System requirements

| Requirement | Details |
|-------------|---------|
| Python | 3.7 or higher |
| Packages | `pandas`, `openpyxl`, `Pillow` (see `requirements.txt`) |
| Optional | WinRAR or 7-Zip (for automatic RAR creation) |

### Files you need in the app folder

| Item | Location | Purpose |
|------|----------|---------|
| **Configuration Workbook.xlsx** | `config/` | Size Reference (Sheet 1) + Pocket Design IDs (Sheet 2) — loaded automatically |
| **Color Bar** (optional) | `config/` | `Color Bar.png` (or `ColorBar.png`, etc.) — added to the right side of each output PNG |

### DTF Des input format

DTF Des files are `.xlsx`, `.xls`, or `.csv` worksheets with order data. Expected columns include:

- **Order - Number**
- **Item - Qty**
- **Item - SKU**
- **Item - Name**
- **Ship To - Name**
- (and other standard order columns)

**Column requirements by mode:**

| Mode | Required columns |
|------|------------------|
| Normal | A column containing **SKU** (e.g. `Item - SKU`) |
| Personalised | **Order - Number** (or similar) + **Item - SKU** |
| Missing Logo | **Order - Number** + **Item - SKU** |

### Supported design image formats

`.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`, `.tif`

---

## Application Layout

The window has a **scrollable left panel** (controls) and a **right panel** titled **Preview**. Controls use a lightweight built-in theme (teal accent actions, muted empty-state labels); no extra GUI packages are required.

### Left panel — main sections (top to bottom)

| Section | Purpose |
|---------|---------|
| **Actions** | **Normal**, **Personalised**, **Missing Logo** (primary); **Save PNG(s)**; **Clear Preview** |
| **Stats label** | Design / batch count (default: *No designs loaded*) |
| **Progress** | Progress bar and status text (default: *Ready*) |
| **Input File / Folder** | Select DTF Des File or Select Input Folder |
| **Normal Designs Folder** | Standard (Normal mode) design library |
| **Single Designs Folder (Personalised)** | Personalised single designs |
| **Double Designs Folder (Personalised)** | Personalised double designs |
| **DTF Queues Folder** | Select or Remove DTF Queues Folder (RAR upload destination) |
| **Canvas Information** | Canvas Size readout; Width (mm), Height (mm), DPI (for printing) |

### Right panel — Preview

| Control | Action |
|---------|--------|
| **Mouse wheel** | Scroll vertically |
| **Shift + mouse wheel** | Scroll horizontally |
| **Scrollbars** | Pan across the full canvas (all designs / batches) |

Multi-batch layouts show a **Batch n / total** label on each batch in the preview. Each design shows its identifier (SKU / order label) in **black** above the design, with a **black** outline around the design box.

---

## First-Time Setup

1. **Place Configuration Workbook** in `config/Configuration Workbook.xlsx` (see [Configuration Workbook](#configuration-workbook)).
2. **Optional:** Add `Color Bar.png` to `config/`.
3. **Launch** the app (`run_queue_app.bat` or `pythonw queue_app.py`).
4. **Select paths** (each is remembered for next time):
   - **Select DTF Des File** or **Select Input Folder**
   - **Select Normal Designs Folder** (and **Select Single Designs Folder** / **Select Double Designs Folder** if using Personalised or Missing Logo)
   - **Select DTF Queues Folder** (optional — for RAR copy after save)
5. Process and save once to confirm folders and output.

Settings are stored in:

```
config/queue_app_settings.json
```

---

## Choosing a Processing Mode

Use this table to pick the right button:

| Your situation | Use this mode |
|----------------|---------------|
| Designs are named by **SKU / design code** in one shared folder | **Normal** |
| Designs are named by **order number** in Single/Double folders | **Personalised** |
| Some orders are personalised, some are standard — you are not sure where files live | **Missing Logo** |
| SKU contains `plainlg` (case-insensitive) | Row is **skipped** (no design search, no missing-design warning) in all modes |

---

## Normal Mode

Matches designs from the **Normal Designs Folder** using the **Item SKU** column. Size comes from the Size Reference sheet.

### Single file

1. **Select DTF Des File** → choose your `.xlsx` / `.xls` / `.csv`.
2. **Select Normal Designs Folder** → folder containing design PNGs/JPGs.
3. *(Optional)* **Select DTF Queues Folder** for RAR upload after save.
4. Click **Normal**.
5. Watch the progress bar; review the preview.
6. Click **Save PNG(s)**.

**What happens during processing:**

- Reads each row’s SKU.
- Finds design files (with smart size-prefix fallback — see [Design File Naming](#design-file-naming)).
- Extracts a size code and looks up dimensions in Size Reference.
- Resizes and packs designs on the canvas (splits into multiple batches if taller than canvas height).

### Folder of files

1. **Select Input Folder** instead of a single file.
2. **Select Normal Designs Folder** (and optional DTF Queues folder).
3. Click **Normal**.
4. Preview shows a **combined** layout; each source file is tracked separately for saving.
5. **Save PNG(s)** → one PNG set per input file, with correct labels on each.

---

## Personalised Mode

Uses **Order Number** to find files in the **Single Designs Folder (Personalised)** and **Double Designs Folder (Personalised)**, and **Item SKU** for sizing (except double designs — see below).

### Single file

1. **Select DTF Des File**.
2. **Select Single Designs Folder** and **Select Double Designs Folder**.
3. Click **Personalised**.
4. **Save PNG(s)**.

**Search order (VBA logic):**

1. **Single** designs first (including pocket `-P` and sleeve `-S` variants).
2. Then **Double** designs from the double folder.

**Sizing rules:**

| Design type | Sizing |
|-------------|--------|
| Single (regular) | Size Reference from Item SKU |
| Single pocket (`-P.png`) | Kids (`-K-`): 65×80 mm; Men’s/Women’s (`-M-` / `-W-`): 80×100 mm |
| Single sleeve (`-S.png`) | 100×100 mm |
| Double | Original image size; scaled down only if wider than canvas (padding preserved) |

### Folder of files

Same as single file, but use **Select Input Folder**. Each file is processed; preview combines all designs; save produces separate PNGs per input file.

---

## Missing Logo Mode

For orders where designs might be in **personalised** folders **or** the standard designs folder.

### Single file

1. **Select DTF Des File**.
2. Select **at least one** of:
   - **Select Single Designs Folder**
   - **Select Double Designs Folder**
   - **Select Normal Designs Folder** (standard)
3. Click **Missing Logo**.
4. **Save PNG(s)**.

**Search order per row:**

1. Personalised folders (order number + VBA logic, pocket/sleeve variants).
2. If not found → standard **Normal Designs Folder** (design ID from SKU).

Sizing follows where the file was found (personalised rules vs standard Size Reference).

### Folder of files

1. **Select Input Folder**.
2. Select the same folder set as above.
3. Click **Missing Logo** → **Save PNG(s)**.

In folder preview, **each input file starts a new batch** so you can tell batches apart visually.

---

## Design File Naming

### Normal (standard folder)

| Rule | Example |
|------|---------|
| Match by full SKU or design code (text before first `-`) | SKU `77989LG-M-T-BLK-M` → `77989LG.png` or full SKU filename |
| Case-insensitive | `77989lg.png` matches |
| Apparel size prefix fallback | SKU `XL39553LG-...` tries `XL39553LG.png`, then `39553LG.png` |
| Multi-position rows | `{DesignCode}-{Position}.png` e.g. `123LG-x93.png` |
| Skip | Rows with `plainlg` in SKU are skipped |

Supported size prefixes for fallback: XS, S, M, L, XL, 2XL, 3XL, 4XL, XXL, XXXL, XXXXL.

### Personalised (single / double folders)

| Case | Filename pattern |
|------|------------------|
| Normal order | `{OrderNumber}.png` |
| Pocket (checked first) | `{OrderNumber}-P.png` |
| Sleeve (checked first) | `{OrderNumber}-S.png` |
| Duplicate orders | `{OrderNumber}-{itemSku}.png` or `{OrderNumber}-{index}-{itemSku}.png` |
| Multi-position | `{OrderNumber}-{Position}.png` |

**Duplicate orders:** When the same order number appears on multiple rows, the app uses SKU-based filenames; `/` and `\` in SKUs are converted to `-`.

**Double designs:** Same naming rules; app searches **single folder first**, then **double folder**.

---

## Configuration Workbook

**File:** `config/Configuration Workbook.xlsx`  
Loaded automatically on startup — no button required.

### Sheet 1 — Size References

| Column / field | Purpose |
|----------------|---------|
| **Size Width** / **Size Height** | Dimensions in mm |
| **SKU Value** (was Merge) | Size codes: `M-T`, `K-SS (YS) (YXS)`, etc. |
| **Number of Designs** (was Number of Positions) | Blank/`1` = single design; `2`–`5` = multi-design |
| **Suffix** (was Position) | File-search suffix (e.g. `F`, `B`, `x93`) |

**Bracket codes:** Entries like `K-SS (YS) (YXS)` match SKUs via bracket tokens first (when the base code is in the SKU), then bare base codes. Matching is token-based (e.g. `YS` does not match inside `YXS`). Leading-dash apparel sizes such as `(-S)` / `(-2XL)` match hyphen tokens in the SKU. If a base has both bracketed rows and a dedicated bare row (e.g. `K-H` and `K-H (YS) (YXS)`), SKUs with the base but no matching bracket still use the bare row.

### Sheet — Override Print Size

| Column | Purpose |
|--------|---------|
| **SKU Contain** | If the item SKU contains this value, apply the override |
| **Width** / **Height** | Print size in mm (e.g. `62310LG` → 80×100) |

When Width/Height are blank on a matching row, the app falls back to the old pocket sizes: **65×80** (kids `-K-`) or **80×100** (otherwise).

---

## Canvas Settings

### Why the default width is 570 mm (printing machine)

Saved PNGs are printed on the DTF/PET film on our printing machine. Keep this layout in mind when changing canvas width:

| Part | Width |
|------|-------|
| Full PET / DTF film | **600 mm** |
| Silver holding plate (each side) | **15 mm** × 2 |
| **Usable print width (app default)** | **570 mm** (600 − 15 − 15) |

The silver plates on the left and right hold the DTF film in place, so designs must stay within the **570 mm** usable area. Do not set canvas width to the full 600 mm film size unless the machine setup changes.

Adjust in the **Canvas Information** panel (shows a **Canvas Size:** readout plus spinboxes):

| Setting | UI label | Default | Range |
|---------|----------|---------|-------|
| Width | **Width (mm):** | 570 mm | 100–2000 mm |
| Height | **Height (mm):** | 3000 mm | 100–10000 mm |
| DPI | **DPI:** *(for printing)* | 300 | 72–600 |

**Important:** Changing width, height, or DPI requires clicking **Normal** (or the mode you used) again — existing previews do not update automatically. Unchanged values do not show a rearrange prompt.

Designs are packed left-to-right with fixed gaps (~**8 mm** between designs, ~**2 mm** left/start, ~**15 mm** between rows). A **color bar** (if present in `config/`) is reserved on the right (~**12 mm** gap + bar width ≈ **5 mm**) so designs never overlap it. Leftover row width stays toward the color bar.

**Packing orientation (automatic):** after sizing, wide (landscape) designs may be rotated to portrait so more fit on a row, then rotated back to landscape on a finished row if spare width allows. A design that already nearly fills the row as landscape (under ~200 mm free) and cannot share that row with the next logo is left landscape. **A3** designs follow the separate A3 landscape rule and are not rotated by this packing pass.

---

## Preview and Save

### After processing

- The **stats label** under the action buttons updates (e.g. *Arranged N designs on canvas*, or with batch/file counts).
- Multiple **batches** appear side by side in **Preview** (with spacing and **Batch n / total** labels).
- Preview shows **all** arranged designs (no on-screen design cap). Scale fits roughly one batch width at **47.5%** of fit-width (`DEFAULT_PREVIEW_ZOOM`); use scrollbars or the mouse wheel to pan.
- Each design has a **black** outline and a **black** identifier label above it (when the preview box is large enough).
- Preview background is cool grey so white designs stay visible.

### Saving

| Button | When to use |
|--------|-------------|
| **Save PNG(s)** | Write PNG(s) to `Output/YYYY-MM-DD/` and create RAR if tools are installed (runs in the background so the window stays responsive) |
| **Clear Preview** | Clear the preview canvas without deleting saved files |

After arrange, there is **no** success popup — use the stats label and preview. Save still shows success/error dialogs when finished.

### Progress during save

The progress bar and label update per batch/file and during RAR creation. If a save is already running, a short “Save in progress” message appears instead of starting a second save.

---

## Output Files and RAR Archives

### PNG files

| Item | Detail |
|------|--------|
| **Location** | `Output/YYYY-MM-DD/` (date folder created next to the app under `Output/`) |
| **Format** | PNG at current DPI (default 300) |
| **Single batch** | `{input_basename}.png` |
| **Multiple batches** | `{input_basename}_Part {N}.png` |
| **Folder processing** | Separate PNG set per input file |
| **Header text** | Text after `des-` in the source filename + part number if applicable |

### RAR archives

After saving PNGs, the app can:

1. Create a RAR (WinRAR preferred) or 7z (7-Zip fallback) in `Output/YYYY-MM-DD/`.
2. Copy it to **DTF Queues Folder** if configured.

**RAR naming examples:**

- Single file: `P200.rar`
- Multiple files: `P200-P211.rar` or `P200-P211-P300-and-5-more.rar`

Use **Remove DTF Queues Folder** to stop copying without changing other settings.

### Missing size reference export

Rows without a matching size in Size Reference are exported automatically to:

```
Missing Size Reference/{original_filename} (YYYY-MM-DD_HH-MM-SS).xlsx
```

Example: `DTF Des 100 (2026-07-14_18-07-00).xlsx`
**Recommended workflow:**

1. Process your file(s).
2. Open the export in `Missing Size Reference/`.
3. Add missing codes to Configuration Workbook → Size References → Merge column.
4. Reload the export in Queue App and process again.

---

## Logs and Diagnostics

Each run writes diagnostics under a single **`Logs/`** folder in the app directory:

| File pattern | Contents |
|--------------|----------|
| **`console_log_YYYY-MM-DD_HH-MM-SS.txt`** | Full run log (all stdout/stderr for that run, human-readable timestamps/events, plus end-of-run summary). Errors and warnings appear here — there are no separate error files. |
| **`(input stem) size_determination_YYYY-MM-DD_HH-MM-SS.txt`** | Per-design size reference decisions (order number, SKU, size reference taken, final dimensions, SUMMARY). One file per DTF Des when processing a folder. |

Related (not run logs):

| Folder | Contents |
|--------|----------|
| **`Missing Size Reference/`** | Exported rows with missing size codes (project root, next to `Output/` and `Logs/`) |
| **`Output/YYYY-MM-DD/`** | PNG and RAR files (one subfolder per day) |

When you start via **`run_queue_app.bat`** / **`pythonw`**, there is no live CMD mirror — open the latest `console_log_*.txt` in **`Logs/`** to see the same detail that used to appear in the console. If you start with **`python queue_app.py`**, output is written to both the console and the log file.

Check **`Logs/`** first for both the full trace and size-matching decisions.

Run events in the console log are written as plain sentences (e.g. `Processing started — mode: personalised, file path: …`), including GUI theme, processing start/complete, preview drawn, and save completed/failed (`save_completed` includes `duration_ms`). Packing orientation passes do not write separate log lines; size determination logs reflect pre-pack resize sizes.

---

## Troubleshooting

### “No SKU column found”

Ensure the DTF Des file has a column named **Item - SKU** or containing **SKU**.

### “Could not find size reference” / wrong sizes

- Add or fix the size code in **Merge** (Column I) of Configuration Workbook.
- For pocket designs: verify design ID is in Sheet 2 and SKU has `-M-`/`-W-`/`-K-` and `-T-`/`-H-`.
- Re-process after updating; use the **Missing Size Reference** export to catch all bad rows.

### Design not found

| Mode | Check |
|------|--------|
| Normal | File in Normal Designs Folder; name matches design code or SKU; try without size prefix |
| Personalised | `{OrderNumber}.png` in Single/Double Designs Folders; `-P`/`-S` variants if applicable |
| Missing Logo | Personalised folders first, then Normal Designs Folder |
| All modes | `plainlg` in SKU → row intentionally skipped |

### Preview empty but processing seemed OK

- Scroll the preview area (mouse wheel or scrollbars); tall or multi-batch layouts may start off-screen.
- Check the stats label for design count.
- Look in **`Logs/`** for preview/processing messages or errors.

### RAR not created

- Install **WinRAR** or **7-Zip**.
- Confirm write access to `Output/`.
- Read **`Logs/`** (`console_log_*.txt`) for details.

### Designs wrong size on canvas

- Verify Size Reference dimensions and Merge codes.
- Re-run processing after changing canvas size or DPI.
- Check `Logs/` for size-matching messages.

### Permission / Output folder errors

- Ensure disk space and write permission in the app folder.
- On Windows, try running as administrator only if needed.

### `WARNING: Ignoring invalid distribution ~ip` on launch

- Harmless to the app if dependencies still install and the GUI opens; it comes from **pip**, not Queue App.
- Usually left behind after an interrupted pip upgrade (`~ip` / `~ip-*.dist-info` junk in site-packages).
- Close Python/the app, delete any `~...` leftovers in your user `site-packages` folder, then run `.\run_queue_app.bat` again.
- Optional: `python -m pip check` should report no broken requirements.

---

## Quick Reference

### Buttons

| Button | Action |
|--------|--------|
| **Select DTF Des File** | One input worksheet |
| **Select Input Folder** | Many input worksheets |
| **Select Normal Designs Folder** | Standard design library |
| **Select Single Designs Folder** | Personalised single designs |
| **Select Double Designs Folder** | Personalised double designs |
| **Select DTF Queues Folder** | RAR copy destination |
| **Remove DTF Queues Folder** | Disable RAR copy |
| **Normal** | Process by SKU |
| **Personalised** | Process by order number |
| **Missing Logo** | Personalised first, then standard |
| **Save PNG(s)** | Export PNG + RAR |
| **Clear Preview** | Clear preview only |

### Mode vs folders vs columns

| Mode | Input | Folders | Key columns |
|------|-------|---------|-------------|
| Normal | File or folder | Normal Designs Folder | Item SKU |
| Personalised | File or folder | Single Designs Folder + Double Designs Folder | Order Number, Item SKU |
| Missing Logo | File or folder | Single and/or Double and/or Normal Designs Folder | Order Number, Item SKU |

### Auto-created folders

```
Output/
  YYYY-MM-DD/            # PNG and RAR files for that day
Logs/                    # console_log_*.txt and *size_determination_*.txt
Missing Size Reference/
```

---

**See also:** [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md) — full feature list, technical details, and change log.

**Last updated:** July 23, 2026
