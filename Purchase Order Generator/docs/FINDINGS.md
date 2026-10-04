# Purchase Order Generator — key findings

- GUI title / folder: Purchase Order Generator. Older docs title: Plain Orders App.
- ShipStation API for awaiting-dispatch orders by tag.
- BTC stock via FTP/SFTP into `data/` (`stock_id`, `free_stock`).
- Packing slips look up `data/Database.xlsx` by SKU (= BTC UID). **Later (not built, 2026-09-17):** those packing lists move to Order Packing List Generator; this app is EDI/stock only.
- Custom label → stock id via CL app `Custom_Label_Database.csv` (`BTC SKU` only; legacy `BTC Stock ID` retired 2026-10-04). Universal match in `shared/cl_sku_match.py`.
- Former local `data/Custom Label Database.csv` archived under `data/archive/`.
- Not connected to NocoDB.
