# Fixed batches

Live table (codes + Graph criteria):  
[`database/order-grouping-sorter/fixed_batches.csv`](../database/order-grouping-sorter/fixed_batches.csv)

Meta columns: `batch_code`, `name`, `notes`.

Criteria columns (cell `any` / `x` / blank = do not care), Graph order:

| Column | Meaning |
|--------|---------|
| order-status | awaiting_shipment / resend / … |
| ship-by-date | today / future |
| product-finish | plain / printed |
| order-source | fawad / own |
| design-grouping | x until on |
| shipping-service | prime / non-prime / any |
| printing-method | dtf / … |
| customised | readymade / customised |
| customisation-type | x until filled |
| print-size | x until on |
| print-position | x until on |
| supply-method | Warehouse Stock / In House Manufacture / … |
| supplier | x when Warehouse Stock / In House (printed) |
| package-type | x until on |
| category | T-SHIRTS / Iron-On / … |
| product-type | `ss_fotl` / `iron_on` / `gildan_tee` / `mug` / `babysuit` / `packs` tokens, or literal type(s) `A;B` |
| product-style / department / brand / size / color | usually `any` for fixed batches |
| destination | `international` = ShipStation ship-to country not `GB` |
| item-name-contains / item-name-not-contains | `;` list; any line; hyphen ≈ space |
| sku-contains / sku-not-contains | `;` list; any line. `=M61` = whole dash-separated SKU part; else substring |

Path helper: `shared.paths.sorter_fixed_batches_path`.  
Loader / match: `scripts/fixed_batches.py` + `grouping.fixed_batch_matches`.

Row order = priority: first match wins (locked 2026-09-28). Dry-run prints `fixed-batch overlaps` for orders that also met a lower row. Plain piles with no fixed batch take `B2000`, `B2100`, `B2200`, `B2500`, `B2600`, `B2700`, … in the order made. `gildan_tee` = Brand Gildan + T-Shirts **or** style token `5000` / `G5000` in Item SKU or Gender Apparel (not a substring of `15000`).

`gildan_tee` (B40): Category T-Shirts + (Brand Gildan **or** Gender Apparel contains GILDAN **or** style token `5000` / `G5000` in Item SKU or Gender Apparel; not a substring of `15000`).

To add or change a fixed batch, edit that CSV.
