# Order Grouping Sorter — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/order-grouping-sorter/`. Locks: `order-grouping-locks.md`. Details: `docs/`.
Current state: `docs/HANDOFF.md`, kept as present-tense state, not a log.

Live paths via `shared/paths.py`. A grouping **run** only **reads** CL + Plain Database + Packs. Sorter DB: `database/order-grouping-sorter/` — `taxonomy_picklists.csv` (Hashim #038), `fixed_batches.csv` (B80/B100/… criteria), `leftover_batches/{YYYY-MM-DD}.csv` (written each run for leftover B1/B2…), and `catalog_cache/` (Plain/Packs pickles). Chat “run the group sorter” → `--run` on current `awaiting_shipment` only (no catalog seed; still-awaiting orders are not skipped for an earlier shift). Locked 2026-10-14; catalog step removed 2026-10-20. Chat “add unmatched” runs `scripts/seed_catalog_misses.py` alone. If the shift was not named, ask and do not run yet (every chat and every new session).

## Live vs helpers

| Live | Other |
|------|--------|
| `scripts/run_sorter.py` | Dry-run by default; `--run` writes Packing Input |
| `scripts/tag_shift_orders.py` | Put `001-1st Shift` … `005-5th Shift` on Order #s in named CSVs (parallel addtag) |
| `scripts/seed_catalog_misses.py` | Chat **add unmatched** only. Not part of “run the group sorter” |
| `database/order-grouping-sorter/taxonomy_picklists.csv` | Closed Areeb category / product type / product style / department + PE subcategory |
| `database/order-grouping-sorter/fixed_batches.csv` | Fixed batch codes + match criteria (`B80` / `B100` / …) |
| `database/order-grouping-sorter/leftover_batches/{YYYY-MM-DD}.csv` | Leftover `B1`/`B2`… criteria for that run date (same columns as fixed; overwritten each sorter run) |
| `database/order-grouping-sorter/catalog_cache/` | Plain/Packs index pickles (auto; gitignored) |
| `database/shared/custom_label/Custom_Label_Database (Areeb).csv` | Finish + printed attributes (temporary; four Areeb columns filled). Other apps still use the live NocoDB CSV. |
| `database/shared/plain/Plain Database.csv` | Plain catalog |
| `database/shared/packs/Packs Database.csv` | Packs catalog |
| `config/ShipStation/.env` | Shared ShipStation |
| `Logs/` | Dry-run reports |
| Packing `Input/{DD-MM-YYYY}/{nth} Shift/` | Write on `--run`. Nth run of the day = nth shift (locked 2026-10-14). Replaces that shift’s CSVs only. `RESEND` / `UNMATCHED` land there. 3rd shift and later: overdue, blank, and the run-day ship-by, plus tag `1004- Personalised Design-Ready-` when ship-by is later (locked 2026-10-22). A later ship-by without that tag stays out |
| `order-grouping-locks.md` | Grouping lock log |
| `order-grouping-criteria.csv` | CEO review table |
| `order-grouping-progress.xlsx` | Progress workbook. Regenerate with `scripts/write_order_grouping_progress.py` |
| `fixed_batches.md` | Pointer to the live fixed-batches CSV |
| `leftover_batches.md` | Pointer to dated leftover-batches CSVs |

## How work is done

Fetch ShipStation `awaiting_shipment` (`shared.shipstation`, including `list_stores` for MAS Clothing → `fawad`) → skip `post-order-designs` → skip tag `00000-Warehouse OOS` → skip tag `1006- PERSONALISED ORDER Listing Error (DW)` → skip store `DTFOcean.co.uk WP` → `1014-ALL-RESEND` → blank ship-by → **today** → customised only with `1004- Personalised Design-Ready-` (else held) → write this run into the **next open shift** (1st `--run` of the day = `1st Shift`, 2nd = `2nd Shift`, …) → **3rd shift and later: overdue, blank, and the run-day ship-by, plus tag `1004- Personalised Design-Ready-` when ship-by is later** (a later ship-by without that tag stays in `awaiting_shipment`; locked 2026-10-22) → **fixed batches first** (`B80-{6 fields}.csv` / `B100-{6 fields}.csv` / …) → leftover `B1-{6 fields}.csv` / `B2-…` (skip reserved). Leftover mixes today+later only when eligible **orders** ≤ 300; above 300 leftover splits by date. Fixed batches are always one CSV per code in that shift.

SKU keys are **stricter** than `shared.cl_sku_match.resolve_label`: CL after first dash, or **whole SKU when there is no dash**; Plain till last dash or whole; Packs whole SKU. Do not import Packing internals. CSV columns (when writing) copy Packing current-view `CSV_FIELDNAMES`.

## Hard do-nots

- Do not write Packing Input unless supervisor **run** (CLI `--run`).
- Do not overwrite catalogs on a grouping run.
- Do not use universal 3-key `resolve_label` for grouping.
- Do not treat 1015 / 1016 / 1017 as resend.
- Do not split Packs on Item 1–10 Colour.
- Do not guess a required field; unmatched instead.

## Report changes

Dry-run: run date, mix yes/no (Hashim 300-order gate), process names with orders / lines / units, `RESEND`, `UNMATCHED` (reasons). Testing always reports `1st Shift`. Say clearly that Input was **not** written.

`--run`: same report plus paths of CSVs written to `1st Shift`.

## Structure & boundaries

- **Orchestration:** `scripts/run_sorter.py` (dry-run default; `--run` writes).
- **Domain:** `scripts/grouping.py` (façade) plus `grouping_*.py` modules (`models`, `finish`, `intake`, `slots`, `peel`, `garments`, `fixed`, `shift`, `parts`, `names`, `bins`, `io`, `report`); also `fixed_batches.py`, `leftover_batches.py`, `catalogs.py`, `catalog_cache.py`.
- **I/O:** Packing Input via `shared.paths.sorter_input_csv_path`; Logs; sorter DB under `database/order-grouping-sorter/`.
- **Legacy oversized:** none in production grouping path; `test_grouping.py` is a thin runner over `test_grouping_*.py` behaviour modules (see `../docs/ARCHITECTURE.md`).
- **Must not:** import Packing internals (CSV columns are copied, not imported); overwrite catalogs on a run; use universal 3-key `resolve_label` for grouping finish keys.
- Architecture: `.cursor/rules/global/architecture.mdc`.
