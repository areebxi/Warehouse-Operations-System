# database/

Live **database** files for the warehouse system. App folders hold code + run I/O only.

| Path | Role |
|------|------|
| `shared/btc_product_data/BTC_Product_Data.csv` | BTC Product Data (CL + PO) |
| `shared/uneek_product_data/Uneek_Product_Data.xlsx` | Uneek Product Data (CL + PO) |
| `shared/absolute_product_data/Absolute_Product_Data.xlsx` | Absolute Product Data (babysuits C800T / C8020T / C8030T only) |
| `shared/shipstation/ShipStation_Tags.xlsx` | ShipStation tags (Packing + PO) |
| `shared/custom_label/Custom_Label_Database.csv` | Live CL catalog (+ `backups/`) |
| `shared/plain/Plain Database.xlsx` | Shared plain catalog (grouping + PO; + `archive/`) |
| `shared/packs/Packs Database.xlsx` | Shared packs catalog (grouping + PO; + `archive/`) |
| `shared/archive/` | Shared backups / former local copies |
| `custom-label-database/support/` | Size refs, mocks, shirts print sizes |
| `custom-label-database/Apparel Images/` | CL apparel images |
| `order-packing-list-generator/` | Packing Workbook, New SKU DB, All Orders log |
| `production-design-queue-manager/` | Configuration Workbook (pocket overrides) |
| `purchase-order-generator/` | Stock CSVs (+ Movie Poster SKUs); Plain/Packs live under `shared/` |
| `shipping-label-generator/` | Reserved (no live DB today) |

Testing-mode demo placeholders live at warehouse root: `Demo Images Database/` (see its README).

Resolve via `shared/paths.py`. Do not commit live files (see root `.gitignore`).

Legacy `data/` at warehouse root is retired — contents moved here under `shared/`.
