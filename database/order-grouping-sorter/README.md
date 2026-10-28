# database/order-grouping-sorter/

Sorter configuration that grouping **reads** (it does not overwrite catalogs).

| File | Role |
|------|------|
| `taxonomy_picklists.csv` | Closed pick-lists for the four Areeb columns (category / product type / product style / department) plus PE subcategory (Hashim #038). Title Case. Product type has no gender. Product style is a named product, never a supplier code. New products pick from these rows. Do not invent a value in fill. To allow a new value, add it in `shared/taxonomy_catalog.py` and rebuild (do not re-harvest ad hoc catalog inventions). |
| `areeb_column_dropdowns.csv` | `Column,Value` rows for Areeb category / product type / product style / department dropdown lists. Path helper: `shared.paths.sorter_areeb_column_dropdowns_path`. Not read by the grouping run itself. |
| `fixed_batches.csv` | Fixed batch codes (`B40` / `B80` / `B100` / `B1050` / `B3500` / `B3700` / …) plus Graph criteria in order: order-status, ship-by-date, product-finish, …, color, plus `item-name-contains` / `sku-contains`. Cell `any` / `x` = do not care. `product-type` tokens `ss_fotl` / `iron_on` / `gildan_tee` drive garment match. First matching row wins. Edit this file to add or change a fixed batch. |
| `catalog_cache/` | Plain/Packs index pickles (auto; gitignored). |

Leftover `B1`/`B2`… criteria CSVs are **not** here — they live under `Logs/Order Grouping Sorter/leftover_batches/` (`shared.paths.sorter_leftover_batches_path`).

Code: `shared/taxonomy_picklist.py` + `shared/taxonomy_catalog.py`. Rebuild pick-lists: `python scripts/build_taxonomy_picklists.py`.  
Fixed batches: `Order Grouping Sorter/scripts/fixed_batches.py` + `grouping.named_process_code`.  
Leftover batches: `Order Grouping Sorter/scripts/leftover_batches.py`.
