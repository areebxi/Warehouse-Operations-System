# database/

Live **database** files for the warehouse system. App folders hold code + run I/O only.

| Path | Role |
|------|------|
| `shared/product_export/ProductExport.csv` | Product Export (CL + PO) |
| `shared/shipstation/ShipStation_Tags.xlsx` | ShipStation tags (Packing + PO) |
| `shared/custom_label/Custom_Label_Database.csv` | Live CL catalog (+ `backups/`) |
| `shared/archive/` | Shared backups / former local copies |
| `custom-label-database/support/` | Size refs, mocks, shirts print sizes |
| `custom-label-database/Apparel Images/` | CL apparel images |
| `order-packing-list-generator/` | Packing Workbook, New SKU DB, All Orders log |
| `production-design-queue-manager/` | Configuration Workbook (pocket overrides) |
| `purchase-order-generator/` | Database.xlsx, packs, stock CSVs |
| `shipping-label-generator/` | Reserved (no live DB today) |

Resolve via `shared/paths.py`. Do not commit live files (see root `.gitignore`).

Legacy `data/` at warehouse root is retired — contents moved here under `shared/`.
