# Production Design Queue Manager — key findings

- Consumes DTF Des Excel/CSV with columns such as `Order - Number`, `Item - SKU`, `Item - Qty`, `Process Num`, `Ship To - Name`.
- Print sizes: live CL CSV Width/Height mm (universal SKU match). Configuration Workbook Size References is archive for sizing; Pocket / Override Print Size stays local.
- Design Queues watcher: `scripts/design_queues_watcher.py` watches SharedInbox; folders from `queue_app_settings.json`; no approval; Processed/Failed under SharedInbox.
- PLAINLG in Item SKU skips design search.
- Canvas: 570×3000 mm default @ 300 DPI; packing gaps documented in USAGE.
- No ShipStation API in this app.
- Issue resolutions: `.cursor/issue-log.md`.
- **1-SP JPEG position hints (locked 2026-09-22):** Duplicate-order SKU files in the single folder only. Companion JPEG `-P-` / `-S-` / `-S1-` / `-S2-` is a hint; only the PNG is queued (80×100 / 100×100). JPEG-only does not invent a design. Apparel size `S` in the SKU is not a sleeve. Legacy `{Order}-P.png` / `-S.png` unchanged (kids `-K-` still 65×80 on that PNG-suffix path). Main search stays PNG-only. Missing Logo inherits via `process_personalised_designs`.
