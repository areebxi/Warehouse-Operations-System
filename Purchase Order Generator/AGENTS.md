# Purchase Order Generator — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/purchase-order-generator/`. Layout facts: `FOLDER_LAYOUT.md`, `docs/`.

Also known in older docs as **Plain Orders**. Live paths via `shared/paths.py` (DB in `database/`; assets/output/config in this app; PE + Tags + ShipStation shared).

## Live vs helpers

| Live | Other |
|------|--------|
| `Run_GUI.bat` → `scripts/run_script_gui.py` | Maintenance scripts under `scripts/` |
| `database/purchase-order-generator/` | Stock CSVs (Plain / Packs are shared) |
| `database/shared/custom_label/Custom_Label_Database.csv` | Custom Label → BTC SKU |
| `database/shared/plain/Plain Database.xlsx` | Shared plain catalog |
| `database/shared/packs/Packs Database.xlsx` | Shared packs catalog |
| `database/shared/shipstation_tags/ShipStation_Tags.xlsx` | Shared |
| `database/shared/btc_product_data/BTC_Product_Data.csv` | Shared BTC Product Data |
| `database/shared/uneek_product_data/Uneek_Product_Data.xlsx` | Shared Uneek Product Data |
| `database/shared/absolute_product_data/Absolute_Product_Data.xlsx` | Shared Absolute Product Data (babysuits only) |
| `assets/` | brand_logos / product_images |
| `output/` | `config.py` (FTP only) |
| `config/ShipStation/.env` | Shared ShipStation `REAL_API_*` |

## How work is done

Fetch ShipStation awaiting-dispatch **by tag** (`shared.shipstation` / `orders/listbytag`) → primary stock id (before first dash) → else universal CL match → `BTC SKU` → free_stock → packing-slip PDFs under `output/`.

**Later (not built, 2026-09-17):** packing list PDFs (including these slips) move to **Order Packing List Generator**. This app stays tag → stock / EDI. Do not grow packing-slip work as the long-term home.

Grouping column **`Supplier Name`** filled 2026-09-09 on Plain Database (`BTC Activewear` / `Uneek Clothing`). Absolute babysuits are on Custom Label only.

## Hard do-nots

- Do not paste credentials into docs or chat. ShipStation keys live in `config/ShipStation/.env`, not `config.py`.
- Do not reinstate a second live CL CSV as the stock map source.
- No live sync/output runs without **yes / do it / fill / run**.

## Report changes

Report tags/orders processed, stock misses, output folder name, and any data files updated (with backup path if created).
