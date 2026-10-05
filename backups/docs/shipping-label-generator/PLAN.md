# Shipping Label App — Rebuild Plan (Parity-First)

This plan converts `REQUIREMENTS.md` into a build sequence that preserves **logic + behavior parity** while keeping the codebase ready for a future **real provider**.

## Goals and constraints

- **Parity-first**: reproduce current behaviors (including quirks like the combined PDF alternating summary/label pages).
- **Windows-first product**: batch files as first-class entrypoints.
- **Config precedence**: ENV / `.env` overrides → `shipping_config.yaml` → safe defaults.
- **Artifacts**: PDFs + failure CSV + human-readable error log + JSON-lines logs.
- **Code size constraint**: keep **every `.py` file ≤ 250 lines** (split modules early; aim for ~150–200).

---

## Proposed project structure (recommended)

### Structure principles (so it stays “clean” as it grows)

- **Strict layering** (dependency direction):
  - `flows/*` may depend on `providers/*`, `rules/*`, `io/*`, `pdf/*`, `util/*`, `app/config/*`, `app/logging/*`, `app/models/*`
  - `providers/*` may depend on `app/models/*`, `util/*`, and provider-internal helpers only
  - `pdf/*` must not call providers (PDF code should be pure “given bytes/pages → output”)
  - `rules/*` must be pure functions (no IO, no network)
- **Small-file guarantee**: keep **every `.py` file ≤ 250 lines** (split at ~200).
- **No shared “misc” module**: if something becomes a grab-bag, split it by responsibility.
- **Composition over inheritance**: especially in flows; keep providers behind an interface.
- **Deterministic core**: most logic should be testable without touching network/filesystem (IO isolated in `io/*` and “writers”).

```
scripts/
  app/
    __init__.py
    main.py                 # CLI entrypoint (thin router; no heavy logic)
    config/
      __init__.py
      defaults.py           # required defaults from REQUIREMENTS.md
      load.py               # YAML + ENV precedence + validation
    logging/
      __init__.py
      jsonl.py              # JSONL logger writer
      redact.py             # recursive redaction utility
    models/
      __init__.py
      order.py
      shipment.py
      label.py
    providers/
      __init__.py
      base.py               # Provider interface contract
      select_provider.py    # SHIPPING_PROVIDER=real
      real/
        __init__.py
        provider.py         # stub now; implement later
    flows/
      __init__.py
      convert/
        __init__.py
        run.py              # orchestrates Flow A
        discover.py         # A0 discovery (csv vs excel)
        parse_csv.py        # A1
        parse_excel.py      # A2
        canonicalize.py     # A3
        archive.py          # A4 manifest + move/delete
      print_labels/
        __init__.py
        run.py              # orchestrates Flow B
        read_group.py       # B1 column matching + grouping
        process_order.py    # B2 per-order logic (calls helpers below)
        resolve_fields.py   # carrier/service/package resolution + mapping
        reuse_or_create.py  # idempotency rules
        write_artifacts.py  # per-order PDF writes + temp files
        build_pdfs.py       # per-process + combined PDF orchestration
        failures.py         # failures CSV + human-readable error log
      void_labels/
        __init__.py
        run.py              # orchestrates Flow C
        read_void_list.py   # parse void CSV
        void_shipments.py   # provider void calls + reporting
    io/
      __init__.py
      canonical_csv.py      # read/write canonical orders list
      artifacts.py          # output paths + permission restriction (best-effort)
    pdf/
      __init__.py
      report_pages.py       # ReportLab summary + missed pages
      merge_process.py      # per-process merge
      merge_combined.py     # combined merge (alternating quirk)
      label_decode.py       # base64 → PDF bytes validation + write
    rules/
      __init__.py
      weights.py            # ounce/pound normalization rules
      service_map.py        # requestedShippingService substring mapping
      selection.py          # order/shipment selection rules
    util/
      __init__.py
      hashing.py            # SHA-256 in 1MB chunks
      retries.py            # tenacity helpers, 429 handling policy
      time.py               # UTC timestamps, shipDate helpers
  bat_files/
    run_convert.bat
    run_print.bat
    run_void.bat
  shipping_config.yaml      # checked in (non-secrets) defaults can live here
  requirements.txt
  README.md
  tests/
    test_convert_parity.py
    test_service_map.py
    test_weight_norm.py
    test_mock_provider_determinism.py
```

Notes:
- You can rename directories later; what matters is the behavior defined in `REQUIREMENTS.md`.
- Keep provider details isolated behind `providers/base.py`.
- Keep files small: when any module approaches ~200 lines, split it (to preserve the **≤250 lines/file** constraint).

---

## Phase 0 — Repository bootstrap (½ day)

- **Create packaging + entrypoints**
  - Add `requirements.txt` with the required libraries:
    - `aiohttp`, `aiofiles`, `tqdm`, `tenacity`, `pandas`, `openpyxl`, `reportlab`, `PyPDF2`, `python-dotenv`, `PyYAML`
  - Add `README.md` with:
    - setup steps (Python 3.12+)
    - commands for convert/print/void
    - provider configuration note
- **Add default `shipping_config.yaml`**
  - Include the schema + defaults listed in `REQUIREMENTS.md`
  - Ensure secrets are **not** in YAML (only via ENV)
- **Add batch scripts**
  - `bat_files/run_convert.bat`: runs `python -m app.main convert`
  - `bat_files/run_print.bat`: runs `python -m app.main print`
  - `bat_files/ALL_VOID_LABELS.bat`: runs `python -m app.main void`

Deliverable: project runs and shows help text and config loading without doing work.

---

## Phase 1 — Config + logging parity (1 day)

### 1A) Config loader with required precedence

Implement `app/config.py`:
- Load defaults in-code that match `REQUIREMENTS.md`
- Overlay `shipping_config.yaml` if present
- Apply ENV overrides:
  - `SHIPPING_PROVIDER=real`
  - `MAX_CONCURRENCY`, `BATCH_NOTES`, `PROCESSED_BY`, `SHIP_FROM`
- Validate types and provide clear startup errors (but keep behavior forgiving where required).

### 1B) JSON-lines logging with redaction

Implement `app/logging/jsonl.py` + `app/logging/redact.py`:
- Write one JSON object per line
- Always include: `ts` (**UTC ISO date+time**), `level`, `msg`, `logger`
- Optional `extra` object for structured context (redacted)
- Optional `exc` string for exceptions (include stack trace)
- Redact keys recursively using `logging.redact_keys` (default includes `labelData`, `Authorization`, `apiKey`, `apiSecret`)
- Log **failure details**, not just pass/fail:
  - for per-order failures: include `order_number`, `process_number`, and a clear `reason`
  - for provider/HTTP failures: include `method`, `endpoint`/`url`, `status` (if available), and `attempt`/retry count
  - when applicable: include `orderId`, `shipmentId`, and `trackingNumber` (non-secret)

Deliverable: every run produces JSONL logs under `paths.logs_dir` (default `logs/`).

---

## Phase 2 — Provider contract + real provider (1–2 days)

### 2A) Provider contract

Create `providers/base.py` with methods matching the contract:
- `lookup_orders(order_number) -> list[Order]`
- `list_shipments(order_id, include_voided, page_size=None) -> list[Shipment]`
- `fetch_label(shipment_id) -> Label | None`
- `create_label(order, resolved fields..., settings...) -> Label | error`
- `void_label(shipment_id) -> success/failure`

Deliverable: provider contract is stable and real provider is wired.

---

## Phase 3 — Flow A: Convert (Excel/CSV → canonical orders list) (1–2 days)

Implement `flows/convert.py` exactly per `REQUIREMENTS.md`.

### 3A) Input discovery (A0)
- Scan `paths.desfiles_dir` (default `desfiles/`)
- If any `*.csv` exists, use **CSV mode** and ignore Excel
- Else if any `*.xlsx|*.xls|*.xlsm`, use **Excel mode**
- Else fail with “no files found”

### 3B) CSV mode parsing (A1)
- Case-insensitive header matching via `lower().strip()`
- Order aliases: `order - number`, `order number`, `ordernumber`, `order`
- Process aliases: `process num`, `process number`, `processnum`, `process`
- Missing columns: mark file invalid, print available columns + continue
- Row filtering rules:
  - order not null and not empty after trim
  - process cast to string + trim; drop if `""` or `"nan"`

### 3C) Excel mode parsing (A2)
- Strict headers: exactly `Order - Number` and `Process Num`
- Drop blank orders
- Process cleanup: string trim + remove leading `^Process\s*` (case-insensitive)

### 3D) Canonical output rules (A3)
- Concatenate valid rows across files
- Dedupe by order number (keep first)
- Output CSV columns exactly:
  - `Process Number`, `orders Numbers`
- Sorting:
  - `_sk = int(process)` if digits else `0`
  - Sort by `_sk`, then `Process Number` (string)

### 3E) Idempotency + archive (A4)
- SHA-256 hash file bytes in 1MB chunks
- Manifest: `desfiles_processed/.processed_manifest.json` with:
  - `{ "hashes": [...], "updated_at": "<iso>" }`
- If hash already in manifest:
  - skip processing that file
  - attempt deletion from `desfiles/`
- If hashing fails:
  - still process file
- On successful conversion:
  - move processed inputs to `desfiles_processed/`
  - prefix timestamp `YYYYMMDD_HHMMSS_`
  - update manifest with hashes of successfully processed files

Deliverable: running `convert` produces/updates the canonical CSV and archives inputs exactly as specified.

---

## Phase 4 — Flow B: Print (canonical orders → labels → per-process PDFs → combined PDF) (2–4 days)

### 4A) Read + group orders (B1)
- Read canonical CSV
- Identify columns case-insensitively:
  - process: first header containing both `process` and `number`
  - order: first header containing `order`, else first header containing `num`
- If process column missing: default all rows to process `"1"`
- Blank/falsey process values coerced to `"1"`

### 4B) Selection rules (B2.1–B2.3)
Implement in `rules/selection.py`:
- Provider lookup can return 0..N orders
- If multiple:
  - Prefer orders with **no active shipments**
  - If multiple awaiting: pick highest `orderId`
  - If none awaiting: treat as not processable
- Shipments selection:
  - sort by `shipmentId` desc
  - split active vs voided
  - if active exists, use active; else use voided and log warning

### 4C) Reuse vs create (idempotency)
- If active shipment exists:
  - try `fetch_label`
  - if base64 `labelData` present: decode + save (no create)
  - else fall back to create
- If only voided shipments exist:
  - allow create (warn)

### 4D) Carrier/service/package resolution + service mapping
Implement in `rules/service_map.py` and config defaults:
- Resolve in priority order:
  1) existing shipment fields (highest)
  2) else order fields
  3) else config defaults + service_map mapping
- **Hard fail** if `serviceCode` cannot be resolved.

### 4E) Weight normalization
Implement in `rules/weights.py`:
- `weight.ounce_carriers` substrings (case-insensitive) ⇒ normalize to ounces
- else normalize to pounds

### 4F) PDF artifacts and merging
Implement in `pdf/`:
- Decode base64 `labelData` and write:
  - individual per-order PDFs
  - temp per-process PDFs for merging
- Per-process PDF:
  1) summary page (ReportLab)
  2) all label pages
  3) missed orders page (only if failures exist)
- Combined PDF (quirk parity):
  - alternating pattern: Summary, Label, Summary, Label, ...

### 4G) Failures + logs artifacts
- Failures CSV header exactly:
  - `Customer Name,Process Number,Order Number,Order ID,Error Reason`
- Human-readable error log blocks exactly:
  - `Order:<order>`
  - `Customer:<name>`
  - `Process:<process>`
  - `Error:<reason>`

Deliverable: `print` produces:
- individual labels
- per-process PDFs
- combined PDF
- failures CSV + error log (when applicable)
- JSONL logs

---

## Phase 5 — Flow C: Void (void list → provider void) (1–2 days)

Implement `flows/void_labels.py`:
- Read `paths.void_csv` (default `void_labels.csv`)
- For each order number:
  - fetch order/shipments
  - find active shipments (non-voided)
  - void each active shipment
- Output: console summary + JSONL logs
- No PDFs created

Deliverable: voiding works in mock mode and updates persisted mock state (so “void then reprint” is testable).

---

## Phase 6 — Concurrency, retries, timeouts, and rate limiting (1–2 days)

Implement bounded concurrency + retries across provider calls:
- Worker count: `concurrency.max_workers` (default 25) with ENV override `MAX_CONCURRENCY`
- Timeouts:
  - request: `request_timeout_sec` (default 15)
  - label: `label_timeout_sec` (default 35)
- Retries:
  - `max_retries` (default 2)
  - exponential backoff within `retry_min_wait_sec..retry_max_wait_sec`
- Rate limiting:
  - on HTTP 429: honor `Retry-After` else sleep `rate_limit.fallback_wait_sec` (default 60)

Deliverable: reliable runs under transient failures (mock can simulate).

---

## Phase 7 — Tests for parity-critical rules (1–2 days)

Add targeted tests (fast, deterministic):
- **Convert flow**
  - CSV header alias detection
  - Excel strict header requirement
  - sort + dedupe behavior
  - manifest hashing + archive prefixing
- **Service mapping**
  - `carrier_key` transform parity
  - first-substring-match-wins parity
- **Weight normalization**
  - ounce-carrier substring behavior (case-insensitive)
- **Provider**
  - real provider contract behavior (API shape assumptions, error handling)

Deliverable: tests provide confidence the rebuild matches the requirements.

---

## Phase 8 — Real provider stub (later, after parity MVP)

Create `providers/real.py` as a placeholder now:
- Reads credentials from ENV (optionally `.env`), never YAML
- Uses `aiohttp`
- Implements the same contract as mock

Once real API details are provided, implement endpoints without changing core flows.

---

## Suggested MVP order (fastest to “working product”)

1) Phase 0–1 (config + logging)  
2) Phase 2 (provider layer)  
3) Phase 3 (convert)  
4) Phase 4 (print)  
5) Phase 5 (void)  
Then add Phase 6–7 hardening and tests.

---

## Parity Checklist + Acceptance Tests (definition of “done”)

Use this section as the go/no-go checklist for “meets `REQUIREMENTS.md`”.

### Legend

- **[AUTO]**: should be covered by automated tests
- **[MANUAL]**: verify by running the CLI and inspecting produced artifacts/logs

### Runtime + secrets handling

- **[MANUAL] Windows-first entrypoints exist**
  - Batch scripts run successfully: `bat_files\run_convert.bat`, `bat_files\run_print.bat`, `bat_files\ALL_VOID_LABELS.bat`.
- **[AUTO] No secrets in code/YAML**
  - Repo scan: `shipping_config.yaml` contains no keys that look like credentials; provider reads secrets only from ENV/`.env`.
- **[MANUAL] Real provider configured**
  - `print` succeeds with `SHIPPING_PROVIDER=real` configured.

### Config precedence + default values

- **[AUTO] Defaults match spec**
  - Effective config equals the defaults in `REQUIREMENTS.md` when no YAML and no ENV are present.
- **[AUTO] YAML overrides defaults**
  - Values changed in `shipping_config.yaml` override defaults.
- **[AUTO] ENV overrides YAML/defaults**
  - `MAX_CONCURRENCY`, `BATCH_NOTES`, `PROCESSED_BY`, `SHIP_FROM` override YAML/defaults.
  - `SHIPPING_PROVIDER` must be `real`.

### Flow A (Convert) parity — A0..A4

- **[AUTO] A0 input discovery priority**
  - If any `*.csv` exist in `paths.desfiles_dir`, CSV mode is used and Excel is ignored.
  - Else if Excel exists, Excel mode is used.
  - Else fail with “no files found” and do not produce new output.
- **[AUTO] A1 CSV header alias matching**
  - Case-insensitive `lower().strip()` matching.
  - Order aliases: `order - number`, `order number`, `ordernumber`, `order`.
  - Process aliases: `process num`, `process number`, `processnum`, `process`.
  - Missing order/process columns: file marked invalid; available columns reported; other files still processed.
- **[AUTO] A1 CSV row filtering**
  - Orders must be non-null and non-empty after trimming.
  - Process cast to string + trimmed; drop if `""` or `"nan"`.
- **[AUTO] A2 Excel strict headers + cleanup**
  - Only accept files with exact headers `Order - Number` and `Process Num`.
  - Drop blank orders.
  - Process cleanup removes `^Process\s*` (case-insensitive).
- **[AUTO] A3 Canonical output shape + sorting + de-dupe**
  - Output headers exactly: `Process Number`, `orders Numbers`.
  - Dedupe by order number keeping first.
  - Sort key `_sk=int(process)` if digits else `0`, sort by `_sk` then `Process Number` (string).
- **[AUTO] A4 Hash manifest + archive rules**
  - SHA-256 computed over bytes in 1MB chunks.
  - Manifest path: `desfiles_processed/.processed_manifest.json` with `{ hashes: [...], updated_at: <iso> }`.
  - If hash already seen: skip file and attempt delete from `desfiles/`.
  - If hashing fails: still process file.
  - On success: move processed inputs to `desfiles_processed/` with `YYYYMMDD_HHMMSS_` prefix; update manifest with successfully processed hashes.

### Provider contract

- **[AUTO] Provider interface supports required operations**
  - lookup orders by order number (0..N)
  - list shipments (include voided flag)
  - fetch label (may return None)
  - create label (returns base64 PDF labelData or error)
  - void label (success/failure)
### Flow B (Print) parity — B1..B4

- **[AUTO] B1 column matching and grouping**
  - Process column: first header containing both `process` and `number` (case-insensitive).
  - Order column: first header containing `order`, else first containing `num`.
  - If process column missing: all rows assigned process `"1"`.
  - Blank/falsey process coerced to `"1"`.
- **[AUTO] Order selection when provider returns multiple orders**
  - Prefer candidates with **no active shipments**.
  - If multiple awaiting: choose highest `orderId`.
  - If none awaiting: treat as not processable (failure recorded).
- **[AUTO] Shipment selection rule**
  - Sort shipments by `shipmentId` descending.
  - Prefer active (`voided=false`); otherwise use voided and log a warning.
- **[AUTO] Idempotency: reuse vs create**
  - If active shipment exists: fetch label; if `labelData` exists, do not create a new label.
  - If reuse fails or `labelData` missing: fall back to create-label.
  - If only voided shipments exist: allow create-label but log warning.
- **[AUTO] Field resolution + hard fail for missing serviceCode**
  - Resolve carrier/service/package from shipment → order → config defaults + service mapping.
  - If `serviceCode` cannot be resolved: order fails with clear error reason.
- **[AUTO] Label request settings match config**
  - `provider.test_label`, `provider.label_format`, `provider.label_layout`, `provider.label_download_type` honored.
- **[AUTO] Weight normalization rules**
  - If carrier contains any configured substring (case-insensitive), normalize to ounces; else pounds.
- **[MANUAL] Per-process PDF ordering**
  - Per-process PDF pages: Summary → all labels → Missed page (only if failures exist).
- **[MANUAL] Combined PDF quirk preserved**
  - Combined merge alternates: Summary, Label, Summary, Label, ... (current behavior).
- **[AUTO] Failure artifacts format**
  - Failures CSV header exactly: `Customer Name,Process Number,Order Number,Order ID,Error Reason`.
  - Human-readable error log contains blocks with:
    - `Order:<order>`
    - `Customer:<name>`
    - `Process:<process>`
    - `Error:<reason>`

### Flow C (Void) parity

- **[AUTO] Void behavior**
  - Reads void list CSV and extracts order numbers.
  - For each order: find active shipments (non-voided) and void each.
- **[MANUAL] No PDFs created**
  - `void` produces only logs/console summary (no new PDFs).

### Logging parity (human + JSONL)

- **[AUTO] JSONL event shape**
  - One JSON object per line containing: `ts` (**UTC ISO date+time**), `level`, `msg`, `logger`.
  - Optional: `extra` (redacted structured context), `exc` (stack trace string).
- **[AUTO] Errors include detailed context (not just pass/fail)**
  - Provider/HTTP errors include (when available): `method`, `endpoint`/`url`, `status`, `attempt` (retry count), and either a provider error payload summary or exception string.
  - Per-order failures include: `order_number`, `process_number`, and a human-readable `reason`.
  - When applicable, include correlation identifiers: `orderId`, `shipmentId`, `trackingNumber`.
- **[AUTO] Redaction works recursively**
  - Keys in `logging.redact_keys` never appear unredacted in the JSONL output (especially `labelData`).
- **[MANUAL] Key lifecycle events logged**
  - Run start/end (counts, elapsed).
  - Per-order failures include a clear reason string.
- **[MANUAL] Human-readable error log includes date+time**
  - Each per-order error block includes a timestamp line (UTC ISO) so failures can be correlated with JSONL events.

### Concurrency + retries + rate limiting

- **[AUTO] Concurrency limit enforced**
  - Number of in-flight provider calls does not exceed configured worker count.
- **[AUTO] Retry/backoff is bounded**
  - Retries limited by `max_retries` and wait bounds.
- **[AUTO/MANUAL] 429 handling**
  - If `Retry-After` present, it is honored; else fallback wait is used.

