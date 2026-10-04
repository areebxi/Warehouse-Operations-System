# Production Design Queue Manager — snapshot

**Updated:** 4 October 2026 (300×500 max size, SL/SR tokens, Order+SKU search, UI keepalive, stem preview labels)  
**Handbook:** `AGENTS.md`

## Continue here

- GUI: `run_queue_app.bat` or `pythonw queue_app.py`.
- Auto Missing Logo: `run_auto_missing_logo.bat` (watches SharedInbox; folders from `config/queue_app_settings.json`).
- Print sizes: CL CSV; Pocket overrides: Configuration Workbook.
- Modes (GUI): Normal, Personalised, Missing Logo.
- Personalised duplicate SKU files: 1-SP JPEG `-P-`/`-S-`/`-S1-`/`-S2-`/`-SL-`/`-SR-` is a size hint; only the PNG is queued.
- Designs capped at 300×500 mm (double-folder path exempt). Unique orders also try `{Order}-{SKU}.png` first.
- Slow Drive I/O runs with UI keepalive so the window stays responsive. Preview labels use filename stems.

## Watch

- Missing size rows export under `Missing Size Reference/`.
- Canvas default width 570 mm (usable DTF on 600 mm film after hold plates).
- Auto-run needs design folders configured in settings before it can succeed.
