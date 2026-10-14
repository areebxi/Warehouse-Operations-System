# Production Design Queue Manager — snapshot

**Updated:** 13 October 2026 (letter index PNGs)  
**Handbook:** `AGENTS.md`

## Continue here

- GUI: `run_queue_app.bat` or `pythonw queue_app.py`.
- Save PNG(s) writes to `Output/YYYY-MM-DD/` and, if DTF Queues Folder is set, copies those PNGs there (no RAR).
- Design Queues watcher: Packing List sync-invokes `--files` after Excel when Make design queues is on; continuous watch via Packing launch or `run_design_queues_watcher.bat`.
- Headless save also copies PNGs to DTF Queues folder when configured (same as GUI Save).
- **Skip Batches** sheet in Configuration Workbook: batch digits listed there skip queue PNGs (file still Processed; leftover Output/DTF Queues PNGs removed). Matches sorter `PB70-S1` and packing `P3570` stems. Packing also skips SharedInbox dual-write for those batches (avoids watcher race).
- Auto Output PNGs use the same names as GUI (`50.png` from `DTF Des-P50`, `B100-S1.png` from `DTF Des-PB100-S1`, `50_Part 1.png`); re-runs overwrite. The packing `P` is not written.
- Print sizes: CL CSV via `shared/cl_columns` (legacy spaced headers renamed to NocoDB names on load); Pocket overrides + Skip Batches: Configuration Workbook.
- GUI action: one **Run** button — Customise=Yes uses Single/Double folders; otherwise Normal designs folder.
- Personalised single-folder PNG: a companion JPEG `-P` / `-S` / `-S1` / `-S2` / `-SL` / `-SR` (before the SKU, or `{order}-P.jpg` beside `{order}.png`) sets the PNG to 80×100 or 100×100. The JPEG is not queued.
- Designs capped at 300×500 mm (double-folder path exempt). Unique orders also try `{Order}-{SKU}.png` first.
- Slow Drive I/O runs with UI keepalive so the window stays responsive. Preview labels use filename stems.

## Watch

- Missing size rows export under `Missing Size Reference/`.
- Canvas default width 570 mm (usable DTF on 600 mm film after hold plates).
- Auto-run needs design folders configured in settings before it can succeed.
