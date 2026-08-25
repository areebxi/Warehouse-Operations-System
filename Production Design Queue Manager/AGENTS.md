# Production Design Queue Manager — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/production-design-queue-manager/`. Details: `USAGE.md`, `docs/DOCUMENTATION.md`.

## Live vs helpers

| Live | Other |
|------|--------|
| `queue_app.py` / `run_queue_app.bat` | `tests/`, `Versions/` (old snapshots) |
| `run_auto_missing_logo.bat` | Shared Inbox Missing Logo watcher |
| `config/queue_app_settings.json` | Design folder paths |
| `config/Configuration Workbook.xlsx` | Pocket / Override Print Size (Size Refs archive for sizing) |
| CL `Custom_Label_Database.csv` | Print sizes via universal SKU match |
| Shared Inbox / GUI DTF Des | Same shape as packing `DTF Des-P*.xlsx` |
| `Output/`, `Logs/`, `Missing Size Reference/` | |

## How work is done

**Auto:** watcher on `Shared Inbox/DTF Des/` → Missing Logo using settings folders → timestamped PNG under `Output/` → move source to `Processed/` (or `Failed/`). No approval.

**GUI:** Load DTF Des → Normal / Personalised / Missing Logo → pack canvas (default 570×3000 mm @ 300 DPI) → preview → Save PNG (+ optional RAR). GUI batches still need supervisor approval.

## Hard do-nots

- Do not treat CL `support/Size References.csv` or Workbook Size References as the live size table (CL CSV print mm is live).
- Do not invent size codes; export missing rows and ask before guessing.
- No live GUI Output batch without **yes / do it / fill / run** (auto Missing Logo is the exception).

## Report changes

Report mode, input file(s), size hits/misses, output paths. Log resolved issues to `.cursor/issue-log.md`.
