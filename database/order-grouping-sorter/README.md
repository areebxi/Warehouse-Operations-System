# database/order-grouping-sorter/

Sorter configuration that grouping **reads** (it does not overwrite catalogs).

| File | Role |
|------|------|
| `taxonomy_picklists.csv` | Closed pick-lists for the four Areeb columns (category / product type / product style / department) plus PE subcategory (Hashim #038). Title Case. Product type has no gender. Product style is a named product, never a supplier code. New products pick from these rows. Do not invent a value in fill. To allow a new value, add it in `shared/taxonomy_catalog.py` and rebuild (do not re-harvest ad hoc catalog inventions). |
| `fixed_batches.csv` | Fixed batch codes (`B40` / `B80` / `B100` / `B1050` / `B3500` / `B3700` / …) plus Graph criteria in order: order-status, ship-by-date, product-finish, …, color, plus `item-name-contains` / `sku-contains`. Cell `any` / `x` = do not care. `product-type` tokens `ss_fotl` / `iron_on` / `gildan_tee` drive garment match. First matching row wins. Edit this file to add or change a fixed batch. |
| `leftover_batches/{YYYY-MM-DD}.csv` | **Written by the sorter** each run (dry-run and `--run`). One file per run date; overwritten on the next run that day. Same columns as `fixed_batches.csv`. Rows = leftover `B1` / `B2` / … piles assigned that run (Graph + 30-chain criteria). Fixed-batch codes are not listed here. |

Code: `shared/taxonomy_picklist.py` + `shared/taxonomy_catalog.py`. Rebuild pick-lists: `python scripts/build_taxonomy_picklists.py`.  
Fixed batches: `Order Grouping Sorter/scripts/fixed_batches.py` + `grouping.named_process_code`.  
Leftover batches: `Order Grouping Sorter/scripts/leftover_batches.py` (path `shared.paths.sorter_leftover_batches_path`).
