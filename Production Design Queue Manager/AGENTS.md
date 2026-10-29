# Production Design Queue Manager — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/production-design-queue-manager/`. Details: `USAGE.md`, `../docs/production-design-queue-manager/DOCUMENTATION.md`.
Current state: `../docs/production-design-queue-manager/HANDOFF.md`, kept as present-tense state, not a log.

Live paths via `shared/paths.py` (DB in `database/`; settings + Input in this app; Logs/Output under warehouse-root; SharedInbox + CL CSV shared).

## Live vs helpers

| Live | Other |
|------|--------|
| `queue_app.py` / `run_queue_app.bat` | `../docs/production-design-queue-manager/` |
| `scripts/design_queues_watcher.py` | SharedInbox Design Queues watcher (Packing auto-starts) |
| `config/queue_app_settings.json` | Design folder paths |
| `database/production-design-queue-manager/Configuration Workbook.xlsx` | Pocket / Override Print Size; Skip Batches |
| `database/shared/custom_label/Custom_Label_Database.csv` | Print sizes via universal SKU match |
| `runtime/SharedInbox/DTF Des/` | Auto input |
| `Input/` (+ Missing Print Sizes) | App-local intake / missing CL print-size exports |
| `Output|Logs/Production Design Queue Manager/` | Warehouse-root run I/O |

## How work is done

**Auto:** Design Queues watcher on SharedInbox (or Packing `--files` sync) → settings folders → PNG under `Output/Production Design Queue Manager/` (same names as GUI, e.g. `50.png` from `DTF Des-P50`, `B100-S1.png` from `DTF Des-PB100-S1`) → optional DTF Queues folder copy → move inbox source to `Processed/` (or `Failed/`). **Skip Batches** sheet skips PNG for listed batch digits. No approval.

**GUI:** Load DTF Des → **Run** (Customise column picks Normal vs Single/Double folders) → pack canvas → preview → Save PNG. GUI batches still need supervisor approval.

## Hard do-nots

- Do not treat CL Size References CSV or Workbook Size References as the live size table (CL CSV print mm is live).
- Do not invent size codes; export missing rows and ask before guessing.
- No live GUI Output batch without **yes / do it / fill / run** (Design Queues watcher is the exception).

## Report changes

Report mode, input file(s), size hits/misses, output paths. Log resolved issues to `.cursor/issue-log.md`.

## Structure & boundaries

- **Orchestration:** `queue_app.py` (+ `scripts/queue_app_impl.py` / `queue_app_gui_setup.py` / `queue_app_gui_actions.py`); Design Queues watcher `scripts/design_queues_watcher.py` → `design_queues_{process,loop,inbox}.py` (Packing auto-starts).
- **Domain:** `scripts/src/core/` (canvas, sizes, image rules; façades + `*_impl*` helpers).
- **I/O:** `scripts/src/io/`; GUI helpers under `scripts/gui_helpers/` (missing-logo / personalised: `gui_processing_ui_*.py` + `*_load.py`).
- **Logging:** `scripts/src/system/logging/console.py` → `console_setup` / `console_close` / `console_state`.
- **200-line:** live Queue scripts cleared; keep new/changed modules ≤200 (see `../docs/ARCHITECTURE.md`).
- **Must not:** import Packing/Shipping/Sorter internals; path resolution outside `shared.paths`; invent size codes.
- Architecture: `.cursor/rules/global/architecture.mdc`.
