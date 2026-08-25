# Rebuild Requirements (Logic + Behavior Parity)

This document captures **how the app works** (its logic, rules, and runtime assumptions) so you can rebuild it without changing behavior.
## Runtime environment requirements

- **OS**: Windows (batch files are first-class entrypoints; Python runs fine cross-platform, but the “product” assumes Windows).
- **Python**: **3.12+** (target for rebuild).
- **Network**: outbound HTTPS access to the provider API base URL

---

## Configuration + secrets rules (must match)

### Secrets
- **Never hardcode API keys** in code or YAML.
- When the real provider API is added later, credentials must be supplied via environment variables (optionally loaded from a `.env` file).

### Provider selection
- `SHIPPING_PROVIDER` must be set to `real`.

### Config
- All tuneables live in **YAML**, not hardcoded:
  - concurrency, timeouts, retries/backoff
  - provider defaults (carrier/package) and label request settings (format/layout/download type)
  - service mapping rules (requested shipping service text → provider `serviceCode`)

**Behavioral requirement**: the rebuild must respect the same config precedence:

- `.env`/ENV overrides where supported (example: concurrency can be overridden)
- otherwise use `shipping_config.yaml`
- otherwise use safe defaults

### Exact `shipping_config.yaml` schema + defaults (logic parity)

To preserve behavior, the rebuild must support these keys and defaults (even if you later rename the file/structure, the *effective values* must match):

- `concurrency.max_workers` (default `25`)
  - ENV override: `MAX_CONCURRENCY` (string/int; when set, it overrides YAML/default)
- `concurrency.request_timeout_sec` (default `15`)
- `concurrency.label_timeout_sec` (default `35`)
- `concurrency.max_retries` (default `2`)
- `concurrency.retry_min_wait_sec` (default `1`)
- `concurrency.retry_max_wait_sec` (default `8`)
- `rate_limit.fallback_wait_sec` (default `60`) for HTTP `429` when `Retry-After` missing

- `paths.output_dir` (default `"output"`)
- `paths.logs_dir` (default `"logs"`)
- `paths.desfiles_dir` (default `"desfiles"`)
- `paths.orders_csv` (default `"Order Numbers.csv"`)
- `paths.void_csv` (default `"void_labels.csv"`)

- `logging.format` (default `"json"`)
- `logging.level` (default `"INFO"`)
- `logging.redact_keys` (default `["labelData","Authorization","apiKey","apiSecret"]`)

- `batch.notes` (default `"CreateAndProcessBatchByOrderIds"`)
  - ENV override: `BATCH_NOTES`
- `batch.processed_by` (default `"Automated"`)
  - ENV override: `PROCESSED_BY`
- `batch.ship_from` (default `"Dudley"`)
  - ENV override: `SHIP_FROM`

- `security.restrict_output_permissions` (default `true`)
  - Behavior: best-effort “restrict output dir permissions”; on Windows it may be a no-op.

- `weight.ounce_carriers` (default `["royal_mail","stamps_com"]`)
  - Behavior: if carrier contains any of these substrings (case-insensitive), weights are normalized to ounces; otherwise to pounds.

- `service_map.<carrier_key>` (default `[]`)
  - `carrier_key` is computed as: `carrier.lower().replace(" ","_").replace("-","_")`
  - Each entry shape: `{ match: "<substring>", code: "<serviceCode>" }`
  - Matching rule: if `entry.match.lower()` is a substring of `requestedShippingService.lower()`, return `entry.code` (first match wins).

- Provider label request settings (defaults chosen to match current behavior):
  - `provider.test_label` (default `false`)
  - `provider.label_format` (default `"PDF"`)
  - `provider.label_layout` (default `"4x6"`)
  - `provider.label_download_type` (default `"url"`)

---

## Inputs and outputs (conceptual, no folder assumptions)

The app is a file-driven pipeline. To preserve behavior without prescribing a directory layout, the rebuild must support these concepts:

- **Order input source**: one or more Excel/CSV files containing at least:
  - **Order Number**
  - **Process Number** (grouping key)
- **Canonical orders list**: a normalized CSV containing the extracted order numbers and process numbers.
- **Void list**: a CSV containing order numbers to cancel/void.
- **Label artifacts**:
  - individual label PDFs (one per order)
  - per-process batch PDFs (summary + labels + optional missed page)
  - combined PDF (cross-process merge)
- **Failure artifacts**:
  - a machine-readable failures CSV
  - a human-readable error log file
  - a structured JSON log stream

The rebuild may place these artifacts anywhere, as long as the produced artifacts and their contents follow the logic described below.

## Core logic flows (must match)

## Provider interface contract (API-agnostic; must match)

The app’s core logic is provider-agnostic. Printing/voiding must call a provider implementation with the following operations (names are illustrative; contract is what matters):

- **Lookup order(s) by order number**
  - Input: `order_number` string
  - Output: list of orders (0..N)
  - Each order must include at minimum:
    - `orderId` (stable unique id)
    - optional shipping fields used for defaults (`carrierCode`, `serviceCode`, `packageCode`)
    - optional `requestedShippingService` string (used for service mapping)
    - optional `items[]` with weights and SKU/name/quantity (used for `customerReference` + weight calculation)
    - optional ship-to/customer fields used for customer name extraction

- **List shipments for an order**
  - Input: `order_id`, and a flag `include_voided`
  - Output: list of shipments
  - Each shipment must include:
    - `shipmentId`
    - `voided` boolean
    - optional `carrierCode`, `serviceCode`, `packageCode` (highest-priority defaults for create-label)

- **Fetch an existing label for a shipment**
  - Input: `shipment_id`
  - Output: label payload or `None`
  - Label payload must include:
    - `labelData` as base64-encoded PDF bytes (string)
    - optional `trackingNumber`

- **Create label for an order**
  - Input: order + resolved carrier/service/package + shipDate + optional weight + optional customerReference + label request settings
  - Output: label payload (same shape as above) or an error string

- **Void label**
  - Input: `shipment_id`
  - Output: success/failure (+ error)

### Flow A: Convert (input Excel/CSV → canonical orders list)
**Goal**: produce a deduped, sorted, consistent orders list.

**Exact rules (logic parity)**:

#### A0) Input discovery
- Inputs are read from `paths.desfiles_dir/` (default `desfiles/`).
- If any `*.csv` files exist, **CSV mode** is used and Excel files are ignored.
- Else, if any `*.xlsx`, `*.xls`, `*.xlsm` exist, **Excel mode** is used.
- Else, fail with “no files found”.

#### A1) CSV mode (header matching + row filtering)
- Read each CSV into a dataframe.
- Header matching is case-insensitive via `lower().strip()`.
- **Order column aliases** (first match wins):
  - `order - number`, `order number`, `ordernumber`, `order`
- **Process column aliases** (first match wins):
  - `process num`, `process number`, `processnum`, `process`
- If the order column is missing:
  - mark that file as invalid, print available columns, continue other files.
- If the process column is missing:
  - mark that file as invalid, print available columns + instruction, continue other files.
- Row filtering:
  - keep rows where order is not null and not empty after trimming
  - process is converted to string and trimmed
  - drop rows where process is `""` or `"nan"`

#### A2) Excel mode (strict headers + process cleanup)
- Each Excel file must contain **exact** headers:
  - `Order - Number` and `Process Num`
  - Files missing these headers are skipped.
- Rows with blank order numbers are dropped.
- Process value cleanup:
  - cast to string + trim
  - remove leading `"Process"` + optional whitespace using regex `^Process\s*` (case-insensitive)

#### A3) Canonical output shape + sort + de-dupe (exact)
- Concatenate all valid extracted rows across all inputs.
- De-duplicate by order number (keep first occurrence).
- Output columns are exactly:
  - `Process Number`, `orders Numbers`
- Sorting:
  - Compute `_sk`:
    - if process is all digits: `_sk = int(process)`
    - else `_sk = 0`
  - Sort by `_sk`, then by string `Process Number`.

#### A4) Idempotency for conversion (hash manifest + archive) (exact)
- For each input file, compute SHA-256 over file bytes (1MB chunks).
- Manifest location:
  - `desfiles_processed/.processed_manifest.json`
- Manifest JSON shape:
  - `{ "hashes": ["<sha256>", ...], "updated_at": "<iso>" }`
- If a file hash is already in the manifest:
  - skip processing that file
  - attempt to delete it from `desfiles/` to keep the folder clean
- If hashing fails for a file:
  - process it anyway (do not silently skip)
- If conversion succeeds:
  - move processed input files to `desfiles_processed/`
  - prefix archived filename with timestamp `YYYYMMDD_HHMMSS_`
  - persist hashes of successfully processed files to the manifest

**Failure behavior**:
- If no valid input files are provided/found, emit a clear message and do not produce new output.

---

### Flow B: Print (canonical orders list → label PDFs → merged PDFs)
**Goal**: for each order, ensure there is a valid label (reuse if possible), then create PDFs.

#### Step B1: Read & group orders
- Read the canonical orders list CSV.
- Group by `process_number` (process groups).
  - Column matching rules (case-insensitive):
    - process column: first header containing both `"process"` and `"number"`
    - order column: first header containing `"order"`, else first header containing `"num"`
  - If process column is missing, all rows use process `"1"`.
  - If a row’s process value is blank/falsey, it is coerced to `"1"`.

#### Step B2: For each order number (async)
For each `order_number` in the group:

1) **Fetch order** from provider
- Contract: provider lookup by order number returns 0..N orders
- If multiple orders match, select one that is safe to process (avoid duplicates; prefer one without an active shipment).
  - Exact selection rule:
    - For each candidate order, check whether it has any **active (non-voided)** shipments.
    - Prefer candidates with **no active shipments** (“awaiting shipment”).
    - If multiple awaiting candidates exist, pick the one with highest `orderId`.
    - If none are awaiting, treat as not processable.

2) **Fetch shipments** to decide reuse vs create
- Contract: provider list-shipments returns shipments with `voided=true/false`
- Must be able to distinguish voided vs active shipments.
  - Exact selection rule:
    - Sort shipments by `shipmentId` descending.
    - Split into `active_shipments` (`voided=false`) and `voided_shipments` (`voided=true`).
    - If any active shipments exist, use those; otherwise use voided shipments (and log a warning).

3) **Idempotency rule**
- If an active shipment exists:
  - attempt to reuse label:
    - Contract: provider fetch-label returns a payload containing base64 `labelData`
  - if `labelData` exists, save it (do not create a new label)
- If only voided shipments exist, allow creating a new label (but log it).
  - Edge-case (must match): if reuse fails (exception or missing `labelData`), fall back to create-label.

4) **Create label (if not reused)**
- Contract: provider create-label returns a payload containing base64 `labelData` (and optional `trackingNumber`)
- Payload rules:
  - carrier/service/package chosen from:
    - existing shipment fields (highest priority)
    - else order fields
    - else config defaults and service mapping
  - include `shipDate` (today)
  - include label request settings from YAML:
    - `labelFormat` (PDF)
    - `labelLayout` (4x6)
    - `labelDownloadType` (default `"url"` unless overridden)
  - include weight if available/needed
  - optionally set `customerReference` (SKU/line items summary)
  - Hard-fail rule: if `serviceCode` cannot be resolved, the order fails with a clear error message.

5) **Persist label PDFs**
- Provider returns label PDF as base64 `labelData`.
- Decode base64 and write:
  - temp per-process file (for merging)
  - one individual label PDF per order

#### Step B3: Build per-process PDF
- For each process group, build a per-process PDF with this page order:
  1. **Summary page** (process/batch information)
  2. **All label pages** for that process (in order)
  3. **Missed orders page** (only if failures exist)

**Important**: the summary/missed pages are generated by the app (ReportLab). The actual labels are PDFs returned by the provider (mock now, real later).

#### Step B4: Build the combined PDF
- After all process PDFs are built, generate a combined PDF across all processes.

**Current behavior to match (even if it’s undesirable)**:
- The combined merge function inserts the **process summary page before each label page**, producing an alternating pattern:
  - Summary, Label, Summary, Label, ...

If you rebuild and want to preserve exact output, keep this behavior. If you want “labels only”, this is the part of the logic to change.

---

### Flow C: Void (void list → provider void calls)
**Goal**: cancel/void labels for listed orders in the provider.

**Rules**:
- Read the void list CSV and extract order numbers.
- For each order number:
  1) fetch the order and/or shipments
  2) find **active (non-voided)** shipments
  3) call void endpoint for each active shipment:
     - Contract: provider void-label with `shipmentId`
- Produce logs for each void attempt and summary counts.

**Output rules**:
- No PDFs are created.
- Results go to console + structured JSON logs.

---

## Logging + error reporting requirements

### What must be logged
- Start/end of batch runs (counts, elapsed, batch id)
- Per-order failures must have a human-readable reason string (at minimum)
- HTTP errors should record:
  - method (GET/POST)
  - URL/endpoint
  - status code (when available)
  - retry attempt count

### Failure artifacts (must match)
When a process group has failures, generate:
- a failures CSV with exact header:
  - `Customer Name,Process Number,Order Number,Order ID,Error Reason`
- a human-readable error log with per-order details in this format:
  - `Order:<order>`
  - `Customer:<name>`
  - `Process:<process>`
  - `Error:<reason>`

### Structured JSON log stream (must match)
- Logging must produce a JSON-lines file (one JSON object per line).
- Each event must include:
  - `ts` (UTC ISO timestamp)
  - `level`
  - `msg`
  - `logger`
  - optional `extra` object (recursively redacted by `logging.redact_keys`)
  - optional `exc` string for exceptions

---

## Real provider API (provided later)

**Secret-handling rule (important)**:
- Do **not** store API keys in YAML config files.
- Keep YAML for non-secret behavior settings (timeouts, concurrency, defaults, mappings).
- Provide secrets via environment variables (optionally loaded from a local `.env`) so they don’t get accidentally shared/committed and can be rotated per environment.

### Authentication
- Not specified yet (will be provided later). Core logic must not depend on auth details.

### Required endpoints
- Not specified yet. The real provider must implement the interface described in **Provider interface contract**.

### Concurrency + rate limits
- Use async concurrency (worker count from config/env).
- Detect HTTP `429` and honor `Retry-After` if present, otherwise wait a fallback number of seconds.
- Implement bounded retries with exponential backoff for network errors / 5xx responses.

---

## Dependency requirements (Python packages)

The rebuild must include these runtime libraries (matching the current app’s behavior):

- `aiohttp` (async HTTP; real-provider client later)
- `aiofiles` (async file writes for PDFs)
- `tqdm` (progress reporting)
- `tenacity` (retry/backoff helper)
- `pandas` + `openpyxl` (CSV/Excel parsing)
- `reportlab` (generate summary/missed pages)
- `PyPDF2` (merge PDFs)
- `python-dotenv` (load `.env`)
- `PyYAML` (load `shipping_config.yaml`)

The current project uses version ranges (example):
- `aiohttp>=3.9.0,<4.0`

If you want rebuild reproducibility, you can later decide to lock exact versions, but parity with the current repo is achieved by keeping the same range constraints.

