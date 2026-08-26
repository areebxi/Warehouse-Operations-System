# Purchase Order Generator — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/purchase-order-generator/`. Layout facts: `FOLDER_LAYOUT.md`, `docs/`.

Also known in older docs as **Plain Orders**. Live paths via `shared/paths.py` (data/assets/output/config.py in this app; PE + Tags + ShipStation shared).

## Live vs helpers

| Live | Other |
|------|--------|
| `Run_GUI.bat` → `scripts/run_script_gui.py` | Maintenance scripts under `scripts/` |
| `data/` (Database, packs, stock) | `data/archive/` at warehouse for former local CL |
| `Custom Label Database/Custom_Label_Database.csv` | Custom Label → BTC SKU |
| `data/shipstation/ShipStation_Tags.xlsx` | Shared |
| `data/product_export/ProductExport.csv` | Shared |
| `assets/` | brand_logos / product_images |
| `output/` | `config.py` (FTP only) |
| `config/ShipStation/.env` | Shared ShipStation `REAL_API_*` |

## How work is done

Fetch ShipStation awaiting-dispatch **by tag** (`shared.shipstation` / `orders/listbytag`) → primary stock id (before first dash) → else universal CL match → `BTC SKU` → free_stock → packing-slip PDFs under `output/`.

## Hard do-nots

- Do not paste credentials into docs or chat. ShipStation keys live in `config/ShipStation/.env`, not `config.py`.
- Do not reinstate a second live CL CSV as the stock map source.
- No live sync/output runs without **yes / do it / fill / run**.

## Report changes

Report tags/orders processed, stock misses, output folder name, and any data files updated (with backup path if created).
