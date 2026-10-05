# Production Design Queue Manager — snapshot

**Updated:** 5 October 2026 (SharedInbox watcher renamed Design Queues watcher)  
**Handbook:** `AGENTS.md`

## Continue here

- GUI: `run_queue_app.bat` or `pythonw queue_app.py`.
- Save PNG(s) writes to `Output/YYYY-MM-DD/` and, if DTF Queues Folder is set, copies those PNGs there (no RAR).
- Design Queues watcher: Packing List starts it on launch, or `run_design_queues_watcher.bat` (SharedInbox; folders from `config/queue_app_settings.json`).
- Auto Output PNGs use the same names as GUI (`P50.png`, `P50_Part 1.png`); re-runs overwrite.
- Print sizes: CL CSV; Pocket overrides: Configuration Workbook.
- GUI action: one **Run** button — Customise=Yes uses Single/Double folders; otherwise Normal designs folder.
- Personalised duplicate SKU files: 1-SP JPEG `-P-`/`-S-`/`-S1-`/`-S2-`/`-SL-`/`-SR-` is a size hint; only the PNG is queued.
- Designs capped at 300×500 mm (double-folder path exempt). Unique orders also try `{Order}-{SKU}.png` first.
- Slow Drive I/O runs with UI keepalive so the window stays responsive. Preview labels use filename stems.

## Watch

- Missing size rows export under `Missing Size Reference/`.
- Canvas default width 570 mm (usable DTF on 600 mm film after hold plates).
- Auto-run needs design folders configured in settings before it can succeed.
