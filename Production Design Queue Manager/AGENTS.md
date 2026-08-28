# Production Design Queue Manager — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/production-design-queue-manager/`. Details: `USAGE.md`, `docs/DOCUMENTATION.md`.

Live paths via `shared/paths.py` (DB in `database/`; settings + I/O in this app; SharedInbox + CL CSV shared).

## Live vs helpers

| Live | Other |
|------|--------|
| `queue_app.py` / `run_queue_app.bat` | docs |
| `run_auto_missing_logo.bat` | SharedInbox Missing Logo watcher |
| `config/queue_app_settings.json` | Design folder paths |
| `database/production-design-queue-manager/Configuration Workbook.xlsx` | Pocket / Override Print Size |
| `database/shared/custom_label/Custom_Label_Database.csv` | Print sizes via universal SKU match |
| `runtime/SharedInbox/DTF Des/` | Auto input |
| `{Output,Logs,Missing Size Reference}/` | App-local I/O |

## How work is done

**Auto:** watcher on SharedInbox → Missing Logo using settings folders → timestamped PNG under app Output → move source to `Processed/` (or `Failed/`). No approval.

**GUI:** Load DTF Des → Normal / Personalised / Missing Logo → pack canvas → preview → Save PNG. GUI batches still need supervisor approval.

## Hard do-nots

- Do not treat CL Size References CSV or Workbook Size References as the live size table (CL CSV print mm is live).
- Do not invent size codes; export missing rows and ask before guessing.
- No live GUI Output batch without **yes / do it / fill / run** (auto Missing Logo is the exception).

## Report changes

Report mode, input file(s), size hits/misses, output paths. Log resolved issues to `.cursor/issue-log.md`.
