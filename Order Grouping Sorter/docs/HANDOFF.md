# Handoff — Order Grouping Sorter

**Status:** Packing PIN short form locked 2026-09-23 (`B100-S1-1 Item 1` from filename `B100-S1-PRINTED-…`). Leftover batches `B1`/`B2`/… skip reserved fixed codes. Batch / process number / item number vocabulary locked same day. Fixed batches (`B100`, `B1000`, …) locked 2026-09-23; **B50** = B100 twin, Supplier On Demand only (locked + built 2026-09-30; no other On Demand mirrors). **B40** also matches Gender Apparel contains `GILDAN` (locked + built 2026-10-07). Cousin numbers retired same day. Shift-first filename locked 2026-09-22. Mixed supply-method locked 2026-09-22. No-dash SKUs match CL whole (`A515`). Blank ship-by → today (in awaiting_shipment → pull today; 2026-09-24). Skip `DTFOcean.co.uk WP`. Skip tag `00000-Warehouse OOS` (locked 2026-10-09). Mixed printed P vs R locked 2026-09-17. Hashim #038 as before. **Hashim #037** date split is leftover only; **fixed batches are one CSV per code per shift** (locked 2026-10-08). Testing rewrites `1st Shift` each `--run`. **Chat fast path (2026-10-07):** “run the group sorter” → straight `--run`. **Catalog cache (2026-10-07):** Plain/Packs pickle under `database/order-grouping-sorter/catalog_cache/`. Last Input write 2026-09-30 (`30-09-2026` / `1st Shift`).

**Dry-run:** `python "Order Grouping Sorter/scripts/run_sorter.py"` from warehouse root (optional `--run-date YYYY-MM-DD`).

**Write Packing Input:** `python "Order Grouping Sorter/scripts/run_sorter.py" --run` after supervisor **run** (chat phrases above count as **run**). Testing: every `--run` writes `1st Shift` (replaces those CSVs). `RESEND.csv` / `UNMATCHED.csv` land there. Production later: nth `--run` of the day = nth shift.

**Self-check:** `python "Order Grouping Sorter/scripts/test_grouping.py"`, `python "Order Grouping Sorter/scripts/test_catalog_cache.py"`, and `python scripts/test_taxonomy_picklist.py`

**Locks / progress:** `order-grouping-locks.md`, `order-grouping-criteria.csv`, and `order-grouping-progress.xlsx` live in this app folder. Regenerate the workbook: `python "Order Grouping Sorter/scripts/write_order_grouping_progress.py"`.

**Not built yet:** leftover floor numbers for stickers / mugs / Gildan / packs / plain / Fawad Prime FOTL. `SHIFT_PER_RUN` (nth `--run` of the day = nth shift) waits for production. Priority field 6: today first, then prime first, then as files are made (more ranking later).

**Absolute Product Data (2026-10-13):** sorter reads the price list with Plain and Packs. Stock Code (`AA22-36-L`) is plain, supplier Absolute Apparels, after Plain and before Packs. BTC UID / Uneek short code still win over a style that is only listed on that sheet.

**Shared already on this warehouse:** `shared.paths` sorter helpers; `shared.shipstation.parse_stores_payload` + `list_stores`. Grouping CL file is `Custom_Label_Database (Areeb).csv` via `cl_areeb_csv_path` (locked 2026-10-09, temporary — four Areeb columns filled). Spaced headers still go through `rename_legacy_headers` (`python "Order Grouping Sorter/scripts/test_cl_legacy_headers.py"`). Other apps keep the live NocoDB export `Custom_Label_Database.csv`. Packs catalog is `database/shared/packs/Packs Database.csv` (whole SKU → Channel Child SKU).
