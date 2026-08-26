# Production Design Queue Manager — key findings

- Consumes DTF Des Excel/CSV with columns such as `Order - Number`, `Item - SKU`, `Item - Qty`, `Process Num`, `Ship To - Name`.
- Print sizes: live CL CSV Width/Height mm (universal SKU match). Configuration Workbook Size References is archive for sizing; Pocket / Override Print Size stays local.
- Auto Missing Logo: `scripts/auto_missing_logo_watcher.py` watches SharedInbox; folders from `queue_app_settings.json`; no approval; Processed/Failed under SharedInbox.
- PLAINLG in Item SKU skips design search.
- Canvas: 570×3000 mm default @ 300 DPI; packing gaps documented in USAGE.
- No ShipStation API in this app.
- Issue resolutions: `.cursor/issue-log.md`.
