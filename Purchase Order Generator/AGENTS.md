# Purchase Order Generator — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/purchase-order-generator/`. Layout facts: `FOLDER_LAYOUT.md`, `docs/`.

Also known in older docs as **Plain Orders**.

## Live vs helpers

| Live | Other |
|------|--------|
| `Run_GUI.bat` → `scripts/run_script_gui.py` | Maintenance scripts under `scripts/` |
| `data/Database.xlsx`, packs DB, tags workbook | `data/archive/` (includes former local CL CSV) |
| `../Custom Label Database/Custom_Label_Database.csv` | Custom Label → BTC SKU |
| BTC stock CSV under `data/` (FTP) | `assets/product_images/`, `brand_logos/` |
| `output/` tag run folders | `config.py` secrets |

## How work is done

Fetch ShipStation awaiting-dispatch by tag → primary stock id (before first dash) → else universal CL match → `BTC SKU` → free_stock → packing-slip PDFs / outputs under `output/`. Sync `Database.xlsx` from ProductExport and download images with maintenance scripts when asked (`--dry-run` first).

## Hard do-nots

- Do not paste credentials from `config.py` into docs or chat.
- Do not reinstate a second live CL CSV under `data/` as the stock map source.
- No live sync/output runs without **yes / do it / fill / run**.

## Report changes

Report tags/orders processed, stock misses, output folder name, and any `data/` files updated (with backup path if created).
