# Handoff — Order Grouping Sorter

**Status:** Packing PIN short form locked 2026-09-23 (`B100-S1-1 Item 1` from filename `B100-S1-PRINTED-…`). Leftover batches `B1`/`B2`/… skip reserved fixed codes. Batch / process number / item number vocabulary locked same day. Fixed batches (`B100`, `B1000`, …) locked 2026-09-23; **B50** = B100 twin, Supplier On Demand only (locked + built 2026-09-30; no other On Demand mirrors). **B40** also matches Gender Apparel contains `GILDAN` (locked + built 2026-10-07). Cousin numbers retired same day. Shift-first filename locked 2026-09-22. Mixed supply-method locked 2026-09-22. No-dash SKUs match CL whole (`A515`). Blank ship-by → today (in awaiting_shipment → pull today; 2026-09-24). Skip `DTFOcean.co.uk WP`. Mixed printed P vs R locked 2026-09-17. Hashim #038 / #037 as before. Testing rewrites `1st Shift` each `--run`. **Chat fast path (2026-10-07):** “run the group sorter” → straight `--run`. **Catalog cache (2026-10-07):** Plain/Packs pickle under `database/order-grouping-sorter/catalog_cache/`. Last Input write 2026-09-30 (`30-09-2026` / `1st Shift`).

**Dry-run:** `python "Order Grouping Sorter/scripts/run_sorter.py"` from warehouse root (optional `--run-date YYYY-MM-DD`).

**Write Packing Input:** `python "Order Grouping Sorter/scripts/run_sorter.py" --run` after supervisor **run** (chat phrases above count as **run**). Testing: every `--run` writes `1st Shift` (replaces those CSVs). `RESEND.csv` / `UNMATCHED.csv` land there. Production later: nth `--run` of the day = nth shift.

**Self-check:** `python "Order Grouping Sorter/scripts/test_grouping.py"`, `python "Order Grouping Sorter/scripts/test_catalog_cache.py"`, and `python scripts/test_taxonomy_picklist.py`

**Not built yet:** leftover floor numbers for stickers / mugs / Gildan / packs / plain / Fawad Prime FOTL. `SHIFT_PER_RUN` (nth `--run` of the day = nth shift) waits for production. Priority field 6: today first, then prime first, then as files are made (more ranking later).

**Shared already on this warehouse:** `shared.paths` sorter helpers; `shared.shipstation.parse_stores_payload` + `list_stores`. CL index accepts Areeb spaced headers via `rename_legacy_headers` (`python "Order Grouping Sorter/scripts/test_cl_legacy_headers.py"`). Live file remains the NocoDB export `Custom_Label_Database.csv`.
