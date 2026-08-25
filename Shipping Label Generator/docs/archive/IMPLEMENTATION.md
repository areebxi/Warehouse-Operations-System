# Implementation Log (step-by-step)

This file records the implementation steps taken to build the app from `PLAN.md` + `REQUIREMENTS.md`.

---

## Step 0 — Read plan + requirements (completed)

- **Inputs reviewed**
  - `PLAN.md`
  - `REQUIREMENTS.md`
- **Key constraints captured**
  - Windows-first entrypoints (`.bat`)
  - Config precedence: ENV/`.env` → `shipping_config.yaml` → defaults
  - JSONL logs with recursive redaction
  - Keep modules small (≤ 250 lines per `.py`)

---

## Step 1 — Bootstrap repo skeleton (completed)

### 1.1 Dependencies

- **Added** `requirements.txt` with required runtime libraries (ranges).

### 1.2 Default config file

- **Added** `shipping_config.yaml` matching the required schema + defaults.

### 1.3 Windows entrypoints

- **Added**
  - `bat_files/run_convert.bat`
  - `bat_files/run_print.bat`
  - `bat_files/ALL_VOID_LABELS.bat`

### 1.4 Python package skeleton + CLI

- **Added** minimal package skeleton under `scripts/`
- **Added** CLI entrypoint `scripts/app/main.py` with subcommands:
  - `convert`
  - `print`
  - `void`

### 1.5 Verified

- `python -m scripts.app.main --help` works.

---

## Step 2 — Config loader + JSONL logging (completed)

### 2.1 Config loader

- **Added**
  - `scripts/app/config/defaults.py` (in-code defaults matching `REQUIREMENTS.md`)
  - `scripts/app/config/load.py` (YAML overlay + ENV overrides + minimal validation)
- **ENV overrides implemented**
  - `MAX_CONCURRENCY`
  - `BATCH_NOTES`
  - `PROCESSED_BY`
  - `SHIP_FROM`
  - `SHIPPING_PROVIDER` (`real`)

### 2.2 JSONL logging

- **Added**
  - `scripts/app/logging/jsonl.py` (UTC ISO timestamps, 1 JSON object per line)
  - `scripts/app/logging/redact.py` (recursive redaction by key)
- **Verified**
  - Running `python -m scripts.app.main convert` creates `logs/run_YYYYMMDD.jsonl`

---

## Step 3 — Provider layer (in progress)

Goal: add provider contract + real provider.

### 3.1 Provider contract + models (partial)

- **Added models**
  - `scripts/app/models/order.py`
  - `scripts/app/models/shipment.py`
  - `scripts/app/models/label.py`
- **Added provider interface + selector**
  - `scripts/app/providers/base.py`
  - `scripts/app/providers/select_provider.py`
- **Added real-provider stub**
  - `scripts/app/providers/real/provider.py`
---

## Step 4 — Restore bootstrap/config files on disk (completed)

During Step 3 smoke testing, we confirmed the on-disk workspace was missing earlier bootstrap/config files, so we re-created them to match the plan.

- **Restored**
  - `requirements.txt`
  - `shipping_config.yaml`
  - `README.md`
  - `bat_files/run_convert.bat`, `bat_files/run_print.bat`, `bat_files/ALL_VOID_LABELS.bat`
  - `scripts/__init__.py`
  - `scripts/app/__init__.py`
  - `scripts/app/main.py`
  - `scripts/app/config/*`
  - `scripts/app/logging/*`

### 4.1 Fix duplicated-appended blocks (completed)

Several Python files contained a duplicated appended copy of their own contents, causing `SyntaxError: from __future__ imports must occur at the beginning of the file`.

- **Fixed by removing appended duplicates**
  - `scripts/app/main.py`
  - `scripts/app/config/defaults.py`
  - `scripts/app/config/load.py`
  - `scripts/app/logging/jsonl.py`
  - `scripts/app/logging/redact.py`
  - `scripts/app/models/{label,order,shipment}.py`
  - `scripts/app/providers/{base,select_provider}.py`
  - `scripts/app/providers/mock/pdf_factory.py`
  - `scripts/app/providers/mock/state.py`
  - `scripts/app/providers/real/provider.py`

### 4.2 Verified (completed)

- `python -m scripts.app.main --help` runs successfully.

---

## Step 5 — Flow A: Convert (completed)

Goal: implement Convert flow A0–A4 (discover → parse → canonicalize → manifest/archive).

### 5.1 Implemented modules (completed)

- **Added**
  - `scripts/app/flows/convert/discover.py` (A0 mode selection: CSV takes precedence over Excel)
  - `scripts/app/flows/convert/parse_csv.py` (A1 alias matching + row filtering)
  - `scripts/app/flows/convert/parse_excel.py` (A2 strict headers + process cleanup)
  - `scripts/app/flows/convert/canonicalize.py` (A3 dedupe + sorting + output column names)
  - `scripts/app/flows/convert/archive.py` (A4 manifest + archiving)
  - `scripts/app/flows/convert/run.py` (orchestrates A0–A4)
  - `scripts/app/util/hashing.py` (SHA-256 in 1MB chunks)
  - `scripts/app/util/time.py` (UTC timestamps + archive prefix)
- **Wired**
  - `scripts/app/main.py` now runs `convert` via `run_convert()`

### 5.2 Next (to verify)

- Run `convert` with sample inputs to confirm:
  - CSV vs Excel discovery priority
  - invalid-file behavior (skip + log available columns)
  - output CSV header names and sort/dedupe behavior
  - `DTF Des Files - Processed/.processed_manifest.json` updates
  - archived filenames are prefixed with `YYYYMMDD_HHMMSS_`

### 5.3 Smoke check (completed)

- Running `python -m scripts.app.main convert` with an empty `desfiles/` produces the required “no files found” failure and logs `convert_no_files`.

### 5.4 Verification run (completed)

- **Verified A0 discovery priority**
  - When both `*.csv` and `*.xlsx` are present in `desfiles/`, Convert runs in **CSV mode** and **does not process Excel** (Excel remains in `desfiles/`).
- **Verified A1 invalid file behavior**
  - Missing required columns ⇒ file is skipped and JSONL log includes `available_columns`.
- **Verified A3 canonical output shape**
  - Output headers are exactly: `Process Number`, `orders Numbers`.
  - Sort/dedupe behavior matches the plan for the sampled inputs.
- **Verified A4 manifest + archiving**
  - `DTF Des Files - Processed/.processed_manifest.json` is created/updated with `hashes` and `updated_at`.
  - Successfully processed CSV inputs are moved to `DTF Des Files - Processed/` with `YYYYMMDD_HHMMSS_` filename prefix.

### 5.5 Fix applied during verification (completed)

- **Fixed** pandas type inference causing process numbers to appear as `2.0` / `10.0` in the output.
  - Updated:
    - `scripts/app/flows/convert/parse_csv.py` to read CSV with `dtype=str`
    - `scripts/app/flows/convert/parse_excel.py` to read Excel with `dtype=str`

---

## Step 6 — Flow B: Print (starting with rules) (in progress)

### 6.1 Parity-critical pure rules (completed)

- **Added**
  - `scripts/app/rules/selection.py` (order + shipment selection rules)
  - `scripts/app/rules/service_map.py` (substring mapping; first match wins)
  - `scripts/app/rules/weights.py` (normalize to oz vs lb based on carrier substring list)

### 6.2 PDF utilities + print flow skeleton (completed)

- **Added PDF helpers**
  - `scripts/app/pdf/label_decode.py` (base64 → PDF bytes validation + write)
  - `scripts/app/pdf/report_pages.py` (ReportLab summary + missed pages)
  - `scripts/app/pdf/merge_process.py` (summary → labels → missed)
  - `scripts/app/pdf/merge_combined.py` (combined alternating Summary,Label quirk)
- **Added Print flow**
  - `scripts/app/flows/print_labels/read_group.py` (B1 grouping rules)
  - `scripts/app/flows/print_labels/process_order.py` (B2 per-order logic: select/reuse/create)
  - `scripts/app/flows/print_labels/failures.py` (failures CSV + human error log formats)
  - `scripts/app/flows/print_labels/run.py` (orchestrates B1–B4 in mock mode)
- **Wired**
  - `scripts/app/main.py` now runs `print` via `run_print()`

### 6.3 Verified (completed)

- Installed dependencies from `requirements.txt` (including `PyPDF2`).
- Ran `python -m scripts.app.main print` with a sample canonical CSV and confirmed artifacts under `output/`:
  - individual label PDFs under `output/labels/process_<n>/`
  - per-process PDFs under `output/process_pdfs/`
  - combined alternating PDF at `output/combined.pdf`
  - failures artifacts when applicable:
    - `output/failures.csv` header matches spec
    - `output/error_log.txt` blocks include `Order:`, `Customer:`, `Process:`, `Error:` plus `Time:` (UTC ISO)

---

## Step 7 — Flow C: Void (completed)

- **Added**
  - `scripts/app/flows/void_labels/read_void_list.py` (reads void CSV; extracts order numbers)
  - `scripts/app/flows/void_labels/void_shipments.py` (void active shipments; logs per shipment)
  - `scripts/app/flows/void_labels/run.py` (orchestrates Flow C with concurrency)
- **Wired**
  - `scripts/app/main.py` now runs `void` via `run_void()`

### 7.1 Verified (completed)

- Created a sample `void_labels.csv` and ran `python -m scripts.app.main void`
- Confirmed JSONL logs include `void_shipment_success` and `void_done`

---

## Step 8 — Move void CSV into input folder (completed)

- **Created** `void label input/`
- **Moved** `void_labels.csv` → `void label input/void_labels.csv`
- **Updated** `shipping_config.yaml`:
  - `paths.void_csv` is now `void label input/void_labels.csv`
- **Fixed** `shipping_config.yaml` accidental duplicate block (removed)
- **Verified** `python -m scripts.app.main void` still runs successfully

---

## Step 9 — Remaining parity gaps from PLAN.md (completed)

Goal: finish the parts of `PLAN.md` that are not yet implemented or not yet verified in this repo:

- Print flow parity wiring (service mapping, weight normalization, provider settings)
- Reliability layer (timeouts, retries, rate limiting / 429 handling)
- Automated tests for parity-critical behaviors

### 9.1 Status

- All Step 9 items below are completed (9.2–9.4).

### 9.2 Print flow parity wiring (completed)

- **Updated** `scripts/app/flows/print_labels/process_order.py`:
  - If `serviceCode` is missing, attempt `rules/service_map.py` mapping using `requestedShippingService`
  - Derive a best-effort total weight from `order.items` and normalize via `rules/weights.py` (oz vs lb based on carrier substring config)
  - Ensure failure rows preserve `customer_name` when the selected order is known

### 9.3 Reliability (Phase 6) — timeouts, retries, rate limiting (completed)

- **Added** `scripts/app/util/retries.py`:
  - Timeouts via `asyncio.wait_for()`:
    - `concurrency.request_timeout_sec`
    - `concurrency.label_timeout_sec`
  - Bounded retries:
    - `concurrency.max_retries`
    - exponential backoff within `concurrency.retry_min_wait_sec..retry_max_wait_sec`
  - 429 handling:
    - honors `retry_after` attribute when present; otherwise uses `rate_limit.fallback_wait_sec`
- **Wired provider calls through reliability wrapper**
  - `scripts/app/flows/print_labels/process_order.py` wraps:
    - `lookup_orders`, `list_shipments`, `fetch_label`, `create_label`
  - `scripts/app/flows/void_labels/void_shipments.py` wraps:
    - `lookup_orders`, `list_shipments`, `void_label`

### 9.4 Tests (Phase 7) — parity-critical coverage (completed)

- **Added** `pytest` to `requirements.txt`
- **Added** test suite under `tests/`:
  - `tests/test_convert_flow.py`:
    - A0 discovery priority (CSV preferred over Excel)
    - A1 CSV parsing preserves string process numbers (no `2.0` artifacts)
    - A3 canonicalize de-dupe + sorting
  - `tests/test_service_map.py`: first-substring-match-wins parity
  - `tests/test_weights.py`: oz-vs-lb normalization by carrier substring
- **Verified**
  - `python -m pytest -q` passes

---

## Step 10 — Combined Windows entrypoint (completed)

- **Added** `bat_files/run_convert_and_print.bat`
  - Runs `convert` and only runs `print` if convert succeeds (non-zero exit code stops the script).
- **Fixed** duplicated blocks in existing scripts
  - `bat_files/run_convert.bat`
  - `bat_files/run_print.bat`

---

## Step 11 — User-friendly launcher (RUN.bat) + interactive menu (completed)

- **Added** `RUN.bat`
  - Checks Python is installed via `py --version`
  - Installs dependencies (best-effort) if `import scripts` fails
  - Launches `shipping_system.py` interactive menu
- **Added** `shipping_system.py`
  - Interactive menu to run: `convert`, `print`, `convert+print`, `void`

---

## Step 12 — First-time installer (SETUP.bat) (completed)

- **Added** `SETUP.bat`
  - Intended for fresh machines (run once)
  - Verifies Python launcher exists (`py --version`)
  - Upgrades pip then installs `requirements.txt`
  - On failure, prints troubleshooting guidance (including “Run as administrator” and venv fallback)

---

## Step 14 — Operator logging: rotating `shipping.log` + JSONL + redaction + console filter (completed)

- **Updated** `scripts/app/logging/jsonl.py`
  - Creates the logs directory from config (`paths.logs_dir`)
  - Writes `shipping.log` using a rotating file handler (5MB max, 5 backups)
  - Each line is JSON (one JSON object per line) with:
    - `ts`, `level`, `msg`, `logger`
    - optional `extra` (redacted)
    - optional `exc` stack trace (on failures)
  - Redacts sensitive keys in `extra` (e.g. `labelData`, `Authorization`, `apiKey`, `apiSecret`)
  - Console logging is limited to WARNING+ (less noisy for operators)

---

## Step 15 — Two void modes + batch entrypoints (completed)

- **Added** `bat_files/VOID.bat`
  - Runs `python -m scripts.app.launchers.void_labels` which voids **one active shipment per order** (single-void mode)
- **Added** `bat_files/ALL_VOID_LABELS.bat`
  - New preferred script entrypoint for void-all mode (same behavior as `app.main void`)
- **Added** `scripts/app/launchers/void_labels.py`
  - Standalone void runner that reads the void CSV and voids **max 1 shipment per order**
- **Added** `scripts/app/launchers/shipping_system.py`
  - Supports `--void` for non-interactive “void-all then exit”
- **Updated** `scripts/app/flows/void_labels/void_shipments.py`
  - Adds `max_shipments_per_order` to control “one” vs “all”









