# config/

Machine-local secrets and GUI settings.
Copy `*.example` / `config_example.py` templates; do not commit live secrets.

| Folder | Contents |
|--------|----------|
| `ShipStation/` | Only place for ShipStation `REAL_API_*` (`.env`) |
| `Packing/` | GUI JSON |
| `Shipping/` | `shipping_config.yaml`; optional app `.env` (no API keys) |
| `PurchaseOrder/` | FTP/`config.py` |
| `Queue/` | `queue_app_settings.json` |
