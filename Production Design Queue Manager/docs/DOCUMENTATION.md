# Queue App - Canvas Layout Tool Documentation

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [Recent Changes](#recent-changes)
4. [Installation & Setup](#installation--setup)
5. [User Guide](#user-guide)
6. [Technical Details](#technical-details)
7. [File Structure](#file-structure)
8. [Troubleshooting](#troubleshooting)

---

## Overview

**Queue App** is a Python-based GUI application designed to automatically arrange design images on a canvas for printing. The tool processes DTF Des files containing SKU information, matches designs from specified folders, and arranges them optimally on a canvas with proper sizing based on a size reference file.

### Key Capabilities
- Process single DTF Des files or entire folders with SKU data
- Match design images to SKUs automatically
- Arrange designs on a printable canvas (570mm × 3000mm)
- Support for three processing modes: "Normal", "Personalised", and "Missing Logo"
- Automatic size detection and resizing based on reference file
- Generate high-quality PNG output files (300 DPI)
- Preview all arranged designs on a scrollable canvas (fixed readable scale; grey background for white designs)
- Process multiple files with combined preview and separate saves
- Automatically export rows with missing size references for easy reprocessing
- Detailed size determination logging under `Logs/` for traceability and debugging (single-file and folder processing in all three modes; one size log per DTF Des file when processing a folder)

---

## Features

### 1. File Management
- **Input File/Folder Selection**: Load single DTF Des files (.xlsx, .xls, .csv) or select a folder containing multiple DTF Des files
- **Configuration Workbook**: Single Excel file containing both Size Reference and Pocket Design IDs Database
  - **File Name**: `Configuration Workbook.xlsx`
  - **Location**: `config/` directory
  - **Sheet "Size References" (or Sheet 1)**: Contains size dimensions (width/height in mm) and merge text
    - **Auto-Load**: Automatically loaded on application startup
    - **Format**: Standard size reference format with Merge / SKU Value column
    - **Bracket Support**: Merge column can include bracket codes for flexible matching
      - Format: `BaseCode (BracketCode1) (BracketCode2)` or `BaseCode (BracketCode)`
      - Examples: `K-SS (YS) (YXS)`, `W115 (S)`, `M-T (XS) (S)`, `M-T (-S)`, `M-T (-2XL)`
      - SKUs can match against base code or any bracket code
      - Leading-dash apparel brackets (`-S`, `-2XL`, `-1-2Y`) match consecutive hyphen tokens (not only the final token), ignoring trailing Yes/No flags
    - **Merge_clean Column**: Automatically created with base code (text before brackets)
    - **Merge_brackets Column**: Automatically created with list of bracket codes
    - **Number of Designs** (was Number of Positions): Blank/`1` = single design; `2`–`5` = multi-design (Suffix / Position column supplies the file-search stem)
    - **No Manual Selection**: Size reference is auto-loaded, no GUI button needed
  - **Sheet "Override Print Size"** (optional): SKU Contain + Width/Height overrides applied when the item SKU contains the token; blank Width/Height fall back to pocket sizes (65×80 kids `-K-`, else 80×100)
  - **Sheet "Pocket Design IDs Database" (or Sheet 2)**: Contains design IDs for pocket designs
    - **Auto-Load**: Automatically loaded on application startup
    - **Format**: Design IDs in column A (first column)
    - **Purpose**: Used to identify pocket designs and generate F8-based size codes
- **Designs Folder**: Select folder containing design image files
- **Single/Double Design Folders**: Separate folders for personalised processing (single and double designs)
- **DTF Queues Folder**: Select folder for automatic RAR file upload (optional)
  - "Select DTF Queues Folder" button: Choose folder for RAR file upload
  - "Remove DTF Queues Folder" button: Clear folder selection to prevent files from being sent to DTF Queues folder
- **Auto-save Settings**: All selections are automatically saved and restored on next launch
- **Folder Processing**: Process all DTF Des files in a folder with combined preview and separate output files

### 2. Processing Modes

#### Normal Mode
- Processes standard SKU-based designs
- Auto-detects Item SKU column from input file
- Matches design files by SKU from designs folder
- **Smart Design Matching**: Automatically handles apparel size prefixes in SKUs
  - If design file not found with full design code (e.g., `XL39553LG`), removes size prefix and searches again (e.g., `39553LG`)
  - Prevents false "design not found" warnings
- Extracts size codes from SKU and matches with size reference
- **Multi-Position Support** (from Size References):
  - If `Number of Designs` (was Number of Positions) is blank/`1`, standard single-design flow is used
  - If `Number of Designs` is `2`/`3`/`4`/`5`, multiple designs are searched for the same row
  - Search stem format: `{DesignCode}-{Suffix}` / `{DesignCode}-{Position}` (example: `123LG-x93`, `123LG-x94`)
  - Each position row uses its own width/height values for resizing
- **PLAINLG Skip Rule**:
  - If Item SKU contains `plainlg` (case-insensitive), design search is skipped
  - Skipped rows are not reported as missing designs
- Arranges designs on canvas with proper sizing

#### Personalised Mode
- Processes orders with single and double designs
- Uses Order Number column to find design files
- Uses Item SKU column for size reference matching
- Follows VBA logic: Single first (with variations), then Double
- Supports single, single-pocket, single-sleeve, and double design types
- Each file is used only once
- **Pocket & Sleeve Variant Detection**: Automatically detects and processes pocket (-P.png) and sleeve (-S.png) variants
  - Checks for `{OrderNumber}-P.png` (pocket) or `{OrderNumber}-S.png` (sleeve) before regular `.png` files
  - Case-insensitive matching (e.g., `-p.png`, `-P.png`, `-s.png`, `-S.png`)
  - Pocket variants: Override target dimensions based on SKU pattern
    - Kids (-K- in SKU): 65mm width × 80mm height
    - Men's/Women's (-M- or -W- in SKU): 80mm width × 100mm height
  - Sleeve variants: Override to 100mm × 100mm for all sizes regardless of SKU
  - Dimension overrides applied after calculating aspect ratio but before resizing
  - Resizing uses orientation-based strategy: width constraint if image is wider than tall, height constraint otherwise
- **Double Design Sizing**: Double design folder images use original image dimensions (no size reference rules applied)
  - Automatically scaled down if width exceeds canvas width (with padding preserved)
- **Single Design Sizing**: Single design folder images use size reference rules for proper sizing (or pocket/sleeve overrides if detected)
- **Multi-Position Support** (from Size References):
  - If `Number of Designs` (was Number of Positions) is blank/`1`, normal personalised search is used
  - If `Number of Designs` is `2`/`3`/`4`/`5`, multiple designs are searched
  - Search stem format: `{OrderNumber}-{Suffix}` / `{OrderNumber}-{Position}` (example: `17-14324-96700-x93`)
  - Each position row uses its own width/height values for resizing
- **PLAINLG Skip Rule**:
  - If Item SKU contains `plainlg` (case-insensitive), design search is skipped
  - Skipped rows are not reported as missing designs

#### Missing Logo Mode
- **Dual Search Strategy**: Searches both personalized and standard design folders
  - **Step 1**: First searches personalized folders (Single/Double Design Folders) using Order Number and VBA logic
  - **Step 2**: If not found in personalized folders, falls back to "Normal" folder using design ID extracted from SKU
- **Column Requirements**:
  - **Order Number column**: Used for finding design files in personalized folders (VBA logic with duplicate index support)
  - **Item SKU column**: Used for finding design files in Normal Designs folder and for size reference matching
- **Processing Logic**:
  - Uses personalized search method (order ID, duplicate index, pocket/sleeve variants) when searching personalized folders
  - Uses standard search method (design ID from SKU, smart matching) when searching Normal Designs folder
  - Supports all personalized design types (single, single-pocket, single-sleeve, double) when found in personalized folders
  - Applies appropriate sizing rules based on where the design was found:
    - **From personalized folders**: Uses personalized sizing rules (size reference, pocket/sleeve overrides, double design scaling)
    - **From Normal Designs folder**: Uses standard sizing rules (size reference only)
- **Multi-Position Support**:
  - Uses the same Size References `Number of Designs` + Suffix/`Position` logic as other modes
  - Personalized step uses `{OrderNumber}-{Suffix}`
  - Fallback standard step uses `{DesignCode}-{Suffix}`
  - Each position row uses its own width/height values for resizing
- **PLAINLG Skip Rule**:
  - If Item SKU contains `plainlg` (case-insensitive), row is skipped
  - Skipped rows are not reported as missing designs
- **Use Cases**:
  - When design locations are uncertain (might be in personalized or standard folders)
  - When processing orders that may have some designs in personalized folders and others in standard folder
  - Reduces need for manual intervention when design locations vary
- **Works with Folder Processing**: Can process multiple DTF Des files in a folder using Missing Logo mode
- **Output**: Same as other modes - generates PNG files with proper labels and supports batch processing

### 3. Size Code Extraction
- **Intelligent Size Detection**: Extracts size codes from SKU strings
- **Reference File Matching**: Gets all size codes from Merge column (Column I) of size reference file
- **Bracket Code Support (Bracket-First, Scoped by Base Code, Token-Based Matching)**: Matches SKUs against both bracket codes and base codes, **checking bracket codes first**, but **only for rows whose base code is present in the SKU**. Bracket codes match **whole tokens** only (e.g., `YS` does not match inside `YXS`).
  - Base codes: Text before brackets (e.g., `K-SS` from `K-SS (YS) (YXS)`)
  - Bracket codes: Codes in parentheses (e.g., `YS`, `YXS` from `K-SS (YS) (YXS)`)
  - **Scoping Rule**:
    - Bracket codes are evaluated **per base code row**. A row’s bracket codes are considered only when the SKU also contains that row’s base code (`Merge_clean`).
  - **Priority Order**:
    - 1) For each row whose base code appears in the SKU, bracket codes in that row are checked first using whole-token matching. If any bracket code token in the SKU matches an entry in `Merge_brackets`, that row is selected and its bracket code is used as the size code.
    - 2) If no bracket code matches, fall back to bare `Merge_clean` bases that are **not** bracket-required (so codes like `A4` can still win).
    - 3) If still no hit, allow a bracket-required base that also has a **dedicated bracket-free row** (e.g. bare `K-H` alongside `K-H (YS) (YXS)`), so SKUs like `…-K-H-…-YL` resolve to `K-H` instead of a false missing-size warning.
  - Examples:
    - SKU `121913LG-K-SS-LPNK-YXS` matches `K-SS (YS) (YXS)` via bracket code `YXS` (bracket match takes priority because SKU contains both `K-SS` and token `YXS`).
    - SKU `128968LG-W115-BLK-S-Yes` matches `W115 (S)` via bracket code `S` (SKU contains `W115` and `S`).
    - SKU `88892LG-K-T-LPNK-YS` with rows `K-T` and `K-SS (YS) (YXS)` matches `K-T` as the size code: the `YS` bracket belongs to base code `K-SS`, and since `K-SS` is not in the SKU, those brackets are ignored.
    - SKU `120457LG-K-H-LPNK-Y2XL` with merge entry `K-H (YS) (YXS)` matches via bracket code `Y2XL` if present, or falls back to base code `K-H`; `YS` will not match inside `Y2XL` because matching is token-based.
    - SKU `121122LG-K-H-DHR-YL` with both bare `K-H` and `K-H (YS) (YXS)` rows matches bare `K-H` (no `YS`/`YXS` token present).
- **Smart Matching Order for Base Codes**: When falling back to base codes, size codes are sorted by length (longest first) to ensure more specific codes match before shorter ones.
  - Example: `F8-M-T` will match before `F8` if both exist in the reference file.
  - Prevents shorter codes from incorrectly matching when longer, more specific codes are present.
- **Pocket Design ID Database**: Automatic detection of pocket designs based on design ID database
  - **Database Location**: Configuration Workbook.xlsx, sheet "Pocket Design IDs Database" or Sheet 2 (auto-loaded from config/ directory)
  - **Database Format**: Design IDs stored in column A (first column)
  - **Detection Logic**: When a design ID (extracted from SKU) is found in the database, the system automatically treats it as a pocket design
  - **F8-Based Size Codes**: For pocket designs, constructs size codes based on SKU patterns:
    - **Gender Detection**: Analyzes SKU for `-M-` (men's), `-W-` (women's), or `-K-` (kids)
    - **Type Detection**: Analyzes SKU for `-T-` (tshirt) or `-H-` (hoodie)
    - **Code Format**: `F8-{gender}-{type}` (always uppercase)
      - Examples: `F8-M-T`, `F8-W-T`, `F8-K-T`, `F8-M-H`, `F8-K-H`
    - **Error Handling**: If gender or type patterns are not found in SKU, returns `None` (results in missing size error)
  - **Apparel Size Prefix Support**: Checks both the extracted design ID and the version with apparel size prefix removed (e.g., `XL39553LG` → also checks `39553LG`)
  - **Priority**: Pocket design detection happens before normal size extraction logic
- **Pattern Matching**: Searches SKU for size codes like:
  - `M-T`, `K-T`, `W-T` (letter-letter patterns)
  - `F8-M-T`, `F8-W-T` (multi-part codes)
  - `A4`, `A5`, `A3`, `A6` (paper sizes)
  - Other custom size codes from reference file
- **Case-Insensitive**: Matching works regardless of case
- **A3 Forced Landscape**: When size code is `A3`, the design is always prepared for landscape paste on the canvas (all processing modes):
  - Source image is rotated 90° clockwise before resize
  - Size-reference width and height are swapped at runtime (~420×297 mm landscape box); the Excel size reference row stays portrait (~297×420 mm)
  - IronOn auto-orientation is disabled for A3 so it does not override this rule
  - Toggle: set `ENABLE_A3_LANDSCAPE = False` in `scripts/src/core/image_orientation.py` to restore previous behavior
  - Console log marker: `a3_landscape=forced rotate=90 size_box_swapped`
  - Size determination logs include `A3 Landscape:` and effective (swapped) reference dimensions

### 4. Canvas Arrangement
- **Canvas Dimensions**: 570mm width × 3000mm height (configurable via UI)
  - Width range: 100-2000mm (adjustable via spinbox in Canvas Information panel)
  - Height range: 100-10000mm (adjustable via spinbox in Canvas Information panel)
  - Changes require reprocessing designs to take effect
- **Why 570 mm width (printing machine reference)**:
  - Output PNGs are printed onto the DTF / PET film on the printing machine
  - Full PET / DTF film width is **600 mm**
  - A **15 mm** silver plate on each side holds the film in place (15 mm × 2 = 30 mm)
  - Usable print width = 600 − 30 = **570 mm** (app default canvas width)
  - Do not use the full 600 mm as canvas width unless the machine hold plates change
- **DPI**: 300 DPI for high-quality printing (configurable via UI)
  - DPI range: 72-600 (adjustable via spinbox in Canvas Information panel)
  - Changes require reprocessing designs to take effect
- **Smart Packing**: Automatically arranges designs to minimize wasted space (two-pass orientation for packing; see Recent Changes)
- **Batch Processing**: Automatically splits into multiple batches if designs exceed canvas height
- **Grid Layout**: Designs are placed left-to-right with a fixed gap; leftover width stays toward the color bar
- **Gaps / margins** (300 DPI constants in `size_reference.py`):
  - Between designs: ~**8 mm** (`DEFAULT_DESIGN_PADDING` = 94 px)
  - Left / start gap: ~**2 mm** (`NON_BAR_MARGIN` = 24 px)
  - Between rows / top & bottom: ~**15 mm** (`DEFAULT_VERTICAL_PADDING` = 177 px)
  - Color-bar gap: ~**12 mm** (`COLOR_BAR_SPACING` = 142 px) plus bar width (`COLOR_BAR_WIDTH` = 59 px ≈ 5 mm)
- **Color Bar Support**: Optional color bar image can be automatically loaded from application directory
  - **Location**: `config/` directory (checks config/ first, then root directory for backwards compatibility)
  - Supported filenames: `Color Bar.png`, `ColorBar.png`, `color_bar.png`, `colorbar.png`
  - Automatically loaded on application startup if found in config/ or root directory
  - Added to canvas right-aligned at the top (if available)
  - Design packing and image resizing reserve a fixed-width area on the right for the color bar (`COLOR_BAR_WIDTH + COLOR_BAR_SPACING`), so designs (including wide/double designs) never overlap it.

### 5. Output Features
- **PNG Generation**: High-quality PNG files with configurable DPI (default: 300 DPI)
- **Output Folder**: All files saved under `Output/YYYY-MM-DD/` in the application directory (one date subfolder per day)
- **Filename Format**: 
  - Single batch: `{filename}.png`
  - Multiple batches: `{filename}_Part {N}.png`
- **Top Text**: Displays text after "des-" from source filename and PART number if multiple batches
  - Each PNG file correctly displays the label from its own source file (important for folder processing)
- **Color Bar**: Optional color bar image automatically loaded from application directory
  - **Location**: `config/` directory (checks config/ first, then root directory for backwards compatibility)
  - Automatically detected and loaded on startup if present
  - Added to canvas right-aligned at the top
  - Supported filenames: `Color Bar.png`, `ColorBar.png`, `color_bar.png`, `colorbar.png`
- **Folder Processing Output**: When processing a folder, each input file generates separate PNG files with correct labels
- **RAR Archive Creation**: Automatically creates RAR archives containing all generated PNG files
  - Detects WinRAR or 7-Zip automatically
  - Smart naming based on source files
  - Automatically copies to DTF Queues folder if configured

### 6. Preview & Navigation
- **Live Preview**: Real-time preview of all arranged designs (no on-screen design cap)
- **Fixed Scale**: Fits roughly one batch width to the panel (default 47.5% of fit-width via `DEFAULT_PREVIEW_ZOOM`), then pan to explore
- **Mouse Wheel**: Scroll vertically; **Shift + mouse wheel** scrolls horizontally
- **Scrollbars**: Horizontal and vertical scrolling for large canvases and multi-batch layouts
- **Grey Background**: Preview panel and batch composites use a cool grey fill (`PREVIEW_BG` from `gui_theme`) so white designs remain visible
- **Design Labels**: Each design shows its identifier (`sku` label) in black text centered above the design when the preview box is large enough
- **Design Outlines**: Black rectangle outline around each design in the preview composite
- **Themed Chrome**: Left-panel controls use a one-shot `ttk` theme (`gui_theme.apply_theme`) with accent/secondary/quiet button styles; no third-party GUI libraries
- **Batch Composites**: Each batch is drawn as one composited preview image for faster rendering
- **Statistics**: Shows number of designs arranged and batch information
- **Visual Improvements**:
  - **Left/Right Padding**: Padding and outline allowance keep the black batch border fully visible
  - **Batch Spacing**: 200px spacing between batches provides clear visual separation
  - **File-Based Batch Separation**: When processing multiple files, each file starts on a new batch in preview
    - Example: File1 (batches 1-2) → File2 (batch 3) → File3 (batch 4)
    - Makes it easy to identify which batches belong to which file
    - PNG output remains unchanged (each file still saves separately)

### 7. Progress Tracking
- **Progress Bar**: Visual progress indicator for all long operations
- **Status Messages**: Real-time status messages for each processing stage
- **File-by-File Progress**: Progress updates when processing multiple files
- **Batch Progress**: Shows progress when saving multiple batches
- **Saving Progress**: Progress updates when saving canvas images to PNG files
  - Shows progress for each batch/file being saved
  - Shows progress during RAR archive creation
  - Displays completion status
- **Auto-Reset**: Progress bar automatically resets after operations complete

### 8. Missing Size Reference Export
- **Automatic Export**: When a design doesn't have a size reference in the reference sheet, the application automatically exports the entire row to a new DTF Des file
- **Export Location**: Files are saved in the `Missing Size Reference` folder at the application (project) root — same level as `Output/` and `Logs/`
- **Filename Format**: `{original_filename} (YYYY-MM-DD_HH-MM-SS).xlsx`
  - Uses the source DTF Des stem (e.g., `DTF Des 100`)
  - Timestamp format: `YYYY-MM-DD_HH-MM-SS` (e.g., `2026-07-14_18-07-00`)
  - Collision suffix: if the same name already exists, appends ` 2`, ` 3`, etc.
  - Example: `DTF Des 100 (2026-07-14_18-07-00).xlsx`
  - Folder processing: one export file per source DTF Des that had missing rows
- **Complete Data**: Exported files include:
  - Full header row (all column names from original DTF Des file)
  - Complete rows (all columns) for all rows with missing size references
  - All instances included (no deduplication)
- **Works with All Modes**:
  - Single file and folder processing (Normal, Personalised, Missing Logo)
  - Folder processing: combines missing rows from all files into one export
- **User Notification**: Shows messagebox with file location when missing size references are found and exported

### 9. Logging (Console + Size Determination)

All run logs live in a single **`Logs/`** folder. There are **no** separate `Errors and Warnings/` files and **no** separate `Size Determination Logs/` folder.

#### Console logs
- **Automatic**: All stdout/stderr from the run is saved to one file per app launch
- **Location**: `Logs/`
- **File Naming**: `console_log_YYYY-MM-DD_HH-MM-SS.txt`
- **Content** (human-readable):
  - Timestamped lines for plain output
  - Run events as plain sentences (e.g. `Processing started — mode: personalised, file path: …`)
  - Errors, warnings, dialogs, and unhandled exceptions (also mirrored to dialogs/UI when applicable)
  - Per-design sizing DEBUG lines (order, SKU, size reference taken, dimensions)
- **No CMD required**: When launched via `run_queue_app.bat` / `pythonw`, open the log file for the same detail
- **Summary Report** at end of each console log:
  - Application start and end times and total runtime
  - Counts of errors, warnings, exceptions, dialogs, and tracebacks
  - Overall status assessment
  - Reminder that both console and size determination logs are under `Logs/`

#### Size determination logs
- **Automatic** for single-file and folder processing in Normal, Personalised, and Missing Logo modes
- **Location**: `Logs/` (same folder as console logs)
- **File Naming**: `(input_file_stem) size_determination_YYYY-MM-DD_HH-MM-SS.txt`
  - Examples:
    - `(DTF Des-P6000283) size_determination_2026-01-28_16-50-03.txt`
    - `size_determination_2025-12-29_14-30-45.txt` (no input path)
- **Content** (human-readable): for each design — Design Type, Order Number, Item SKU, original size, Size Reference taken (merge entry, size code, match type), final size; SUMMARY with labeled counts
- **Bracketed size rows**: entries like `M261 (102722)` only match when **both** the base and the bracket token appear in the SKU; otherwise a later bare code such as `A4` can win
- **Purpose**: Traceability for size decisions during debugging and QA

#### Related export (not a log stream)
- **Missing Size Reference/** — Excel export of rows missing a size code (separate from `Logs/`)

### 10. RAR Archive Creation
- **Automatic RAR Creation**: After saving PNG files, automatically creates RAR archive containing all generated PNG files
- **RAR Tool Detection**: Automatically detects WinRAR (prioritized) or 7-Zip (fallback)
- **Smart Naming**: RAR files are named based on source files
  - Single file: `{filename}.rar`
  - Multiple files: `{file1}-{file2}-{file3}.rar` or `{file1}-{file2}-{file3}-and-N-more.rar`
- **DTF Queues Integration**: Automatically copies RAR files to selected DTF Queues folder (if configured)

---

## Recent Changes

> **Note**: All changes to the Queue App are now logged in this section. When making updates, please document them here with date, description, and technical details.

### Size Lookup: Bare-Base Fallback When Bracket Codes Do Not Match
**Date**: 2026-07-31 (helpers refined 2026-08-02)

**Change**: If a base code (e.g. `K-H`) has bracketed Size Reference rows (e.g. `K-H (YS) (YXS)`) **and** a dedicated bracket-free `K-H` row, SKUs that contain the base but **none** of the bracket tokens no longer fail size lookup.

**Details**:
- **Problem**: Bases with any bracketed siblings were marked bracket-required, so bare `K-H` was skipped. SKUs like `…-K-H-DHR-YL` (no `YS`/`YXS`) fell through to unrelated tokens (e.g. `DHR`) and produced false “missing size reference” warnings even when a bare `K-H` row existed
- **Fix** (in `_search_reference_size_codes()` in `scripts/src/core/size_code_extractor.py`):
  1. Try bracket match first (unchanged)
  2. Try bare bases that are **not** bracket-required (unchanged; keeps `A4` and similar winning when brackets do not apply)
  3. **New**: If still no hit, allow a bracket-required base that has a dedicated bracket-free row in the index (`index.by_base`) — e.g. bare `K-H` alongside `K-H (YS) (YXS)`
- **Unchanged**: When a bracket token **does** match (`YS` / `YXS`), the bracketed row is still preferred; leading-dash apparel brackets (`-S`, `-2XL`, `-1-2Y`) and Override Print Size behavior are unchanged
- **Modules**: `size_code_extractor.py`; shared resolve/override helpers in `design_processing_helpers.py`

**Logging**:
- Size determination and missing-size export now resolve these SKUs to the bare base row instead of exporting them as missing
- No new console event names

### Docs: PET / DTF Film Width Rationale (570 mm Usable)
**Date**: 2026-07-26

**Change**: Documented why the default canvas width is 570 mm for the printing machine.

**Details**:
- Full PET / DTF film width: **600 mm**
- Silver hold plate: **15 mm** on each side
- Usable print width: **570 mm** (app default) — do not set canvas width to the full 600 mm film unless the machine setup changes
- Recorded in `USAGE.md` (Canvas Settings + overview) and this file (Canvas Arrangement / Specifications)

### Canvas Gaps: Start 2 mm, Vertical 15 mm
**Date**: 2026-07-25

**Change**: Left/start gap and vertical row spacing retargeted for print layout.

**Details**:
- **Start / left gap** (`NON_BAR_MARGIN`): **24 px (~2 mm)** at 300 DPI (was 12 px / ~1 mm after the 2026-07-18 retarget; briefly tested at 35 px / ~3 mm, then set to 2 mm)
- **Between rows / top & bottom** (`DEFAULT_VERTICAL_PADDING`): **177 px (~15 mm)**
- **Unchanged**: Between designs ~8 mm (`DEFAULT_DESIGN_PADDING` = 94); color-bar gap ~12 mm (`COLOR_BAR_SPACING` = 142); color-bar width reservation 59 px (~5 mm)
- **Modules**: Constants in `scripts/src/core/size_reference.py`; placement/arranger already consume these values

**Logging**: No new events

### Packing: Skip Landscape→Portrait When Row Is Already Full-Width
**Date**: 2026-07-23

**Change**: Pass 1 no longer rotates a landscape design to portrait when keeping it landscape already leaves little free width **and** the next logo still cannot sit on the same row.

**Details**:
- **Skip when both are true** (in `_rotate_landscape_for_packing()`):
  1. Free space beside the design as landscape is **&lt; 200 mm** (`min_free_px = int(200 * mm_to_pixel_factor)`)
  2. The **next** logo **cannot** fit on the same row next to it (next width uses portrait packing width for landscape non-A3 designs via `_packing_width_for_fit_check()`)
- **Otherwise**: Rotate 90° to portrait and set `_pack_pass1_rotated = True` (same as before)
- **Unchanged**: A3 and squares (`width <= height`) are never rotated in Pass 1; size codes / resize math unchanged

**Logging**:
- No new console or size-determination events (packing rotations remain silent; final paste sizes appear only after placement)

### Save PNG Background Thread and Faster Write
**Date**: 2026-07-23

**Change**: Saving large canvases no longer freezes the GUI; PNG encode is faster; progress label text no longer truncates/garbles mid-update.

**Details**:
- **Background save**: `gui_save.py` and `gui_save_folder.py` run save/RAR work on a daemon `SaveWorker` thread; UI updates use `root.after` / `_ui`; overlapping saves show “Save in progress”
- **Faster PNG**: `create_canvas_image()` / save path uses `compress_level=1`, `optimize=False` (still lossless PNG; much faster on huge canvases than Pillow default 6)
- **Progress label**: Clear-then-set text in `gui_progress.py`; label `width=48`, `anchor="w"` in `gui_ui_builder_impl.py` so strings like “Preparing Save…” stay readable

**Logging**:
- **Console / run log**: `event=save_completed` now includes `duration_ms` (single-file save path)
- `event=save_failed` unchanged on errors
- Folder save still has no separate `log_run_event` calls beyond existing console Tee output

### Removed Arrange Success Popup
**Date**: 2026-07-23

**Change**: After arranging designs, the app no longer shows a “Successfully arranged … designs” info dialog.

**Details**:
- Removed `messagebox.showinfo("Success", …)` from `gui_processing_helpers_arrangement.py`
- Stats label under Actions and the preview still update as before; progress still reaches “Complete!” then resets
- Save success/error dialogs are unchanged

**Logging**: No change (`Processing completed` / `Preview Drawn` events still written)

### Two-Pass Packing Rotation (Landscape↔Portrait)
**Date**: 2026-07-22 (Pass 2 + orientation fix; Pass 1 introduced 2026-07-18)

**Change**: After sizing, the packer may rotate designs only for canvas packing — size reference mm values stay the same. Pass 1 narrows landscapes for denser rows; Pass 2 widens portraits again when a closed row has spare width.

**Details**:
- **Pass 1** (`_rotate_landscape_for_packing`): For each design with `width > height` (skip A3 / squares), rotate **+90°** to portrait before row fill; mark `_pack_pass1_rotated`
- **Row packing**: Uses current (often portrait) widths with fixed 8 mm gaps and left start margin
- **Pass 2** (`_fill_row_spare_with_landscape`, via `_place_completed_row`): After a row is complete, rotate any portrait that still fits as landscape:
  - Pass‑1 designs → **−90°** (undo; avoids 180° content flip)
  - Native portraits → **+90°**
- **A3**: Skipped in both passes (A3 forced-landscape path in `image_orientation.py` still applies at load/resize)
- **Modules**: `scripts/src/core/canvas_arranger.py`

**Logging**:
- No dedicated packing-rotation console or size-log lines (Jul 22 debug instrumentation was removed)
- Size determination logs still reflect **pre-pack** resize dimensions; final on-canvas orientation may differ after Pass 1/2

### Canvas Gaps Retargeted (8 / 1 / 12 mm)
**Date**: 2026-07-18

**Change**: Horizontal packing margins updated to match print targets; row-fit math aligned with `place_row_grid`.

**Details**:
- **Constants** in `scripts/src/core/size_reference.py` (300 DPI: `px ≈ mm × 300 / 25.4`), re-exported via `image_utils.py`:
  - `DEFAULT_DESIGN_PADDING` = **94** (~**8 mm** between designs; was 100)
  - `NON_BAR_MARGIN` = **12** (~**1 mm** left / start gap; was 20)
  - `COLOR_BAR_SPACING` = **142** (~**12 mm** gap before color bar; was 150)
  - `COLOR_BAR_WIDTH` = **59** (unchanged, ~5 mm bar reservation)
- **Placement**: Left-aligned fixed gap; leftover width stays on the color-bar side (`canvas_placement.py`)
- **Fit check**: `_row_width_needed` = `NON_BAR_MARGIN + Σ widths + (n−1)×padding` (matches placement; fixes false “doesn’t fit” for pairs that should share a row)

**Logging**: No new events; effective canvas width for packing still excludes `COLOR_BAR_WIDTH + COLOR_BAR_SPACING`

### Unified Logs Folder and Human-Readable Logging
**Date**: 2026-07-14

**Change**: All run logs now live under a single `Logs/` folder. Separate `Errors and Warnings/` and `Size Determination Logs/` outputs were removed. Console and size determination logs are written in a more human-readable format.

**Details**:
- **Single folder**: `Logs/` holds `console_log_*.txt` and `(stem) size_determination_*.txt`
- **No error files**: `save_error_to_file` is a no-op; errors/warnings still appear in the console log and UI dialogs; stats for the run summary are still counted
- **Size determination**: Written into `Logs/` via `scripts/src/system/logging/size_determination.py`; design entries use aligned labels (Order Number, Item SKU, Size Reference, Final Size)
- **Console**: Timestamped plain output; run events as sentences (`Processing started — …`); end-of-run summary points only to `Logs/`
- **Bracket matching**: Size rows like `M261 (102722)` require both base and bracket in the SKU; otherwise bare codes such as `A4` can match (`size_code_extractor.py`)
- **Docs**: `USAGE.md`, `docs/README.md`, and this file updated to match

### Preview Zoom and Design Overlay Polish
**Date**: 2026-07-14

**Change**: Default preview zoom raised slightly, and per-design overlay markup made clearer (black label above each design, black outline).

**Details**:
- **Default zoom**: `DEFAULT_PREVIEW_ZOOM` in `scripts/gui_helpers/canvas/gui_preview_helpers.py` changed from `0.35` to `0.475` (still fits one batch width to the panel, then applies this factor)
- **SKU / identifier label**: Drawn centered **above** each design (`anchor="mb"`) instead of below it
- **Label color**: Black `(0, 0, 0)` instead of blue
- **Design outline**: Black rectangle around each design instead of blue
- **Unchanged**: Label still only draws when the scaled box is large enough (`box_w > 50` and `box_h > 20`); text content remains `design["sku"]` (SKU / order label); batch border, scroll behavior, and PhotoImage cache path unchanged

**Logging**:
- **Console / run log**: `event=preview_drawn` unchanged (`designs_total`, `batches_total`, `scale`, `duration_ms`); the new zoom value is reflected in the logged `scale` field after arrange draws
- No new log events added

### Lightweight GUI Theme Polish
**Date**: 2026-07-12

**Change**: Applied a one-shot `ttk` theme so the chrome UI looks cleaner without new dependencies or preview-performance cost.

**Details**:
- **Theme module**: `scripts/gui_helpers/common/gui_theme.py` — slate/teal palette, Segoe UI fonts, shared color constants (`BG`, `FG`, `MUTED`, `ACCENT`, `PREVIEW_BG`)
- **Applied once**: `apply_theme(root)` runs at the start of `create_ui` (`gui_ui_builder_impl.py`) using the `clam` theme for reliable color customization
- **Button hierarchy**: Accent styles for **Normal** / **Personalised** / **Missing Logo**; Secondary for **Save PNG(s)**; Quiet for **Clear Preview** and **Remove DTF Queues Folder**
- **Layout**: Action buttons grouped under an **Actions** LabelFrame; muted empty-state labels; teal progress bar
- **Preview**: Background color moved to theme constants (`#d0d5dd` / matching RGBA); compositing, PhotoImage cache, and draw path unchanged
- **No new packages**: Still stock Tkinter + `ttk` only

**Logging**:
- **Console / run log**: `event=gui_theme_applied` once at UI build (`theme`, `accent`, `preview_bg`)
- Preview draw logging (`event=preview_drawn`) unchanged

### Minor Bug Fixups (Paths, Messages, Validation)
**Date**: 2026-07-10

**Change**: Small correctness and UX polish with no widget/layout changes.

**Details**:
- **Mode naming in messages**: Dialogs and prompts now say **Normal** (matching the action button) instead of outdated labels such as "All In One Go" / "Load & Arrange Designs"
- **Canvas size / DPI validation**: Unchanged spinbox values no longer trigger rearrange prompts; changing width and height together shows a single rearrange dialog
- **Output filename strip**: `DTF Des-` prefix removal for saved PNG names uses the correct whitespace regex (`^DTF\s*Des-`), matching `rar_utils.py`
- **Missing Size Reference path**: Export folder resolves via `queue_app.__file__` (project root) instead of incorrectly landing under `scripts/gui_helpers/`
- **DTF Queues fallback**: Folder picker initial directory falls back to the same project root
- **Docs**: `USAGE.md`, `docs/README.md`, and this change log updated to match current button names (`Normal`, `Save PNG(s)`) and export paths

**Logging / export impact**:
- New missing-size exports write to `{app_root}/Missing Size Reference/`
- Older warning files may still reference `scripts/gui_helpers/Missing Size Reference/` from before this fix; that path is obsolete

### Cleared Invalid Pip Leftover (`~ip`)
**Date**: 2026-07-10

**Change**: Removed a broken pip leftover that caused `WARNING: Ignoring invalid distribution ~ip` every time `run_queue_app.bat` installed dependencies.

**Details**:
- **Symptom**: Launcher step "Installing/Updating dependencies..." printed the same warning repeatedly; the app still started and dependencies still installed successfully
- **Cause**: Interrupted `pip` self-upgrade left junk folders under the user site-packages directory (Microsoft Store Python 3.11 path), typically named `~ip` and `~ip-*.dist-info`
- **Fix applied**: Deleted `~ip` and `~ip-26.0.1.dist-info` from  
  `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\local-packages\Python311\site-packages`
- **Verified**: `python -m pip check` reported no broken requirements; `pip install --upgrade pip` completed with no invalid-distribution warnings
- **Docs**: Troubleshooting entries added in this file and in `USAGE.md` for the same warning if it reappears on another machine

### Hide CMD Window, Keep File Logging
**Date**: 2026-07-10

**Change**: The Windows launcher starts the GUI without a persistent black CMD window; all run output still goes to log files.

**Details**:
- **Launcher**: `run_queue_app.bat` installs dependencies, then starts `pythonw queue_app.py` with `start "" /MAX` and exits so only the maximized GUI remains
- **PowerShell**: Run as `.\run_queue_app.bat` (PowerShell does not run scripts from the current folder without `.\`)
- **Logging safety**: `scripts/src/system/logging/console.py` Tee writes to the log file even when stdout/stderr are missing (`pythonw`); `errors.py` / `errors_setup.py` guard `__stderr__` writes the same way
- **Window visibility**: GUI deiconifies / maximizes on startup (`queue_app.py`) so the window does not stay minimized after detached launch
- **Log location**: Run capture files remain in `Logs/` as `console_log_YYYY-MM-DD_HH-MM-SS.txt` (not a live CMD mirror when using the bat / `pythonw`)
- **Debug**: Use `python queue_app.py` if you want a visible console; file logging still applies

### Scrollable Full-Canvas Preview
**Date**: 2026-07-10

**Change**: Preview shows all arranged designs at a fixed readable scale with scrolling (zoom controls and the 100-design preview cap removed).

**Details**:
- **No design cap**: Preview draws every arranged design; save/export behavior unchanged
- **No zoom UI**: Zoom in/out/reset buttons and mouse-wheel zoom removed
- **Scale**: Fits one batch width to the preview panel, then applies `DEFAULT_PREVIEW_ZOOM` so the default view is slightly zoomed out (later set to `0.475`; see Preview Zoom and Design Overlay Polish, 2026-07-14)
- **Navigation**: Mouse wheel pans vertically; Shift+wheel pans horizontally; scrollbars pan the full scrollregion
- **Performance**: Each batch is composited into one PIL preview image / one Tk `PhotoImage`; PhotoImages are cached by scale and cleared on Clear Preview; canvas resize redraw is debounced (150 ms)
- **Visibility**: Cool grey preview background (theme `PREVIEW_BG`, `#d0d5dd`) so white designs remain visible; right padding / outline allowance so the black batch border is not clipped
- **Modules**: `gui_preview.py`, `gui_preview_draw.py`, `gui_preview_helpers.py`, `gui_ui_builder_preview.py`
- **Logging**: `event=preview_drawn` (designs_total, batches_total, scale, duration_ms) on full arrange draws; `event=preview_draw_failed` on errors. Debounced resize redraws that reuse the PhotoImage cache are not logged.

### A3 Forced Landscape (Rotate + Swap Size Box)
**Date**: 2026-06-11

**Change**: A3 designs are always rotated 90° clockwise and resized to a landscape size box before canvas paste.

**Details**:
- **Trigger**: Any design whose size reference lookup resolves to size code `A3` (Normal, Personalised, and Missing Logo modes)
- **Transform** (in `load_and_resize_design()` via `image_orientation.py`):
  1. Rotate source PNG 90° clockwise (`PIL.Image.rotate(90, expand=True)`)
  2. Swap `width_mm` / `height_mm` and `width_px` / `height_px` from the size reference (portrait Excel values become a landscape target box at runtime)
  3. Resize with existing `resize_image_with_constraints()`; canvas paste unchanged
- **IronOn interaction**: IronOn auto-orientation (`ENABLE_AUTO_ORIENTATION`) is skipped for A3 (`allow_orientation=False`) so area-based rotation does not override the forced landscape rule
- **Kill switch**: `ENABLE_A3_LANDSCAPE = False` in `scripts/src/core/image_orientation.py`
- **Logging**:
  - **Console log** (DEBUG): `a3_landscape=forced rotate=90 size_box_swapped original_box=WxH swapped_box=WxH`
  - **Size determination log**: per-design entries show swapped reference dimensions plus `A3 Landscape:` and `IronOn auto-orientation: skipped` when applicable
- **Size reference file**: No spreadsheet change required; A3 rows remain portrait in Configuration Workbook

**Example** (portrait source 3356×4698 px, reference box 3507×4960 px):
- After rotate: 4698×3356 px image
- After swap: 4960×3507 px target box (~420×297 mm)
- Final paste size: ~4909×3507 px (landscape on canvas)

### Improved Size Determination Logging and Bracket Matching
**Date**: 2026-01-28

**Change**: Enhanced size determination logging format and improved bracket code matching with token-based whole-token matching.

**Details**:
- **Improved Log Format**: Each design's log entry now includes a clear "Size Determination" section showing:
  - **Merge Entry**: The full Merge cell text from the Size Reference (e.g., `K-H (YS) (YXS)`) indicating which row was selected
  - **Size Code (used)**: The actual pattern/key from the SKU that triggered the match (e.g., `YXS`, `Y2XL`, `K-H`)
  - This makes it easy to see both which reference row was used and which SKU pattern triggered it
- **Log Filename Enhancement**: Size determination log filenames now include the input file name in brackets at the start:
  - Format: `(input_file_stem) size_determination_YYYY-MM-DD_HH-MM-SS.txt`
  - Example: `(DTF Des-P6000283-P6000283) size_determination_2026-01-28_16-50-03.txt`
  - Makes it easier to identify which log file corresponds to which input file
- **Token-Based Bracket Matching**: Bracket codes now match against **whole tokens** in the SKU (split by `-`), not substrings:
  - This ensures `YS` only matches when there is a token exactly `YS`, and `YXS` only matches when there is a token exactly `YXS`
  - Prevents `YS` from incorrectly matching inside `YXS` or other longer codes
  - Each Merge row represents a single size definition; bracket codes are aliases to select that row, not separate pieces
- **Technical Implementation**:
  - Updated `_search_reference_size_codes()` in `src/size_code_extractor.py` to tokenize SKU and match bracket codes against whole tokens
  - Updated `_build_size_result()` in `src/size_reference.py` to include `merge_entry` in the result dictionary
  - Updated `create_design_log_entry()` in `gui_helpers/gui_processing_helpers.py` to display Merge Entry and Size Code (used) clearly
  - Updated `start_size_determination_log()` in `src/logging_utils.py` to include input file stem in log filename

**Benefits**:
- **Clearer Logs**: Easy to see which Size Reference row was used and which SKU pattern triggered it
- **Better File Organization**: Log filenames immediately show which input file they correspond to
- **More Accurate Matching**: Token-based matching prevents substring confusion (e.g., `YS` vs `YXS`)

### Size Determination Logging for Folder Processing
**Date**: 2026-01-27

**Change**: Size determination logs are now created when processing a **folder** in all three modes (Normal, Personalised, Missing Logo). Previously, size determination logging applied only to single-file processing.

**Details**:
- **Normal (folder)**: One size determination log per DTF Des file in the folder; mode is `standard`.
- **Personalised (folder)**: One size determination log per DTF Des file; mode is `personalised`.
- **Missing Logo (folder)**: One size determination log per DTF Des file; mode is `missing_logo`.
- **Logging overview**: Documentation now describes all four log types per run (console logs, errors and warnings, missing size reference CSV, size determination logs).
- **Implementation**: `process_single_file_for_folder`, `process_personalised_file_for_folder`, and `process_missing_logo_file_for_folder` in `gui_helpers/gui_processing_core.py` now call `start_size_determination_log`, `log_size_determination` (via `create_design_log_entry`), and `finish_size_determination_log` on every exit path.

### Bracket Size Code Support in Size Reference
**Date**: 2026-01-09

**Change**: Added support for bracket size codes in the Size Reference Merge column, allowing multiple size codes to match a single entry.

**Details**:
- **Bracket Format**: Size Reference entries can now include bracket codes in the Merge column
  - Format: `BaseCode (BracketCode1) (BracketCode2)` or `BaseCode (BracketCode)`
  - Examples: `K-SS (YS) (YXS)`, `W115 (S)`, `M-T (XS) (S)`
- **Matching Logic**:
  - **Base Code Matching**: SKUs can match against the base code (existing behavior)
    - Example: SKU `121913LG-K-SS-LPNK-...` matches `K-SS (YS) (YXS)` via base code `K-SS`
  - **Bracket Code Matching (scoped by base code)**:
    - Bracket codes are now matched **together with** their base code, not in isolation.
    - Internally, when a SKU contains both a base garment code and a bracket size code, the extractor builds a composite like `"K-H|YXS"` or `"M-T|YXS"`.
    - The Size Reference lookup then:
      1. First looks for a row where **both** `Merge_clean` equals the base code (e.g. `K-H`) **and** `Merge_brackets` contains the bracket code (e.g. `YXS`).
      2. If that fails, falls back to **base-only** matching using the base code.
      3. Only if that also fails does it fall back to the generic behavior (bracket-only / base-only using the size code).
    - Example: SKU `121913LG-K-SS-LPNK-YXS` matches `K-SS (YS) (YXS)` because the composite `"K-SS|YXS"` requires `Merge_clean = "K-SS"` **and** `Merge_brackets` containing `YXS`.
    - Example: SKU `121798LG-K-H-LPNK-YXS-YES` matches `K-H (YS) (YXS)` rather than `K-SS (YXS)` because the composite `"K-H|YXS"` requires `Merge_clean = "K-H"` **and** `Merge_brackets` containing `YXS`.
    - Example: SKU `128968LG-W115-BLK-S-Yes` matches `W115 (S)` via base `W115` plus bracket code `S`.
- **Backward Compatibility**: Entries without brackets continue to work as before
  - Example: `M-T` or `W115` (no brackets) work exactly as they did before
- **Technical Implementation**:
  - New function: `_parse_brackets_from_merge()` in `src/file_loaders.py` extracts base codes and bracket codes
  - New column: `Merge_brackets` stores list of bracket codes for each row
  - Updated: `_search_reference_size_codes()` in `src/size_code_extractor.py` now returns a composite `"BASE|BRACKET"` string (e.g. `"K-H|YXS"`) when a bracket match is found, so both pieces of information are preserved.
  - Updated: `get_size_from_reference()` / `_find_matching_row()` in `src/size_reference.py` accept an optional `base_code` and enforce that **both** `Merge_clean` and `Merge_brackets` match when base+bracket information is available.
  - When only a simple size code is used (no brackets and no base_code), the lookup behavior is unchanged.

**Benefits**:
- **Flexible Matching**: One size reference entry can match multiple SKU patterns
- **Easier Maintenance**: Add bracket codes to existing entries instead of creating duplicate rows
- **Better Organization**: Related size codes grouped together in one entry
- **Backward Compatible**: Existing entries without brackets continue to work

### Configuration Workbook Sheet Name Support
**Date**: 2026-01-09

**Change**: Updated code to use sheet names instead of indices for loading Configuration Workbook sheets, with fallback to indices for backward compatibility.

**Details**:
- **Sheet Names**: Code now prefers to load sheets by name:
  - Size Reference: Sheet name `"Size References"` (falls back to Sheet 1 / index 0)
  - Pocket Design IDs: Sheet name `"Pocket Design IDs Database"` (falls back to Sheet 2 / index 1)
- **Backward Compatibility**: If sheet names don't exist, code automatically falls back to using sheet indices
  - This ensures existing workbooks continue to work without modification
- **Technical Implementation**:
  - Updated `load_size_reference_from_app_dir()` in `src/file_loaders.py`
  - Updated `load_pocket_design_ids_database()` in `src/file_loaders.py`
  - Both functions try sheet name first, then fall back to index if name not found
- **Benefits**:
  - **More Robust**: Works even if sheets are reordered
  - **Self-Documenting**: Sheet names make the code more readable
  - **Flexible**: Users can rename sheets to meaningful names
  - **Safe**: Automatic fallback ensures no breaking changes

### Logging Initialization File Location Fix
**Date**: 2026-01-08
**Change**: Fixed `logging_initialized.txt` file location - now stored in Console Logs folder instead of Errors and Warnings folder

**Details**:
- **Location Change**: The `logging_initialized.txt` marker file is now created in the `Console Logs/` folder instead of the `Errors and Warnings/` folder
  - This file is a marker indicating that the logging system has initialized, not an actual error or warning
  - It belongs with other console-related files, not mixed with error/warning logs
- **Better Organization**: 
  - Console Logs folder now contains: console log files and the initialization marker
  - Errors and Warnings folder now contains: only actual error and warning files
- **Technical Implementation**:
  - Modified `setup_error_logging()` in `src/logging_utils.py` to use `_console_logs_dir` instead of `_logs_dir`
  - Falls back to `_logs_dir` if console logging isn't initialized (edge case)
  - Since `setup_console_logging()` runs before `setup_error_logging()`, the console logs directory is always available

**Benefits**:
- **Cleaner Organization**: Initialization markers are separate from actual errors/warnings
- **Logical Grouping**: All console-related files are now in one location
- **Easier Maintenance**: Errors and Warnings folder only contains actual issues to investigate

### Grid Layout Placement
**Date**: 2026-01-07

**Change**: Replaced complex alignment system with simple grid layout for design placement

**Details**:
- **Grid Format**: Designs are now placed in a simple left-to-right grid format
  - All designs are left-aligned with consistent spacing
  - Removed complex left/center/right alignment logic based on design count
  - Eliminates gaps and overlapping issues that occurred with the previous alignment system
- **Benefits**:
  - **Fixes Bug**: Resolves spacing issues (large gaps and overlapping) in personalized run mode
  - **Predictable Layout**: Simple, consistent placement makes it easier to predict design positions
  - **Simpler Code**: Removed complex alignment logic, making the codebase easier to maintain
  - **Color Bar Spacing Preserved**: The right-side gap for the color bar is maintained via effective canvas width calculation
- **Technical Details**:
  - New function: `place_row_grid()` in `src/canvas_placement.py`
  - Replaces `place_row_split_aligned()` calls in `src/canvas_arranger.py`
  - All designs placed left-to-right with fixed gap (`DEFAULT_DESIGN_PADDING` ≈ 8 mm) and left start (`NON_BAR_MARGIN` ≈ 2 mm); vertical row spacing ≈ 15 mm (`DEFAULT_VERTICAL_PADDING`)
  - Effective canvas width accounts for color bar space (`COLOR_BAR_WIDTH + COLOR_BAR_SPACING` ≈ bar + 12 mm)
  - Canvas width constraints in `calculate_image_dimensions()` / `resize_image_with_constraints()` use the same effective canvas width, ensuring resized designs respect the color bar gap (including personalised double designs).
  - Two-pass packing rotation may change on-canvas orientation after resize (see Recent Changes, 2026-07-18 / 2026-07-22 / 2026-07-23)

### Missing Logo Processing Mode
**Date**: 2026-01-02

**Change**: Added new "Missing Logo" processing mode that searches both personalized and standard design folders

**Details**:
- **New Button**: "Missing Logo" button added below "Personalised" button in the action buttons section
- **Dual Search Strategy**:
  1. **First**: Searches personalized folders (Single/Double Design Folders) using Order Number and VBA logic
  2. **Fallback**: If not found in personalized folders, searches "Normal" folder using design ID extracted from SKU
- **Column Requirements**:
  - **Order Number column**: Used for finding design files in personalized folders (VBA logic)
  - **Item SKU column**: Used for finding design files in Normal Designs folder and for size reference matching
- **Processing Logic**:
  - Uses personalized search method (order ID, duplicate index, pocket/sleeve variants) for personalized folders
  - For duplicate order numbers (same Order ID appearing multiple times), the VBA search logic first looks
    for the specific suffixed file name (e.g. `203-...-1`, `203-...-2`, `203-...-3`) across Single and Double
    folders, and only falls back to the base order number file (`203-...`) if no suffixed file exists in either
    folder. This ensures that personalised suffix files are preferred over base files when present.
  - Uses standard search method (design ID from SKU) for Normal Designs folder
  - Supports all personalized design types (single, single-pocket, single-sleeve, double)
  - Applies appropriate sizing rules based on where the design was found
- **Works with Folder Processing**: Can process multiple DTF Des files in a folder using Missing Logo mode
- **Benefits**:
  - Handles cases where designs might be in either location
  - Reduces manual intervention needed when design locations are uncertain
  - Maintains all existing functionality (size reference, pocket/sleeve variants, etc.)

### Canvas Preview Improvements
**Date**: 2026-01-02

**Change**: Enhanced canvas preview display with better visual separation and border visibility

**Details**:
- **Left Padding**: Added 5px left padding to prevent canvas border clipping
  - Canvas black outline is now fully visible on the left side
  - Padding applied to all drawing coordinates (borders, designs, labels)
  - Scroll region adjusted to account for padding
- **Batch Spacing**: Increased spacing between batches in preview
  - Base spacing: 200 pixels (increased from 50)
  - Total spacing: 204 pixels (200 base + 4 for borders)
  - Provides clear visual separation between batches
  - Spacing is fixed in preview pixels (zoom level no longer applies)
- **File-Based Batch Separation**: Each DTF Des file now starts on a new batch in preview
  - When processing multiple files in a folder, batches from each file are kept separate
  - Example: File1 (batches 1-2) → File2 (batch 3) → File3 (batch 4)
  - PNG output remains unchanged (each file still saves separately)
  - Only affects preview canvas display, not PNG output files
- **Benefits**:
  - Better visual clarity when viewing multiple batches
  - Easier identification of which batches belong to which file
  - No border clipping issues
  - Improved user experience when reviewing arranged designs

### Error Logging System Fix
**Date**: 2026-01-02

**Change**: Fixed recursive error logging issue that caused infinite loops and console log spam

**Details**:
- **Problem**: Error logging system was creating infinite recursion loops
  - When an error was detected, it printed "[ANOMALY DETECTED] Error logged to file"
  - This message went through the logging system, which detected "Error" keyword
  - This triggered another error log, creating an infinite loop
  - Resulted in hundreds of repeated messages and "maximum recursion depth exceeded" errors
- **Solution**: 
  - Added recursion prevention: "[ANOMALY DETECTED]" messages are now skipped by the logging system
  - Changed error markers to use `sys.__stderr__.write()` directly instead of `print(..., file=sys.stderr)`
  - This bypasses the logging wrapper and prevents recursion
  - Applied to all error logging functions (print wrapper, stderr logger, messagebox wrappers, exception handler)
- **Benefits**:
  - Clean console logs without spam
  - Errors are logged once without repetition
  - No more recursion errors
  - Improved system stability

### Configuration Workbook Integration
**Date**: 2026-01-02

**Change**: Consolidated Size Reference and Pocket Design IDs Database into a single Configuration Workbook

**Details**:
- **Configuration Workbook.xlsx**: Single file in `config/` directory containing both:
  - **Sheet "Size References" (or Sheet 1)**: Size Reference (replaces separate `Size Reference.xlsx` file)
  - **Sheet "Pocket Design IDs Database" (or Sheet 2)**: Pocket Design IDs Database (replaces separate `Pocket Design IDs Database.xlsx` file)
- **Auto-Loading**: Both are automatically loaded on application startup
  - Size Reference from sheet "Size References" (or Sheet 1)
  - Pocket Design IDs from sheet "Pocket Design IDs Database" (or Sheet 2)
- **GUI Changes**:
  - Removed "Select Size Reference File" button (no longer needed)
  - Size Reference section removed from GUI (consistent with Pocket IDs)
- **Code Changes**:
  - Removed asterisk removal logic from Merge column (only whitespace trimming now)
  - Updated `auto_load_settings()` to skip size reference loading from saved settings
  - All size reference operations now use Configuration Workbook sheet "Size References" (or Sheet 1)
- **Benefits**:
  - Single file to manage instead of two separate files
  - Automatic loading - no manual file selection needed
  - Cleaner GUI with fewer buttons
  - Consistent behavior for both Size Reference and Pocket Design IDs

---

## Recent Changes (Previous)

#### 1. Size Code Extraction Enhancement
**Date**: November 27, 2025
**Change**: Improved size code extraction logic to use reference file as source of truth

**Details**:
- Changed from extracting potential codes from SKU and checking reference file
- Now extracts all size codes from Merge column (Column I) of size reference file
- Searches SKU string for each reference size code
- Returns first match found (in order of appearance in SKU)
- Handles patterns like `*M-T*`, `*W-T*`, `*K-T*`, `*A4*`, `*A5*`, etc.

**Example**:
- SKU: `87984LG-I-M-T-BLK-L`
- Old behavior: Extracted `I-M` (first match)
- New behavior: Finds `M-T` from reference file in SKU → Returns `M-T`

#### 2. Output File Naming
**Date**: November 27, 2025
**Change**: Simplified output file naming and folder structure

**Details**:
- **Removed date prefix** from PNG filenames
  - Before: `2024-01-15_filename_Part 1.png`
  - After: `filename_Part 1.png`
- **Changed output folder** from date-based to "Output"
  - Before: `2024-01-15/` folder
  - After: `Output/` folder
- **Removed "DTF Des-" prefix** from filenames
  - Before: `DTF Des-P200-P211_Part 1.png`
  - After: `P200-P211_Part 1.png`

#### 4. Folder Processing Restored
**Date**: November 27, 2025
**Change**: Restored folder processing functionality with improved behavior

**Details**:
- **Select Input Folder**: Process all DTF Des files in a selected folder
- **Combined Preview**: All designs from all files are shown in a single combined preview
- **Separate Saves**: Each input file generates its own separate PNG output files
- **Correct Labels**: Each PNG file displays the correct label extracted from its own source file
- **No Auto-Save**: Files are not saved automatically during folder processing; user must click "Save PNG(s)"
- Works with both "Normal" and "Personalised" modes

**Implementation**:
- Added `select_input_folder()` function to select folder containing DTF Des files
- Added `process_folder()` for folder processing in "Normal" mode
- Added `process_folder_personalised()` for folder processing in "Personalised" mode
- Added `save_folder_files_separately()` to save each file's batches separately
- Modified `create_and_save_canvas()` to accept `source_file_path` parameter for correct label extraction

#### 5. PNG Label Fix for Folder Processing
**Date**: November 27, 2025
**Change**: Fixed issue where all PNG files showed the same label when processing multiple files

**Details**:
- **Problem**: When processing a folder, all PNG files were displaying the same label (e.g., "p1200-1200") even if that label wasn't in the batch
- **Solution**: Each PNG file now correctly extracts and displays the label from its own source file
- **Implementation**: Added `source_file_path` parameter to `create_and_save_canvas()` to track which file each batch came from

**Example**:
- Processing "DTF Des-p100-121.xlsx" and "DTF Des-p200-300.xlsx"
- Before: Both PNGs showed "p1200-1200" (incorrect)
- After: PNGs show "p100-121" and "p200-300" respectively (correct)

#### 6. Missing Size Reference Export Feature
**Date**: November 27, 2025
**Change**: Added automatic export of rows with missing size references to a new DTF Des file

**Details**:
- **Automatic Export**: When processing designs, if a size reference is not found in the reference sheet, the entire row from the DTF Des file is automatically exported
- **Export Location**: Files are saved in the `Missing Size Reference` folder at the application (project) root — same level as `Output/` and `Logs/`
- **Smart Numbering**: Filenames include a number suffix that auto-increments for multiple files on the same day
  - First file: `DTF Des-Missing Size Reference 2025-11-27 1.xlsx`
  - Second file: `DTF Des-Missing Size Reference 2025-11-27 2.xlsx`
  - And so on...
- **Complete Data Preservation**: 
  - Includes full header row (all column names)
  - Includes complete rows with all columns
  - All instances included (no deduplication)
- **Works with All Processing Modes**:
  - Single file processing: Exports missing rows from that file
  - Folder processing: Combines missing rows from all files into one export
  - Works with both "Normal" and "Personalised" modes
- **User Notification**: Shows messagebox informing user where the file was saved

**Benefits**:
- Easy reprocessing: After adding missing size references to the reference sheet, users can simply load the exported file and process it again
- No data loss: All rows with missing references are preserved with complete information
- Organized workflow: All missing reference rows are collected in one place for easy management

**Example Workflow**:
1. Process DTF Des file(s) with some missing size references
2. Application automatically exports missing rows to `DTF Des-Missing Size Reference 2025-11-27 1.xlsx`
3. User adds missing size references to the size reference sheet
4. User loads the exported file and processes it again
5. All designs now have proper size references and are processed correctly

#### 7. Comprehensive Error and Warning Logging System
**Date**: November 28, 2025
**Change**: Added comprehensive error and warning logging system that saves each error/warning to separate files

**Details**:
- **Automatic Logging**: All errors and warnings are automatically logged to separate text files
- **Log Location**: Files are saved in "Errors and Warnings" folder in the application directory
- **File Naming**: 
  - Format: `{error_type}_{YYYY-MM-DD}_{occurrence}.txt`
  - Examples: `error_2025-11-28_1.txt`, `warning_2025-11-28_1.txt`
  - Occurrence number auto-increments for each error/warning on the same day
- **Comprehensive Coverage**:
  - Unhandled exceptions (with full traceback)
  - Print statements containing error/warning keywords
  - Stderr output and tracebacks
  - Error and warning messageboxes
- **Log Content**: Each file contains:
  - Timestamp of when the error/warning occurred
  - Error type (Error or Warning)
  - Full error message or traceback
  - Context information
- **Initialization**: Logging system is automatically initialized when the application starts
  - Creates a marker file `logging_initialized.txt` in the Console Logs folder to verify the logging system is working
  - The marker file contains initialization timestamp and logs directory path
  - Note: The marker file is stored in Console Logs folder, not Errors and Warnings folder
- **Fallback Handling**: If primary log directory cannot be created, attempts to use fallback location

**Benefits**:
- Easy debugging: All errors are preserved with full context
- No data loss: Errors are saved even if the application crashes
- Organized tracking: Each error/warning in a separate file makes it easy to review issues
- Historical record: Date-based naming allows tracking errors over time

#### 8. Design Code Extraction and Apparel Size Prefix Removal
**Date**: November 28, 2025
**Change**: Enhanced design file matching with design code extraction and apparel size prefix removal

**Details**:
- **Design Code Extraction**: Extracts design code from SKU (e.g., "77989LG" from "77989LG-M-T-BLK-M")
  - Takes the first part before the first dash
  - Falls back to full SKU if no dash is present
- **Apparel Size Prefix Removal**: Automatically removes common apparel size prefixes from design codes when initial search fails
  - Supported prefixes: XXXXL, XXXL, XXL, 3XL, 4XL, 2XL, XL, XS, S, M, L
  - Example: SKU `XL39553LG-I-M-T-BLK-XL` extracts design code `XL39553LG`
  - If file not found, removes "XL" prefix and searches for `39553LG.png`
  - Case-insensitive matching
  - Only activates as fallback when normal search fails
- **Enhanced File Matching**: Design file search now uses multiple strategies:
  1. Exact match with design code
  2. Case-insensitive match with design code
  3. Fallback to full SKU match
  4. **NEW**: Try with apparel size prefix removed (if initial search fails)
- **Benefits**: 
  - Prevents false "design not found" warnings when design files exist without size prefixes
  - Handles cases where SKUs contain size prefixes but design files don't
  - Improves design file matching accuracy, especially for files with size prefixes in their names

#### 9. RAR Archive Creation and DTF Queues Integration
**Date**: November 28, 2025
**Change**: Added automatic RAR archive creation and integration with DTF Queues folder

**Details**:
- **Automatic RAR Creation**: After saving PNG files, the application automatically creates a RAR archive containing all generated PNG files
- **RAR Tool Detection**: Automatically detects and uses available RAR tools:
  - **WinRAR** (prioritized): Creates `.rar` format files
  - **7-Zip** (fallback): Creates `.7z` format files if WinRAR is not available
- **Smart RAR Naming**:
  - **Single File Processing**: Uses input filename (e.g., `P200-P211.rar`)
  - **Folder Processing**: Combines source file names (e.g., `P200-P211-P300.rar`)
  - If more than 3 files: Uses first 3 names + count (e.g., `P200-P211-P300-and-5-more.rar`)
  - Removes "DTF Des-" prefix and "_Part X" suffixes automatically
- **DTF Queues Folder Integration**:
  - New UI option: "Select DTF Queues Folder" button
  - "Remove DTF Queues Folder" button: Clear folder selection to prevent files from being sent
  - Automatically copies created RAR files to the selected DTF Queues folder
  - Folder path is saved in settings and restored on next launch
- **User Feedback**: Shows success message with RAR file location and copy status
- **Error Handling**: Gracefully handles missing RAR tools or copy failures

**Benefits**:
- Streamlined workflow: PNG files are automatically packaged into RAR archives
- Easy upload: RAR files are automatically copied to DTF Queues folder for processing
- Organized output: RAR files are named based on source files for easy identification

#### 10. Logging Initialization File Naming Update
**Date**: November 29, 2025
**Change**: Renamed logging initialization marker file for better clarity

**Details**:
- **Filename Change**: Changed initialization marker file from `_logging_initialized.txt` to `logging_initialized.txt`
  - Removed leading underscore for cleaner naming convention
  - File still serves the same purpose: verifying logging system initialization
- **Purpose**: The marker file confirms that the logging system is working correctly
  - Contains initialization timestamp
  - Contains logs directory path
  - Created once when the application starts (if it doesn't already exist)
- **Location**: The marker file is stored in the Console Logs folder (not Errors and Warnings folder)
  - This keeps initialization markers separate from actual error/warning files
  - All console-related files are now grouped together in Console Logs folder

**Benefits**:
- Cleaner file naming: No leading underscore makes the file more visible and easier to identify
- Consistent naming: Matches standard file naming conventions
- Better organization: Initialization marker is stored with console logs, not mixed with errors/warnings

#### 11. UI Improvements - Action Buttons and Progress Bar Repositioning
**Date**: November 29, 2025
**Change**: Moved action buttons and progress bar to the top of the left panel for better accessibility

**Details**:
- **Action Buttons Repositioned**: Moved all action buttons to the top of the left panel
  - "Normal" button
  - "Personalised" button
  - "Missing Logo" button (added 2026-01-02)
  - "Save PNG(s)" button
  - "Clear Preview" button
  - Now appears as the first elements in the left panel, before file selection and folder selection sections
- **Progress Bar Repositioned**: Moved progress bar directly below the action buttons
  - Progress bar and label now appear immediately after action buttons
  - Easier to see progress status during operations
- **Improved Workflow**: Users can now access primary actions and see progress updates without scrolling down

**Benefits**:
- Better user experience: Most frequently used buttons are immediately visible
- Improved accessibility: Progress updates are visible at the top
- Streamlined workflow: No need to scroll to find action buttons or check progress

#### 12. Progress Bar Updates During Image Saving
**Date**: November 29, 2025
**Change**: Added progress bar updates when saving canvas images to PNG files

**Details**:
- **Progress During Saving**: Progress bar now updates when saving images to PNG files
  - Shows "Preparing to save X image(s)..." at the start
  - Shows "Saving batch 1/3..." when saving multiple batches
  - Shows "Saving file 1/10: filename.png..." when saving multiple files from folder processing
  - Progress ranges from 0-90% during image saving
- **Progress During RAR Creation**: Shows progress updates during RAR archive creation
  - Shows "Creating RAR archive..." at 90%
  - Shows "Copying RAR to DTF Queues folder..." at 95%
  - Shows "Save complete!" at 100%
- **Auto-Reset**: Progress bar automatically resets after 1 second to show completion message
- **Error Handling**: Progress bar shows "Save failed" and resets on errors
- **Works for All Save Scenarios**:
  - Single file with single batch
  - Single file with multiple batches
  - Folder processing with multiple files

**Benefits**:
- Better user feedback: Users can see progress during long save operations
- Transparency: Clear indication of what operation is in progress
- Improved UX: No more wondering if the application is frozen during saving

#### 13. Apparel Size Prefix Fallback Logic Enhancement
**Date**: November 29, 2025
**Change**: Enhanced design file matching with automatic apparel size prefix removal as fallback

**Details**:
- **Problem Solved**: Fixed issue where SKUs with apparel size prefixes (e.g., `XL39553LG-I-M-T-BLK-XL`) couldn't find design files that exist without the prefix (e.g., `39553LG.png`)
- **Fallback Logic**: When initial design file search fails, automatically removes common apparel size prefixes and searches again
  - Supported prefixes: XS, S, M, L, XL, 2XL, 3XL, 4XL, XXL, XXXL, XXXXL
  - Case-insensitive matching
  - Only activates when normal search fails (doesn't slow down successful searches)
- **Implementation**:
  - Added `remove_apparel_size_prefix()` helper function
  - Updated `find_design_file()` to use fallback logic
  - Updated `find_design_file_personalised()` for consistency
- **Example**:
  - SKU: `XL39553LG-I-M-T-BLK-XL`
  - Extracted design code: `XL39553LG`
  - First search: Looks for `XL39553LG.png` (not found)
  - Fallback: Removes "XL" prefix, searches for `39553LG.png` (found!)
  - Result: Design file found, no false warning

**Benefits**:
- Prevents false "design not found" warnings
- Handles real-world scenarios where SKUs include size prefixes but design files don't
- Improves user experience by reducing unnecessary warnings
- Works automatically without user intervention

#### 14. Mixed File and Folder Processing Support
**Date**: November 29, 2025
**Change**: Enhanced file processing to support mixing single files with folder files in the same save operation

**Details**:
- **Problem Solved**: Previously, when mixing single files with folder files, single files were not included when saving images
- **Unified Storage**: Single files are now stored in the same `folder_file_batches` dictionary as folder files
  - When processing a single file, batches are stored in `folder_file_batches[file_path] = batches`
  - This allows single files to be saved together with folder files
- **Flexible Combinations**: Now supports any combination of files and folders:
  - Multiple folders: Folder 1 + Folder 2 → All files saved together
  - Multiple single files: File 1 + File 2 → All files saved together
  - Mixed: Folder 1 + Single File 1 → All files saved together
  - Complex: Folder 1 + Folder 2 + Single File 1 → All files saved together
- **Consistent Saving**: All files (from folders and single files) are saved using the same `save_folder_files_separately()` function
  - Each file gets its own separate PNG output files
  - All files are included in the same RAR archive
  - Proper filename extraction and batch handling for all files

**Implementation**:
- Updated `process_single_file()` to store batches in `folder_file_batches` when `file_path` is provided
- Updated `process_personalised_file()` to store batches in `folder_file_batches` when `file_path` is provided
- Save function already checks `folder_file_batches` first, so all accumulated files are saved together

**Example Workflow**:
1. Select Folder 1 → Load preview (files from folder stored in `folder_file_batches`)
2. Select Folder 2 → Load preview (files from folder added to `folder_file_batches`)
3. Select Single File → Load preview (single file added to `folder_file_batches`)
4. Click "Save PNG(s)" → All files from both folders and the single file are saved together

**Benefits**:
- Flexible workflow: Mix and match files and folders as needed
- Consistent behavior: All files treated the same way regardless of source
- No data loss: All files are saved together in one operation
- Improved user experience: No need to save files separately

#### 15. UI Label Enhancement - File/Folder Indicator
**Date**: November 29, 2025
**Change**: Added "File:" prefix to file labels to match "Folder:" prefix for better clarity

**Details**:
- **Consistent Labeling**: File labels now show "File:" prefix to match the "Folder:" prefix used for folders
  - Before: `filename.xlsx` (unclear if it's a file or folder)
  - After: `File: filename.xlsx` (clearly indicates it's a file)
- **Visual Consistency**: Both file and folder selections now have clear indicators:
  - **File:** filename.xlsx (when a single file is selected)
  - **Folder:** foldername (when a folder is selected)
- **Updated Locations**: Applied to both places where file labels are updated:
  - When auto-loading from saved settings
  - When manually selecting a file

**Benefits**:
- Better clarity: Users can immediately see whether a file or folder is selected
- Consistent UI: Matches the "Folder:" prefix format
- Improved user experience: Reduces confusion about what type of input is selected

#### 16. Double Design Folder - Original Image Size with Canvas Width Fitting
**Date**: December 3, 2025
**Change**: Double design folder images use original image dimensions (no size reference rules) but are automatically scaled down if they exceed canvas width

**Details**:
- **Original Size Preservation**: When a design is found in the double design folder, the image maintains its original width and height
  - No size reference rules are applied (M-T, W-T, K-T, A4, A5, A6, A3, BS, etc.)
  - Size reference file is not consulted for double designs
- **Canvas Width Fitting**: If a double design exceeds the canvas width (accounting for padding), it is automatically scaled down
  - Maximum allowed width = Canvas width - (2 × padding)
  - Padding is 100px on each side (left and right), so 200px total is reserved
  - Scaling maintains the original aspect ratio
  - Uses high-quality LANCZOS resampling for resizing
- **Scope**: This change only applies when a design is found in the double design folder
  - Single design folder images are unaffected and continue to use size reference rules
  - Only affects images loaded from the double design folder
- **Implementation**: Modified both `process_personalised_file_for_folder()` and `process_personalised_file()` methods
  - Uses original image dimensions by default
  - Checks if width exceeds `canvas_width_px - (2 × design_padding)`
  - Scales down proportionally if needed while maintaining aspect ratio

**Benefits**:
- Preserves original image quality: Uses original dimensions when possible
- Prevents overflow: Automatically ensures designs fit within canvas boundaries
- Maintains padding: Always preserves 100px padding on both sides
- Flexible sizing: Double designs can have any dimensions, but are constrained to fit the canvas
- Clear separation: Single and double designs have different sizing behaviors as needed

**Example**:
- Single design: SKU `12345-M-T-BLK-L` → Finds `12345.png` in single folder → Resizes to M-T dimensions from size reference
- Double design (fits): Order `12345` → Finds `12345.png` in double folder → Uses original image size (e.g., 500×500px) without any resizing
- Double design (too wide): Order `12346` → Finds `12346.png` in double folder → Original size 8000×4000px → Scaled down to fit canvas width (e.g., 6532×3266px) while maintaining aspect ratio

#### 17. Error and Warning Messages - Filename Inclusion for Single Files
**Date**: December 3, 2025
**Change**: Error and warning messages now include the filename for single file processing, matching the behavior already present for folder processing

**Details**:
- **Problem Solved**: Previously, error and warning messages for single files did not include the filename, making it difficult to identify which file had issues
- **Consistent Behavior**: Single file processing now matches folder processing behavior by including filenames in all error and warning messages
- **Comprehensive Coverage**: Filenames are now included in:
  - Warning messages for missing designs (e.g., "Could not find designs for 5 SKUs in filename.xlsx")
  - Error messages when no designs are found (e.g., "No design files found in filename.xlsx!")
  - Warning messages for missing size references (e.g., "Could not find size reference for 3 designs in filename.xlsx")
  - Exception handlers that save errors to log files (includes filename in saved error content)
- **Implementation**: Updated all error and warning message generation in:
  - `process_single_file()`: Added filename to all warning/error messages
  - `process_personalised_file()`: Added filename to all warning/error messages
  - Exception handlers: Added filename to error log content when saving errors to files
- **Format**: Uses `os.path.basename(file_path)` to show just the filename (not full path) for cleaner messages
  - Example: "Could not find designs for 5 SKUs in DTF Des-P200-P211.xlsx"
  - Falls back to "file" if file_path is not available

**Benefits**:
- Better debugging: Users can immediately identify which file has issues
- Consistent experience: Single file and folder processing now have the same level of detail in error messages
- Improved error logs: Saved error files now include filename context for easier troubleshooting
- Clearer feedback: Error and warning dialogs provide more actionable information

**Example**:
- Before: "Could not find designs for 5 SKUs: 12345, 12346, ..."
- After: "Could not find designs for 5 SKUs in DTF Des-P200-P211.xlsx: 12345, 12346, ..."

#### 18. Pocket and Sleeve Variant Detection for Personalised Button
**Date**: December 11, 2025
**Change**: Added automatic detection and processing of pocket (-P.png) and sleeve (-S.png) image variants for personalized button processing

**Details**:
- **Variant Detection**: The application now checks for pocket and sleeve variants before regular image files
  - Checks for `{OrderNumber}-P.png` (pocket) or `{OrderNumber}-S.png` (sleeve) suffixes
  - Case-insensitive matching: `-p.png`, `-P.png`, `-s.png`, `-S.png` all supported
  - Priority order: Pocket → Sleeve → Regular `.png` file
  - Works with duplicate indexes in the legacy order-only naming flow (e.g., `12345-1-P.png` for the second occurrence)
  - Note: in the newer duplicate-order SKU-based naming flow (exact filenames like `{OrderNumber}-{itemSku}.png`), the `-P.png` / `-S.png` suffix is not automatically applied
- **Pocket Dimension Overrides**: When a pocket variant is detected, target dimensions are overridden based on SKU pattern:
  - **Kids** (SKU contains "-K-"): 65mm width × 80mm height
  - **Men's/Women's** (SKU contains "-M-" or "-W-"): 80mm width × 100mm height
  - Defaults to Men's/Women's dimensions if SKU pattern is not found
- **Sleeve Dimension Overrides**: When a sleeve variant is detected, target dimensions are overridden to:
  - 100mm width × 100mm height (for all sizes, regardless of SKU)
- **Dimension Override Timing**: Dimension overrides are applied after calculating the aspect ratio but before resizing
  - Ensures proper aspect ratio preservation
  - Replaces default target dimensions from size reference configuration
- **Orientation-Based Resizing**: Resizing now uses a smart strategy based on image orientation:
  - **Landscape** (width > height): Uses target width as primary constraint, calculates height from aspect ratio
  - **Portrait/Square** (height ≥ width): Uses target height as primary constraint, calculates width from aspect ratio
  - Provides better fitting for both landscape and portrait images
- **Scope**: This feature applies **only to personalized button processing**
  - Does not affect "Normal" mode
  - Only applies to single design folder images (not double design folder)
- **Implementation**: Modified `find_design_file_vba_logic()` to detect variants and return flags
  - Returns `(file_path, design_type, is_pocket, is_sleeve)` tuple
  - Updated `process_personalised_file()` and `process_personalised_file_for_folder()` to handle variants
  - Dimension overrides integrated into existing resize logic

**Benefits**:
- Automatic variant detection: No manual configuration needed
- Proper sizing: Pocket and sleeve variants get appropriate dimensions based on product type
- Better image fitting: Orientation-based resizing ensures images fit properly regardless of orientation
- Consistent workflow: Variants are handled automatically in the same processing flow
- Clear labels: Pocket and sleeve variants are labeled correctly in the design list (e.g., "12345 (Single-Pocket)")

**Examples**:
- Order `12345` with SKU `ABC-K-T-BLK-XL`:
  - File `12345-P.png` exists → Detected as pocket → Resized to 65×80mm (Kids)
  - File `12345-S.png` exists → Detected as sleeve → Resized to 100×100mm
  - File `12345.png` exists → Regular processing → Uses size reference dimensions
  
- Order `67890` with SKU `XYZ-M-T-BLK-L`:
  - File `67890-P.png` exists → Detected as pocket → Resized to 80×100mm (Men's)
  - File `67890.png` exists → Regular processing → Uses size reference dimensions

**File Naming Examples**:
- Regular single: `12345.png`
- Pocket variant: `12345-P.png` (detected first if exists)
- Sleeve variant: `12345-S.png` (detected first if exists)
- With duplicates: `12345-1-P.png`, `12345-2-S.png`, etc.

#### 19. Remove DTF Queues Folder Button
**Date**: December 11, 2025
**Change**: Added "Remove DTF Queues Folder" button to clear folder selection and prevent files from being sent to DTF Queues folder

#### 20. Size Code Matching Enhancement - Prioritize Longer Codes
**Date**: December 11, 2025
**Change**: Improved size code matching to prioritize longer, more specific codes over shorter ones

**Details**:
- **Problem Solved**: When both shorter and longer size codes exist in the reference file (e.g., `F8` and `F8-M-T`), the shorter code could incorrectly match first
- **Solution**: Size codes are now sorted by length (longest first) before searching, ensuring more specific codes are matched before shorter ones
- **Implementation**: Added sorting step in `extract_size_code()` method
  - Codes are sorted by length in descending order before searching
  - Longer codes like `F8-M-T` are checked before shorter codes like `F8`
- **Example**:
  - Reference file contains: `F8`, `F8-M-T`, `F8-W-T`
  - SKU: `12345-F8-M-T-BLK-L`
  - Before: Could match `F8` (incorrect)
  - After: Matches `F8-M-T` (correct, more specific)
- **Benefits**:
  - More accurate size code detection
  - Prevents false matches when multiple similar codes exist
  - Ensures the most specific size code is used for sizing

#### 21. Pocket Design IDs Database - Automatic F8 Size Code Detection
**Date**: December 29, 2025
**Change**: Added automatic detection of pocket designs based on a database of design IDs, with automatic generation of F8-based size codes

**Details**:
  - **Database Location**: Configuration Workbook.xlsx, Sheet 2 (auto-loaded from config/ directory)
  - **Location**: `config/` directory (checks config/ first, then root directory for backwards compatibility)
  - **Format**: Design IDs stored in column A (first column)
  - **Auto-Load**: Automatically loaded on application startup if found in app directory
  - **Error Handling**: Gracefully handles missing file (continues without pocket detection)
- **Detection Logic**: 
  - Extracts design ID from SKU (first part before dash, e.g., `77989LG` from `77989LG-M-T-BLK-M`)
  - Checks if design ID exists in Pocket Design IDs Database
  - Also checks design ID with apparel size prefix removed (e.g., `XL39553LG` → also checks `39553LG`)
  - If found in database, treats as pocket design and uses F8-based size codes
- **F8-Based Size Code Generation**:
  - **Gender Detection**: Analyzes SKU for gender patterns:
    - `-M-` → Men's
    - `-W-` → Women's
    - `-K-` → Kids
  - **Type Detection**: Analyzes SKU for garment type patterns:
    - `-T-` → Tshirt
    - `-H-` → Hoodie
  - **Code Format**: Constructs `F8-{gender}-{type}` (always uppercase)
    - Examples: `F8-M-T`, `F8-W-T`, `F8-K-T`, `F8-M-H`, `F8-K-H`
  - **Error Handling**: If gender or type patterns are not found in SKU, returns `None` (results in missing size error/warning)
- **Priority**: Pocket design detection happens before normal size extraction logic
  - If design ID is in database, uses F8-based code generation
  - If design ID is not in database, continues with normal size extraction
- **Integration**: Generated F8 size codes are used to look up dimensions in Size Reference file
  - Size Reference file should contain entries like `F8-M-T`, `F8-W-T`, etc.
  - Uses existing case-insensitive matching in `get_size_from_reference()` method

**Benefits**:
- Automatic pocket detection: No need to manually identify pocket designs
- Consistent sizing: All pocket designs use standardized F8-based size codes
- Flexible database: Easy to add/remove design IDs from the database file
- Apparel size prefix support: Works with design IDs that have size prefixes (XL, 2XL, etc.)
- Error prevention: Returns error if SKU patterns are missing, preventing incorrect sizing

**Examples**:
- Design ID `77989LG` in database, SKU `77989LG-M-T-BLK-L`:
  - Detected as pocket design
  - Gender: `-M-` → Men's
  - Type: `-T-` → Tshirt
  - Generated code: `F8-M-T`
  - Looks up `F8-M-T` in Size Reference file
  
- Design ID `12345` in database, SKU `12345-K-H-BLK-XL`:
  - Detected as pocket design
  - Gender: `-K-` → Kids
  - Type: `-H-` → Hoodie
  - Generated code: `F8-K-H`
  - Looks up `F8-K-H` in Size Reference file
  
- Design ID `67890` in database, SKU `67890-BLK-L` (no gender/type patterns):
  - Detected as pocket design
  - Gender: Not found
  - Type: Not found
  - Returns `None` → Missing size error/warning

**File Requirements**:
- `Configuration Workbook.xlsx` must be in the `config/` directory with Pocket Design IDs in sheet "Pocket Design IDs Database" or Sheet 2
- Column A should contain design IDs (one per row)
- Design IDs should match the format extracted from SKUs (first part before dash)

#### 22. Console Logging and Run Summary Reports
**Date**: January 15, 2026
**Change**: Added comprehensive console logging system that captures all CMD output to files and generates summary reports at the end of each run

**Details**:
- **Console Log Files**: Every application run creates a new log file capturing all console output
  - **Location**: `Logs/` folder in application directory (historically documented as `Console Logs/`; current code uses `Logs/`)
  - **File Naming**: `console_log_YYYY-MM-DD_HH-MM-SS.txt` (timestamped, one file per run)
  - **Content**: Complete record of all stdout and stderr output during the run
  - **Automatic**: Logging starts automatically when application launches
  - **Output**: Always written to the log file; also mirrored to a console when one exists
- **Anomaly Tracking**: Comprehensive tracking of all anomalies during the run
  - **Error Counter**: Tracks total errors from print statements, stderr, and tracebacks
  - **Warning Counter**: Tracks total warnings from print statements and dialogs
  - **Exception Counter**: Tracks unhandled exceptions
  - **Dialog Counters**: Tracks error dialogs and warning dialogs separately
  - **Traceback Counter**: Tracks tracebacks detected in stderr
- **Anomaly Logging to Console**: All anomalies are clearly marked and printed to console (CMD)
  - **Unhandled Exceptions**: Displayed with full tracebacks and clear markers
  - **Error Dialogs**: Logged to console with timestamp and clear formatting
  - **Warning Dialogs**: Logged to console with timestamp and clear formatting
  - **Stderr Errors**: Detected and logged to console with clear markers
  - **Print Statement Errors/Warnings**: Detected and logged to console
- **Summary Report**: Each console log file includes a comprehensive summary report at the end
  - **Application Times**: Start time and end time with timestamp
  - **Runtime**: Total runtime calculated and displayed (hours, minutes, seconds format)
  - **Anomaly Statistics**: Complete breakdown of all anomalies detected:
    - Total Errors
    - Total Warnings
    - Unhandled Exceptions
    - Error Dialogs
    - Warning Dialogs
    - Tracebacks
  - **Status Assessment**: Overall status of the run:
    - ✓ Success (no anomalies detected)
    - ⚠ Warnings detected
    - ⚠ Errors detected
    - ✗ Critical issues (unhandled exceptions detected)
  - **Log Locations**: Information about where detailed error logs are saved
  - **Console Output**: Summary is also printed to console when application closes
- **Implementation**:
  - `setup_console_logging()`: Initializes console logging at application startup
  - `close_console_logging()`: Closes log file and generates summary report when application exits
  - Tee class: Writes to both console and file simultaneously
  - Statistics tracking: Global counters track all anomalies during the run
  - Automatic integration: Works seamlessly with existing error logging system

**Benefits**:
- **Complete Record**: Every run has a complete log file with all console output
- **Easy Debugging**: Summary reports provide quick overview of what happened during each run
- **Anomaly Visibility**: All anomalies are clearly visible in console for immediate feedback
- **Historical Tracking**: Timestamped log files allow tracking issues over time
- **Comprehensive Coverage**: All output (stdout, stderr, errors, warnings) is captured
- **No Performance Impact**: Logging is efficient and doesn't slow down the application

**Example Summary Report**:
```
================================================================================
RUN SUMMARY REPORT
================================================================================
Application End Time: 2025-01-15 14:30:45
Total Runtime: 5m 23s

ANOMALIES DETECTED:
--------------------------------------------------------------------------------
  Total Errors:           3
  Total Warnings:         2
  Unhandled Exceptions:   0
  Error Dialogs:          1
  Warning Dialogs:        1
  Tracebacks:             0

STATUS: ⚠ Run completed with ERRORS detected.

NOTE: Detailed error and warning logs are saved in:
  - Errors and Warnings/ folder (individual error/warning files)
  - This console log file (complete output with timestamps)

================================================================================
```

**File Structure**:
- `Logs/console_log_2025-01-15_14-25-22.txt` - Console log for each run
- `Errors and Warnings/error_2025-01-15_1.txt` - Individual error files (existing)
- `Errors and Warnings/warning_2025-01-15_1.txt` - Individual warning files (existing)

#### 23. Missing Size Reference Warning Fix and Run Summary Report Fix
**Date**: January 2, 2026
**Change**: Fixed missing size reference warnings not appearing and corrected run summary report location

**Details**:
- **Missing Size Reference Warning Fix**:
  - **Problem**: Warnings for missing size references were not appearing when size codes like "YXS" couldn't be found in the reference file
  - **Root Cause**: The `extract_size_code` function was only using fallback logic when the size reference file was not loaded, but not when it was loaded but didn't contain the size code
  - **Solution**: Updated `extract_size_code` to always use fallback logic, even when the reference file is loaded. This ensures size codes are extracted from SKUs (like "YXS" from "13828LG-SX187-CTNPNK-YXS") even if they're not in the reference file
  - **Result**: Missing size reference warnings now appear correctly when size codes are found in SKUs but not in the reference file
  - **Implementation**: Modified `src/size_code_extractor.py` to always run fallback extraction logic after checking the reference file
- **Run Summary Report Location Fix**:
  - **Problem**: Run summary reports were being saved to both Console Logs and Errors and Warnings folders
  - **Root Cause**: The summary report was printed using `print()`, which was intercepted by the logging system. Since the report contains the word "WARNING", it was being saved as an error file
  - **Solution**: Changed the summary report output to use `sys.__stdout__.write()` instead of `print()`, bypassing the logging system
  - **Result**: Run summary reports now only appear in Console Logs folder, not in Errors and Warnings folder
  - **Implementation**: Modified `src/logging_utils.py` in `close_console_logging()` function

**Benefits**:
- **Accurate Warnings**: Users now receive proper warnings when size references are missing, helping them identify and fix issues
- **Cleaner Logs**: Run summary reports are only in Console Logs, making it easier to find them and reducing clutter in Errors and Warnings folder
- **Better User Experience**: All warnings and errors now appear correctly, providing complete feedback about processing issues

---

## Installation & Setup

### Requirements
- Python 3.7 or higher
- Required packages:
  - `pandas` (>=2.0.0)
  - `openpyxl` (>=3.1.0)
  - `Pillow` (>=10.0.0)
  - `tkinter` (usually included with Python)

### Installation Steps

1. **Download/Clone the application files**
   - `queue_app.py` (main application)
   - `run_queue_app.bat` (Windows launcher, optional)
   - `requirements.txt` (dependencies, optional)

2. **Install Python dependencies**
   ```bash
   pip install pandas openpyxl Pillow
   ```
   Or use the batch file which installs automatically.

3. **Run the application**
   - **Windows (recommended)**: Double-click `run_queue_app.bat` (PowerShell: `.\run_queue_app.bat`)
     - Installs dependencies, then launches with `pythonw` (no persistent CMD window)
   - **Manual (no console)**: Run `pythonw queue_app.py`
   - **Manual (debug console)**: Run `python queue_app.py`

### First-Time Setup

1. **Select Input File**: Click "Select DTF Des File" and choose your DTF Des file
2. **Size Reference**: Automatically loaded from Configuration Workbook.xlsx (sheet "Size References" or Sheet 1) in config/ directory
   - No manual selection needed - auto-loaded on startup
3. **Select Designs Folder**: Choose folder containing design image files
4. **For Personalised Mode**: Also select Single Design Folder and Double Design Folder

All selections are automatically saved in `queue_app_settings.json` and will be restored on next launch.

### Canvas Configuration

The application allows you to customize canvas dimensions and DPI:

1. **Canvas Size**: Adjust width and height using the spinboxes in the "Canvas Information" panel
   - Width: 100-2000mm (default: 570mm)
   - Height: 100-10000mm (default: 3000mm)
   - Changes require clicking the processing button again to apply
   - **Printing machine reference**: PET/DTF film is 600 mm wide; 15 mm silver hold plates on each side leave **570 mm** usable width for PNG designs (see Canvas Arrangement / Canvas Specifications)

2. **DPI Settings**: Adjust DPI for output quality using the spinbox in the "Canvas Information" panel
   - Range: 72-600 DPI (default: 300 DPI)
   - Higher DPI = better quality but larger file sizes
   - Changes require clicking the processing button again to apply

3. **Color Bar**: Place a color bar image file (`Color Bar.png`, `ColorBar.png`, `color_bar.png`, or `colorbar.png`) in the `config/` directory (or root directory for backwards compatibility)
   - Automatically detected and loaded on startup
   - Added to all generated PNG files (right-aligned at the top)

---

## User Guide

### Basic Workflow

#### Normal Mode

**Single File Processing:**

1. **Prepare Input File**
   - DTF Des file with Item SKU column
   - Each row contains a SKU (e.g., `77989LG-M-T-BLK-M`)

2. **Load Files**
   - Click "Select DTF Des File" → Choose your DTF Des file
   - Click "Select Designs Folder" → Choose folder with design images
   - (Optional) Click "Select DTF Queues Folder" → Choose folder for RAR upload
   - (Optional) Click "Remove DTF Queues Folder" → Clear folder selection to prevent files from being sent
   - **Note**: Size Reference is automatically loaded from Configuration Workbook.xlsx (sheet "Size References" or Sheet 1) in the config/ directory

3. **Process**
   - Click "Normal" button
   - Application will:
     - Extract SKUs from input file
     - Match design files by SKU
     - Extract size codes and match with reference
     - Resize designs based on size reference
     - Arrange on canvas

4. **Preview & Save**
   - Review arranged designs in preview panel (scroll to see the full layout)
   - (Optional) Adjust canvas size or DPI in "Canvas Information" panel if needed (requires reprocessing)
   - Click "Save PNG(s)" to save PNG files
   - RAR archive is automatically created and copied to DTF Queues folder (if configured)

**Folder Processing:**

1. **Prepare Input Folder**
   - Folder containing multiple DTF Des files
   - Each file should have Item SKU column

2. **Load Files**
   - Click "Select Input Folder" → Choose folder with DTF Des files
   - Click "Select Designs Folder" → Choose folder with design images
   - (Optional) Click "Select DTF Queues Folder" → Choose folder for RAR upload
   - (Optional) Click "Remove DTF Queues Folder" → Clear folder selection to prevent files from being sent
   - **Note**: Size Reference is automatically loaded from Configuration Workbook.xlsx (sheet "Size References" or Sheet 1) in the config/ directory

3. **Process**
   - Click "Normal" button
   - Application will:
     - Process each DTF Des file in the folder
     - Create a size determination log for each file (in `Logs/`)
     - Show a combined preview of all designs from all files
     - Store batches for each file separately

4. **Preview & Save**
   - Review combined preview in preview panel
   - Click "Save PNG(s)" to save
   - Each input file will be saved as separate PNG files with correct labels
   - RAR archive containing all PNG files is automatically created and copied to DTF Queues folder (if configured)

#### Personalised Mode

**Single File Processing:**

1. **Prepare Input File**
   - DTF Des file with:
     - Order Number column (for finding design files)
     - Item SKU column (for size reference)

2. **Load Files**
   - Select input file (with Order Number and Item SKU columns)
   - Select Single Design Folder
   - Select Double Design Folder
   - (Optional) Select DTF Queues Folder (or click "Remove DTF Queues Folder" to clear selection)
   - **Note**: Size Reference is automatically loaded from Configuration Workbook.xlsx (sheet "Size References" or Sheet 1) in the config/ directory

3. **Process**
   - Click "Personalised" button
   - Application will:
     - Find single designs first (checks for -P.png and -S.png variants before regular .png)
     - Detect pocket/sleeve variants automatically
     - Resize single designs:
       - Regular: Based on size reference from Item SKU
       - Pocket: Override dimensions based on SKU (Kids: 65×80mm, Men's/Women's: 80×100mm)
       - Sleeve: Override to 100×100mm for all sizes
     - Use orientation-based resizing (width constraint for landscape, height constraint for portrait)
     - Then find double designs
     - Use original image size for double designs (no size reference rules)
     - Scale down double designs if they exceed canvas width (with padding preserved)
     - Arrange on canvas

4. **Save**
   - Click "Save PNG(s)" to save PNG files
   - RAR archive is automatically created and copied to DTF Queues folder (if configured)

**Folder Processing:**

1. **Prepare Input Folder**
   - Folder containing multiple DTF Des files
   - Each file should have Order Number and Item SKU columns

2. **Load Files**
   - Click "Select Input Folder" → Choose folder with DTF Des files
   - Select Single Design Folder
   - Select Double Design Folder
   - (Optional) Select DTF Queues Folder (or click "Remove DTF Queues Folder" to clear selection)
   - **Note**: Size Reference is automatically loaded from Configuration Workbook.xlsx (sheet "Size References" or Sheet 1) in the config/ directory

3. **Process**
   - Click "Personalised" button
   - Application will:
     - Process each DTF Des file in the folder
     - Create a size determination log for each file (in `Logs/`)
     - Find single and double designs for each order
     - Check for pocket (-P.png) and sleeve (-S.png) variants first
     - Resize single designs:
       - Regular: Based on size reference from Item SKU
       - Pocket: Override dimensions based on SKU (Kids: 65×80mm, Men's/Women's: 80×100mm)
       - Sleeve: Override to 100×100mm for all sizes
     - Use orientation-based resizing (width constraint for landscape, height constraint for portrait)
     - Use original image size for double designs (no size reference rules)
     - Scale down double designs if they exceed canvas width (with padding preserved)
     - Show a combined preview of all designs from all files
     - Store batches for each file separately

4. **Save**
   - Click "Save PNG(s)" to save
   - Each input file will be saved as separate PNG files with correct labels
   - RAR archive containing all PNG files is automatically created and copied to DTF Queues folder (if configured)

#### Missing Logo Mode (Single File)

1. **Select Input File**
   - Click "Select Input File" and choose a DTF Des file (.xlsx, .xls, or .csv)

2. **Select Folders**
   - Select at least one of the following:
     - Single Design Folder (for personalized designs)
     - Double Design Folder (for personalized designs)
     - Normal Designs Folder (for Normal mode designs)

3. **Process**
   - Click "Missing Logo" button
   - Application will:
     - First search personalized folders (Single/Double Design Folders) using Order Number and VBA logic
     - If not found, search Normal Designs Folder using design ID extracted from SKU
     - Apply appropriate sizing rules based on where design was found:
       - From personalized: Uses personalized sizing (size reference, pocket/sleeve overrides, double scaling)
       - From Normal Designs folder: Uses standard sizing (size reference only)
     - Arrange on canvas

4. **Preview & Save**
   - Review arranged designs in preview panel (scroll to see the full layout)
   - Click "Save PNG(s)" to save PNG files

#### Missing Logo Mode (Folder Processing)

1. **Select Input Folder**
   - Click "Select Input Folder" and choose a folder containing DTF Des files

2. **Select Folders**
   - Select at least one of the following:
     - Single Design Folder (for personalized designs)
     - Double Design Folder (for personalized designs)
     - Normal Designs Folder (for Normal mode designs)

3. **Process**
   - Click "Missing Logo" button
   - Application will:
     - Process each DTF Des file in the folder
     - Create a size determination log for each file (in `Logs/`)
     - For each order, search personalized folders first, then Normal Designs folder
     - Apply appropriate sizing rules based on where each design was found
     - Show a combined preview of all designs from all files
     - Each file starts on a new batch in preview (for easy identification)
     - Store batches for each file separately

4. **Save**
   - Click "Save PNG(s)" to save
   - Each input file will be saved as separate PNG files with correct labels
   - RAR archive containing all PNG files is automatically created and copied to DTF Queues folder (if configured)

### File Naming Conventions

#### Design Files (Normal)
- Design files can match SKU exactly or use design code (first part before dash)
- Example: SKU `77989LG-M-T-BLK-M` → Files: `77989LG-M-T-BLK-M.png` or `77989LG.png`
- **Apparel Size Prefix Handling**: Automatically handles size prefixes in SKUs
  - If SKU is `XL39553LG-I-M-T-BLK-XL`, it first searches for `XL39553LG.png`
  - If not found, automatically removes "XL" prefix and searches for `39553LG.png`
  - Works with all common size prefixes: XS, S, M, L, XL, 2XL, 3XL, 4XL, XXL, XXXL, XXXXL
  - Prevents false warnings when design files exist without size prefixes
- Case-insensitive matching

#### Design Files (Personalised)
- **Single designs (non-duplicate order rows)**:
  - Regular: `{OrderNumber}.png`
  - Pocket variant: `{OrderNumber}-P.png` (checked first if exists)
  - Sleeve variant: `{OrderNumber}-S.png` (checked first if exists)
  - Case-insensitive: `-p.png`, `-P.png`, `-s.png`, `-S.png` all supported
  - Matching is exact on the filename stem (no prefix matching)
- **Duplicate order rows (same `OrderNumber` appears multiple times in the input)**:
  - `duplicateIndex == 0`: `{OrderNumber}-{itemSku}.png`
  - `duplicateIndex > 0`: `{OrderNumber}-{duplicateIndex}-{itemSku}.png`
  - SKU normalization for filenames: any `/` or `\` in the SKU is converted to `-` before searching
  - If the SKU-based filename is not found, the code falls back to legacy order-only names:
    - `{OrderNumber}.png`
    - and (when `duplicateIndex > 0`) `{OrderNumber}-{duplicateIndex}.png`
  - In this SKU-based duplicate flow, pocket/sleeve `-P.png` / `-S.png` suffix is not automatically added
- **Double designs**:
  - The app searches single folder first, then double folder, using the same naming rules above

### Configuration Workbook Format

The Configuration Workbook.xlsx file should be located in the `config/` directory and contain two sheets:

#### Sheet "Size References" (or Sheet 1): Size Reference
The size reference sheet should have:
- **Size Width** column: Width in millimeters
- **Size Height** column: Height in millimeters
- **Merge** column (Column I): Size codes like `M-T`, `A4`, etc.
  - **Format Options**:
    - **Simple format**: `M-T`, `W115`, `K-SS` (no brackets)
    - **Bracket format**: `K-SS (YS) (YXS)`, `W115 (S)`, `M-T (XS) (S)` (with bracket codes)
  - **Bracket Support**: 
    - Base code (text before brackets) is used for primary matching
    - Bracket codes (in parentheses) allow multiple SKU patterns to match the same entry
    - Example: `K-SS (YS) (YXS)` matches SKUs containing `K-SS`, `YS`, or `YXS`
  - **Note**: Asterisks should not be used (removed from data)
  - Whitespace is automatically trimmed during processing
  - Used for matching size codes in SKUs
  - **Merge_clean** column is automatically created with base code (text before brackets)
  - **Merge_brackets** column is automatically created with list of bracket codes
- **Optional multi-position columns**:
  - `Number of Designs` (was Number of Positions): Leave blank/`1` for normal single-design flow; set `2`/`3`/`4`/`5` for multi-design flow
  - `Suffix` / `Position`: Position suffix used in file search (e.g., `x93`, `x94`, `F`, `B`)
  - For multi-position entries, use one row per position with its own width/height

#### Sheet "Override Print Size" (optional)
- **SKU Contain**: If the item SKU contains this value, apply the override (longest match wins)
- **Width** / **Height**: Print size in mm; if blank on a matching row, falls back to pocket sizes (65×80 for kids `-K-`, else 80×100)

#### Sheet "Pocket Design IDs Database" (or Sheet 2): Pocket Design IDs Database
The pocket design IDs sheet should have:
- **Column A (first column)**: Design IDs (e.g., `137063LG`, `130085LG`)
  - One design ID per row
  - Used to identify pocket designs and generate F8-based size codes

### Output Files

- **Location**: `Output/YYYY-MM-DD/` under the application directory (one subfolder per day)
- **Format**: PNG files at 300 DPI
- **Naming**: 
  - Single batch: `{input_filename}.png`
  - Multiple batches: `{input_filename}_Part {N}.png`
  - Folder processing: Each input file generates separate PNG files with its own filename
- **Top Text**: Contains "des-" text from source file and PART number if applicable
  - **Important**: Each PNG file displays the label extracted from its own source file
  - When processing a folder, each PNG correctly shows the label from its corresponding input file
- **RAR Archives**: Automatically created after saving PNG files
  - Location: Same as PNG files (in `Output/YYYY-MM-DD/`)
  - Naming: Based on source file(s) (e.g., `P200-P211.rar` or `P200-P211-P300-and-5-more.rar`)
  - Automatically copied to DTF Queues folder if configured
  - Requires WinRAR or 7-Zip to be installed

---

## Technical Details

### Architecture

**Main Class**: `DesignArrangerGUI` (internal class name for Queue App)
- Tkinter-based GUI application (~340 lines)
- Object-oriented design with state management
- Settings persistence via JSON file
- Dependency injection support for testing and flexibility

**Modular Structure**:
- **Core Modules** (`src/`): 23 Python modules containing core business logic
  - Canvas operations (arranging, creation, placement)
  - Design processing workflows
  - File operations (searching, loading, handling)
  - Image processing (resizing, utilities)
  - Size reference and code extraction
  - Logging and error handling
  - Dependency injection container
  - Settings management
  - RAR archive utilities
  - **Interfaces** (`src/interfaces.py`): 5 abstract base classes defining service contracts
    - `ISettingsManager`: Settings management service interface
    - `ISizeReferenceProvider`: Size reference lookup service interface
    - `IDesignProcessor`: Design processing service interface
    - `ICanvasArranger`: Canvas arrangement service interface
    - `ICanvasCreator`: Canvas creation service interface
- **GUI Helpers** (`gui_helpers/`): Package under `scripts/gui_helpers/` (canvas, common, processing, selection, settings, ui, etc.)
  - File selection UI
  - Processing coordination and UI updates
  - Preview canvas rendering
  - Progress management
  - Save operations
  - Canvas settings
  - UI builder utilities (`gui_ui_builder_impl.py`, `gui_ui_builder_preview.py`)
  - Lightweight ttk theme (`common/gui_theme.py`)
  - Size reference UI handling

**Interface-Based Design**:
The application follows SOLID principles with well-defined interfaces for key services:
- **Dependency Inversion Principle (DIP)**: High-level modules depend on abstractions (interfaces) rather than concrete implementations
- **Interface Segregation Principle (ISP)**: Interfaces are focused and segregated by responsibility
- **Open/Closed Principle (OCP)**: Services can be extended without modification through interface-based design
- **Benefits**: Enables dependency injection, improves testability, and allows for easy swapping of implementations

**Total Codebase**:
- Main application: `queue_app.py` (340 lines)
- Core modules: 23 Python files in `src/`
- GUI helpers: package under `scripts/gui_helpers/` (canvas, common, processing, selection, settings, ui, utilities, reference, preview)
- Test suite: 34 test files in `tests/`
- Modular architecture with clear separation of concerns

### Key Algorithms

#### 1. Size Code Extraction
```python
def extract_size_code(self, sku):
    # Gets all size codes from Merge_clean column
    # Searches SKU string for each code
    # Returns first match found
```

**Process**:
1. Load all unique values from `Merge_clean` column
2. Filter out empty/NaN values
3. Convert to uppercase
4. Sort codes by length (longest first) to prioritize more specific matches
5. Search SKU (uppercase) for each code in sorted order
6. Return first match found (most specific match)

#### 2. Design Packing Algorithm
```python
def pack_designs(self, designs):
    # Arranges designs on canvas
    # Splits into batches if exceeds canvas height
```

**Process**:
1. **Pass 1**: Rotate landscape (non-A3) designs +90° to portrait when it helps packing (skip if free beside &lt; 200 mm **and** next logo cannot share the row)
2. Place designs row by row left to right using current widths
3. Fixed ~8 mm gap between designs; ~2 mm left start; ~15 mm between rows; color-bar reservation on the right
4. When a row is full: **Pass 2** may rotate portraits back to landscape if spare width allows, then place the row
5. Start a new row below; split into batches if total height > canvas height

#### 3. Size Matching
```python
def get_size_from_reference(self, size_code):
    # Matches size code with reference file
    # Returns width and height in pixels
```

**Process**:
1. Search `Merge_clean` column for size code
2. Get corresponding `Size Width` and `Size Height`
3. Convert mm to pixels (300 DPI)
4. Return dimensions
5. **A3 only**: `load_and_resize_design()` rotates the image 90° and swaps width/height before resize (see A3 Forced Landscape in Recent Changes)

#### 4. Image Orientation (`image_orientation.py`)

**IronOn auto-orientation** (`ENABLE_AUTO_ORIENTATION`):
- Runs only when SKU/order contains `IronOn` (case-insensitive)
- Compares original vs 90°-rotated layout; picks orientation with larger output area
- Console log when rotated: `orientation=rotated_90 area_orig=... area_rot=... -> using rotated`

**A3 forced landscape** (`ENABLE_A3_LANDSCAPE`):
- Applies to all A3 size codes in every processing mode
- Rotates image 90° clockwise, swaps size-reference box to landscape, disables IronOn auto-orient for that design
- Console log: `a3_landscape=forced rotate=90 size_box_swapped original_box=... swapped_box=...`

### Canvas Specifications

- **Default Width**: 570mm = ~6732 pixels (at 300 DPI)
- **Default Height**: 3000mm = ~35433 pixels (at 300 DPI)
- **Default DPI**: 300 (high-quality printing standard)
- **Printing machine / DTF film (why default width is 570 mm)**:
  - Saved PNGs are printed on the DTF / PET film
  - Full PET / DTF film width: **600 mm**
  - Silver holding plate: **15 mm** on each side (left + right)
  - Usable design width: **570 mm** = 600 − 15 − 15
  - Canvas width should stay at 570 mm for this machine setup; 600 mm is the physical film, not the printable area
- **Canvas Size Customization**: 
  - Width: Adjustable from 100-2000mm via UI spinbox in Canvas Information panel
  - Height: Adjustable from 100-10000mm via UI spinbox in Canvas Information panel
  - Changes require reprocessing designs to take effect
- **DPI Customization**: 
  - Adjustable from 72-600 DPI via UI spinbox in Canvas Information panel
  - Changes require reprocessing designs to take effect
- **Gaps** (configurable in `size_reference.py`): ~8 mm between designs, ~2 mm left/start, ~15 mm between rows, ~12 mm before color bar (+ bar width)
- **Background**: Transparent (RGBA)
- **Color Bar**: Optional, automatically loaded from `config/` directory (or root for backwards compatibility) if available
  - Supported filenames: `Color Bar.png`, `ColorBar.png`, `color_bar.png`, `colorbar.png`
  - Added right-aligned at the top of canvas

### File Formats Supported

- **Input**: DTF Des files (.xlsx, .xls, .csv)
- **Design Images**: PNG only (`.png`)
- **Output**: PNG (RGBA, 300 DPI)
- **Settings**: JSON

### Performance Considerations

- **Large Files**: Handles large DTF Des files efficiently
- **Image Processing**: Uses PIL/Pillow for image operations
- **Memory**: Removes PIL image size limit for large canvases
- **Batch Processing**: Automatically splits large arrangements into batches

---

## File Structure

```
Queue App/
│
├── queue_app.py          # Main application file
├── run_queue_app.bat         # Windows launcher (deps + pythonw, no CMD with GUI)
├── requirements.txt                # Python dependencies
├── README.md                       # Quick start guide
├── DOCUMENTATION.md                # This file
│
├── src/                            # Source code package (core modules)
│   ├── __init__.py
│   ├── canvas_arranger.py          # Canvas packing algorithm
│   ├── canvas_creation.py          # Canvas image creation
│   ├── canvas_placement.py         # Design placement logic
│   ├── design_processing.py        # Design processing workflows
│   ├── design_processor.py         # Design processing coordination
│   ├── di_container.py             # Dependency injection container
│   ├── exceptions.py               # Custom exception classes
│   ├── file_handlers.py            # File operations
│   ├── file_loaders.py             # File loading utilities
│   ├── file_search.py              # Design file searching
│   ├── file_utilities.py           # File utility functions
│   ├── gui_components.py           # UI component rendering
│   ├── image_resizing.py           # Image resizing logic
│   ├── image_orientation.py        # IronOn auto-orientation and A3 forced landscape
│   ├── image_utils.py              # Image utility functions
│   ├── interfaces.py               # Interface definitions
│   ├── logging_utils.py            # Logging functionality
│   ├── rar_utils.py                # RAR archive operations
│   ├── service_factory.py          # Service factory
│   ├── settings_manager.py         # Settings management
│   ├── size_code_extractor.py      # Size code extraction
│   ├── size_reference.py           # Size reference handling
│   └── vba_file_search.py          # VBA-style file search logic
│
├── scripts/gui_helpers/            # GUI helper package (facades + impl)
│   ├── common/
│   │   ├── gui_common.py           # Shared dialog/label helpers
│   │   ├── gui_progress.py         # Progress bar updates
│   │   └── gui_theme.py            # One-shot ttk theme + color constants
│   ├── canvas/
│   │   ├── gui_ui_builder_impl.py  # Left panel / create_ui
│   │   ├── gui_ui_builder_preview.py
│   │   ├── gui_preview*.py         # Preview draw / helpers / controls
│   │   └── ...
│   ├── processing/                 # Arrange / folder / mode processors
│   ├── selection/                  # File/folder pickers
│   ├── settings/                   # Persist/restore paths
│   └── ui/                         # Facade re-exports for create_ui, etc.
│
├── config/                         # Configuration files & data
│   ├── queue_app_settings.json   # Auto-saved settings
│   ├── Configuration Workbook.xlsx     # Combined file: Size Reference (sheet "Size References") + Pocket Design IDs (sheet "Pocket Design IDs Database")
│   └── Color Bar.png                   # Color bar image (optional)
│
├── scripts/                        # Utility scripts
│   ├── profile_performance.py      # Performance profiling script
│   └── run_compliance_check.py     # Compliance check script
│
├── docs/                           # Documentation
│   ├── DOCUMENTATION.md            # Full application documentation
│   ├── README.md                   # Documentation overview
│   └── internal/                   # Internal development documents
│       ├── ARCHITECTURAL_COMPLIANCE_CHECKLIST.txt
│       ├── COMPLIANCE_REPORT_DESIGN_ARRANGER.md
│       └── compliance_results.json
│
├── archive/                        # Archived/backup files
│
├── tests/                          # Test suite (34 test files)
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration and fixtures
│   ├── run_tests.py                # Test runner script
│   └── test_*.py                   # Test files for all modules
│
├── Output/                         # Generated PNG files by date (created automatically)
│   └── YYYY-MM-DD/
│       ├── filename.png
│       ├── filename_Part 1.png
│       └── ...
│
├── Missing Size Reference/         # Exported rows with missing size references (created automatically)
│   ├── DTF Des 100 (YYYY-MM-DD_HH-MM-SS).xlsx
│   ├── DTF Des 101 (YYYY-MM-DD_HH-MM-SS).xlsx
│   └── ...
│
└── Logs/                           # Console + size determination logs (created automatically)
    ├── console_log_YYYY-MM-DD_HH-MM-SS.txt
    ├── (input_stem) size_determination_YYYY-MM-DD_HH-MM-SS.txt
    └── ...
```

### Configuration Files

**Settings File Location**: `config/queue_app_settings.json` (checks `config/` directory first, then root directory for backwards compatibility)

**Configuration Files Location**: All configuration files are in `config/` directory:
- `queue_app_settings.json` - Application settings
- `Configuration Workbook.xlsx` - Combined file containing:
  - Sheet "Size References" (or Sheet 1): Size Reference (size dimensions and merge text, supports bracket codes)
  - Sheet "Pocket Design IDs Database" (or Sheet 2): Pocket Design IDs Database (design IDs in column A)
- `Color Bar.png` - Color bar image (auto-loaded, optional)

`queue_app_settings.json`:
```json
{
  "input_file": "path/to/input.xlsx",
  "input_folder_path": "path/to/input/folder",
  "size_reference_file": null,  // Not used - auto-loaded from Configuration Workbook.xlsx
  "designs_folder": "path/to/designs",
  "single_designs_folder": "path/to/single",
  "double_designs_folder": "path/to/double",
  "dtf_queues_folder": "path/to/dtf/queues"
}
```

**Note**: Only the active input method (either `input_file` or `input_folder_path`) is saved. If both are present, the last used one takes precedence. All other selections are automatically saved when made and restored on next launch.

---

## Troubleshooting

### Common Issues

#### 1. "No SKU column found"
**Problem**: Input file doesn't have a column with "SKU" in the name
**Solution**: Ensure your DTF Des file has a column named "Item SKU" or contains "SKU" in the column name

#### 2. "Could not find size reference"
**Problem**: Size code from SKU not found in size reference file
**Solution**: 
- Check that size code exists in Merge column (Column I) of size reference file
- Verify size code format matches (e.g., `M-T` vs `M-T`)
- Check for typos in SKU or reference file
- **Note**: Rows with missing size references are automatically exported to "Missing Size Reference" folder
- After adding the missing size codes to your reference file, you can load the exported file and process it again
- **Pocket Designs**: If using Pocket Design IDs Database, ensure:
  - Design ID is in the database (column A of Configuration Workbook.xlsx, sheet "Pocket Design IDs Database" or Sheet 2)
  - SKU contains gender pattern (`-M-`, `-W-`, or `-K-`) and type pattern (`-T-` or `-H-`)
  - Size Reference file contains corresponding F8-based codes (e.g., `F8-M-T`, `F8-W-T`, etc.)

#### 3. "No design files found"
**Problem**: Design files don't match SKU/Order Number
**Solution**:
- For Normal: ensure filenames match search stems used by the mode (design code-based stems; for multi-position rows use `{DesignCode}-{Position}`)
- For Personalised: ensure filenames follow order-based naming (`{OrderNumber}.png`; for multi-position rows use `{OrderNumber}-{Position}.png`)
- If SKU contains `plainlg`, the app intentionally skips design search and missing-design warnings for that row

#### 4. Designs not resizing correctly
**Problem**: Designs appear wrong size on canvas
**Solution**:
- Verify size reference file has correct dimensions
- Check that size code matching is working (see size code extraction)
- Ensure Size Width and Size Height columns have valid values

#### 5. "Failed to create Output folder"
**Problem**: Permission issue or disk full
**Solution**:
- Check write permissions in application directory
- Ensure sufficient disk space
- Run application as administrator if needed

#### 6. Preview not showing designs
**Problem**: Designs arranged but preview is blank
**Solution**:
- Use scrollbars or the mouse wheel to pan (tall or multi-batch layouts may start off-screen)
- Check that designs were actually loaded (check statistics label)
- Check console logs for `event=preview_drawn` or drawing errors

#### 7. `WARNING: Ignoring invalid distribution ~ip` when launching
**Problem**: `run_queue_app.bat` prints pip warnings about an invalid distribution named `~ip` (sometimes other `~...` names) during "Installing/Updating dependencies..."
**Solution**:
- The warning is from **pip**, not from Queue App; the GUI can still start successfully
- Cause is usually an interrupted pip upgrade that left a tilde-prefixed junk folder in user site-packages
- Close the app, then delete any folders/files whose names start with `~` under your Python `site-packages` directory (for Microsoft Store Python 3.11 this is under `%LOCALAPPDATA%\Packages\PythonSoftwareFoundation.Python.3.11_...\LocalCache\local-packages\Python311\site-packages`)
- Re-run `.\run_queue_app.bat`; the warnings should stop
- Optional check: `python -m pip check`

#### 8. All PNG files showing same label when processing folder
**Problem**: When processing multiple files from a folder, all PNG files display the same label
**Solution**: 
- Each PNG file correctly extracts and displays the label from its own source file
- Verify that each input file has a unique filename with "des-" prefix

#### 9. Missing Size Reference Export
**Problem**: How to handle rows with missing size references
**Solution**:
- The application automatically exports all rows with missing size references to a file in "Missing Size Reference" folder
- Filename format: `{original_filename} (YYYY-MM-DD_HH-MM-SS).xlsx` (one file per source DTF Des)
- The exported file contains complete rows with all columns and headers
- **Workflow**:
  1. Process your DTF Des file(s) - missing rows are automatically exported
  2. Check the "Missing Size Reference" folder for the exported file
  3. Add the missing size codes to your size reference file (Merge column, Column I)
  4. Load the exported file in the application and process it again
  5. All designs should now have proper size references
- **Note**: When processing multiple files, all missing rows are combined into one export file

#### 10. RAR Creation Failed
**Problem**: RAR archive is not being created
**Solution**:
- Ensure WinRAR or 7-Zip is installed on your system
- WinRAR is preferred (creates `.rar` format)
- 7-Zip can be used as fallback (creates `.7z` format)
- Check that the application has write permissions in the Output folder
- Review error details in `Logs/console_log_*.txt`

#### 11. Pocket Design Not Detected or Missing Size Error
**Problem**: Design ID is in Pocket Design IDs Database but getting missing size error, or pocket design not being detected
**Solution**:
- **Database File**: Ensure `Configuration Workbook.xlsx` is in the `config/` directory with Pocket Design IDs in sheet "Pocket Design IDs Database" or Sheet 2 (column A)
- **Database Format**: Verify design IDs are in column A (first column) of the database file
- **Design ID Match**: Check that the design ID extracted from SKU matches exactly what's in the database
  - Design ID is the first part before the first dash (e.g., `77989LG` from `77989LG-M-T-BLK-M`)
  - The system also checks design IDs with apparel size prefixes removed (e.g., `XL39553LG` → also checks `39553LG`)
- **SKU Patterns**: For pocket designs, SKU must contain:
  - Gender pattern: `-M-` (men's), `-W-` (women's), or `-K-` (kids)
  - Type pattern: `-T-` (tshirt) or `-H-` (hoodie)
  - If either pattern is missing, the system returns a missing size error
- **Size Reference**: Ensure Size Reference file contains the corresponding F8-based codes:
  - `F8-M-T`, `F8-W-T`, `F8-K-T`, `F8-M-H`, `F8-K-H`
  - Codes should be in the Merge column (Column I) of the Size Reference file
- **Console Output**: Check console for messages about database loading:
  - "Pocket Design IDs Database loaded from: ... (Pocket Design IDs Database)" or "(Sheet 2)" (success)
  - "Configuration Workbook.xlsx not found in config/ directory" (file missing, but continues without error)

#### 12. Design File Not Found
**Problem**: Design file cannot be found even though it exists
**Solution**:
- The application uses multiple matching strategies (in order):
  1. Exact match with design code (first part of SKU before dash)
  2. Case-insensitive match with design code
  3. Full SKU match
  4. **Apparel Size Prefix Removal**: If initial search fails, removes size prefixes and searches again
     - Example: SKU `XL39553LG-I-M-T-BLK-XL` → searches for `XL39553LG.png` first
     - If not found, removes "XL" and searches for `39553LG.png`
     - Supported prefixes: XS, S, M, L, XL, 2XL, 3XL, 4XL, XXL, XXXL, XXXXL
- Ensure design file is in the correct folder
- Check that file extension is supported (.png, .jpg, .jpeg, .gif, .bmp, .tiff, .tif)
- Verify design code extraction is working correctly
- **Note**: If your SKU contains a size prefix (e.g., `XL39553LG`) but your design file doesn't (e.g., `39553LG.png`), the fallback logic will automatically find it

### Logging

The application writes **two** log types into **`Logs/`** (no separate Errors and Warnings files):

#### Console log
- **Location**: `Logs/`
- **File Naming**: `console_log_YYYY-MM-DD_HH-MM-SS.txt` (one per app run)
- **Content**: Complete stdout/stderr for the run, human-readable timestamps and events, errors/warnings/dialogs, end-of-run summary (runtime + anomaly counts)
- **Output targets**: Always written to the log file; also mirrored when a console exists (`python queue_app.py`). With `run_queue_app.bat` / `pythonw`, use `Logs/` as the source of truth

#### Size determination log
- **Location**: `Logs/`
- **File Naming**: `(input_stem) size_determination_YYYY-MM-DD_HH-MM-SS.txt`
- **Content**: Per-design Order Number, Item SKU, Size Reference taken, match type, final dimensions, SUMMARY
- **Folder processing**: One size determination file per DTF Des file

### Debug Tips

1. **Check Progress Messages**: Progress bar shows current operation
2. **Review Warning Messages**: Application shows warnings for missing files/sizes
3. **Check Logs**: Open the latest `console_log_*.txt` and matching `*size_determination_*.txt` under `Logs/`
4. **Verify File Paths**: Ensure all paths in settings file are valid
5. **Check File Formats**: Ensure design files are valid image formats
6. **Size Reference**: Verify Merge column (Column I) has size codes
7. **Logging per run**: Look in **`Logs/`** for `console_log_*.txt` (full run) and `*size_determination_*.txt` (per-design size choices). Missing-size row exports go to **`Missing Size Reference/`**.

---

## API Reference

### Main Methods

#### File Selection
- `select_input_file()`: Load DTF Des input file
- `select_designs_folder()`: Select designs folder
- `select_single_designs_folder()`: Select single designs folder (Personalised)
- `select_double_designs_folder()`: Select double designs folder (Personalised)
- `select_dtf_queues_folder()`: Select DTF Queues folder for RAR upload
- `remove_dtf_queues_folder()`: Remove/clear DTF Queues folder directory to prevent files from being sent

#### Processing
- `arrange_designs()`: Process file or folder in "Normal" mode
- `arrange_personalised_designs()`: Process file or folder in "Personalised" mode
- `arrange_missing_logo_designs()`: Process file or folder in "Missing Logo" mode (searches both personalized and standard folders)
- `select_input_folder()`: Select folder containing multiple DTF Des files
- `process_folder()`: Process all files in folder (Normal mode); creates one size determination log per DTF Des file
- `process_folder_personalised()`: Process all files in folder (Personalised mode); creates one size determination log per DTF Des file
- `process_folder_missing_logo()`: Process all files in folder (Missing Logo mode); creates one size determination log per DTF Des file
- `process_single_file()`: Process single file with SKU column
- `process_personalised_file()`: Process file with Order Number and Item SKU columns
- `process_missing_logo_file()`: Process file with Missing Logo mode (searches both personalized and standard folders)
- `save_folder_files_separately()`: Save each file's batches separately when processing folder

#### Size & Design Matching
- `extract_size_code(sku)`: Extract size code from SKU using reference file
- `extract_design_code(sku)`: Extract design code from SKU (first part before dash)
- `remove_apparel_size_prefix(design_code)`: Remove apparel size prefixes (XL, 2XL, etc.) from design code
- `get_size_from_reference(size_code)`: Get dimensions for size code
- `get_merged_text_from_reference(size_code)`: Get merge text for size code
- `find_design_file(sku)`: Find design file for SKU (with multiple matching strategies)
- `find_design_file_vba_logic(order_number, duplicate_index, folder_type, exclude_path)`: Find design file for order (Personalised)
  - Returns `(file_path, design_type, is_pocket, is_sleeve)` tuple
  - Detects pocket (-P.png) and sleeve (-S.png) variants automatically
  - `is_pocket` and `is_sleeve` are boolean flags indicating variant detection
- `save_missing_size_reference_rows(df, missing_row_indices, source_file_path)`: Save rows with missing size references to a new DTF Des file

#### Canvas Operations
- `pack_designs(designs)`: Arrange designs on canvas
- `create_and_save_canvas(arranged_designs, save_path, ..., source_file_path)`: Create and save PNG with correct label from source file
- `save_canvas_image()`: Save current arrangement (handles both single file and folder processing)
- `save_folder_files_separately()`: Save each file from folder processing separately
- `draw_preview()`: Draw preview on canvas

#### RAR Operations
- `detect_rar_tool()`: Detect available RAR tool (WinRAR or 7-Zip)
- `create_rar_from_pngs(png_files, rar_path)`: Create RAR archive from PNG files
- `generate_rar_name(saved_files_info, is_folder_processing)`: Generate RAR filename based on source files
- `copy_rar_to_dtf_queues(rar_path, dtf_queues_folder)`: Copy RAR file to DTF Queues folder

#### Error Logging
- `save_error_to_file(content, error_type)`: Save error or warning to separate file
- `setup_error_logging()`: Initialize comprehensive error and warning logging system
- `setup_console_logging()`: Initialize console logging to capture all CMD output to file
- `close_console_logging()`: Close console log file and generate summary report

#### Canvas Configuration
- `update_canvas_size()`: Update canvas width and height dimensions
- `update_dpi()`: Update DPI setting and recalculate mm to pixel conversion
- `load_color_bar_from_app_dir()`: Auto-load color bar image from application directory

#### UI Controls
- `on_mousewheel()`: Pan the preview canvas (Shift+wheel for horizontal)
- `on_canvas_resize()`: Debounced redraw when the preview panel is resized
- `clear_preview()`: Clear preview canvas and cached preview images
- `draw_preview()`: Draw all arranged batches as composited preview images

---

## Support & Contact

For issues, questions, or feature requests, please refer to the application's error messages and this documentation.

---

**Last Updated**: August 4, 2026

#### Recent Updates Summary
- **August 4, 2026**:
  - Change log and docs synced for work since July 23 (gaps, PET width rationale, bare-base size fallback)
- **July 31, 2026** (helpers refined August 2):
  - Bare-base size lookup fallback when bracketed siblings exist but no bracket matches (e.g. `K-H` + `YL`)
- **July 26, 2026**:
  - Documented PET/DTF film: 600 mm film, 15 mm silver plates each side → 570 mm usable canvas width
- **July 25, 2026**:
  - Canvas gaps: start/left ~**2 mm** (`NON_BAR_MARGIN` = 24); between rows ~**15 mm** (`DEFAULT_VERTICAL_PADDING` = 177)
- **July 23, 2026**:
  - Pass 1 skip rule: keep landscape when free beside &lt; 200 mm **and** next logo cannot share the row
  - Save PNG on background thread; faster lossless write (`compress_level=1`); progress label fixed
  - Removed “Successfully arranged designs” popup after arrange
  - Docs (`USAGE.md`, `docs/README.md`, this file) and `Logs/logging_initialized.txt` updated
- **July 22, 2026**:
  - Pass 2: after a row closes, rotate portraits to landscape when spare width allows (−90° for Pass‑1, +90° for native)
  - `_pack_pass1_rotated` prevents double-rotate content flips
- **July 18, 2026**:
  - Canvas gaps retargeted to ~8 mm between designs, ~1 mm left/start (later changed to ~2 mm on July 25), ~12 mm color-bar gap
  - Row-fit width matches `place_row_grid`; Pass 1 landscape→portrait packing rotation introduced
- **July 14, 2026**:
  - Unified logging under `Logs/` only (console + size determination); removed separate Errors and Warnings / Size Determination Logs outputs
  - Human-readable console events and size determination design entries; bracketed size rows require both base and bracket in SKU
  - Preview zoom default raised to 47.5%; black labels above designs and black outlines
  - Docs (`USAGE.md`, `docs/README.md`, this file) updated for logging layout
- **July 12, 2026**:
  - Lightweight ttk GUI theme (`gui_theme.py`): slate/teal chrome, accent action buttons, muted empty states
  - Actions LabelFrame; preview background color centralized in theme (`#d0d5dd`)
  - Added `event=gui_theme_applied` run log at UI build (once per launch)
  - Docs (`USAGE.md`, `docs/README.md`, this file) updated for theme and layout
- **July 10, 2026**:
  - Scrollable full-canvas preview: removed 100-design cap and zoom controls
  - Fixed readable scale (one batch width × zoom factor), mouse-wheel / scrollbar pan, grey background
  - Batch composite drawing with PhotoImage cache and debounced resize redraw
  - Added `event=preview_drawn` run log when the preview is drawn after arrange
  - Minor bug fixups: Normal/Save PNG(s) message wording; no-op canvas/DPI validation; `DTF Des-` strip regex; Missing Size Reference + DTF Queues paths use project root
  - Docs (`USAGE.md`, `docs/README.md`, this file) updated for current button names and export paths
- **June 11, 2026**:
  - Added A3 forced landscape: 90° rotate + runtime size-box swap before canvas paste (all modes)
  - Console and size determination logs document A3 landscape transform and skipped IronOn auto-orientation
- **January 15, 2026**: 
  - Added comprehensive console logging system that captures all CMD output to files
  - Added run summary reports at the end of each console log file
  - Enhanced anomaly tracking with counters for errors, warnings, exceptions, dialogs, and tracebacks
  - All anomalies are now clearly marked and logged to console for immediate visibility
  - Summary reports provide quick overview of what happened during each run
- **January 1, 2026**: 
  - Updated documentation to accurately reflect current codebase structure
  - Corrected file counts and line numbers
  - Updated project structure to match actual directory layout
  - Clarified configuration file locations and loading order
- **December 29, 2025**: 
  - Added Pocket Design IDs Database feature for automatic F8-based size code detection
- **December 11, 2025**: 
  - Added "Remove DTF Queues Folder" button to clear folder selection
  - Added pocket and sleeve variant detection for personalized button processing
  - Implemented dimension overrides for pocket variants based on SKU patterns
  - Added orientation-based resizing strategy for better image fitting
  - **Size Code Matching Enhancement**: Improved size code matching to prioritize longer, more specific codes (e.g., `F8-M-T` matches before `F8`)
- **December 3, 2025**: 
  - Added filename inclusion in error/warning messages for single file processing
  - Enhanced double design sizing with automatic canvas width fitting

