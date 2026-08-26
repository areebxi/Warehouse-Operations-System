# Purchase Order Generator — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/purchase-order-generator/`. Layout facts: `FOLDER_LAYOUT.md`, `docs/`.

Also known in older docs as **Plain Orders**. App folder = **code only**.

## Live vs helpers

| Live | Other |
|------|--------|
| `Run_GUI.bat` → `scripts/run_script_gui.py` | Maintenance scripts under `scripts/` |
| `data/PurchaseOrder/` (Database, packs, stock) | `data/archive/` former local CL |
| `Custom Label Database/Custom_Label_Database.csv` | Custom Label → BTC SKU |
| `data/shipstation/ShipStation_Tags.xlsx` | Shared |
| `data/product_export/ProductExport.csv` | Shared |
| `data/images/purchase_order/` | brand_logos / product_images |
| `runtime/PurchaseOrder/Output/` | `config/PurchaseOrder/config.py` |

## How work is done

Fetch ShipStation awaiting-dispatch by tag → primary stock id (before first dash) → else universal CL match → `BTC SKU` → free_stock → packing-slip PDFs under Runtime output.

## Hard do-nots

- Do not paste credentials from `config.py` into docs or chat.
- Do not reinstate a second live CL CSV as the stock map source.
- No live sync/output runs without **yes / do it / fill / run**.

## Report changes

Report tags/orders processed, stock misses, output folder name, and any Data files updated (with backup path if created).
