# Order Grouping Sorter — handbook

Domain handbook for the **Warehouse Automation System Engineer**. Parent map: `../AGENTS.md`. Policy: parent `.cursor/rules/order-grouping-sorter/`. Locks: `../order-grouping-locks.md`. Details: `docs/`.

Live paths via `shared/paths.py`. A grouping **run** only **reads** CL + Plain Database + Packs. Sorter DB: `database/order-grouping-sorter/` — `taxonomy_picklists.csv` (Hashim #038), `fixed_batches.csv` (B80/B100/… criteria), and `leftover_batches/{YYYY-MM-DD}.csv` (written each run for leftover B1/B2…).

## Live vs helpers

| Live | Other |
|------|--------|
| `scripts/run_sorter.py` | Dry-run by default; `--run` writes Packing Input |
| `database/order-grouping-sorter/taxonomy_picklists.csv` | Closed Areeb category / product type / product style / department + PE subcategory |
| `database/order-grouping-sorter/fixed_batches.csv` | Fixed batch codes + match criteria (`B80` / `B100` / …) |
| `database/order-grouping-sorter/leftover_batches/{YYYY-MM-DD}.csv` | Leftover `B1`/`B2`… criteria for that run date (same columns as fixed; overwritten each sorter run) |
| `database/shared/custom_label/Custom_Label_Database.csv` | Finish + printed attributes |
| `database/shared/plain/Plain Database.xlsx` | Plain catalog |
| `database/shared/packs/Packs Database.xlsx` | Packs catalog |
| `config/ShipStation/.env` | Shared ShipStation |
| `Logs/` | Dry-run reports |
| Packing `Input/{DD-MM-YYYY}/1st Shift/` | Write on `--run` while testing (replaces 1st Shift CSVs). `RESEND` / `UNMATCHED` land there. Production later: nth run = nth shift |
| `fixed_batches.md` | Pointer to the live fixed-batches CSV |
| `leftover_batches.md` | Pointer to dated leftover-batches CSVs |

## How work is done

Fetch ShipStation `awaiting_shipment` (`shared.shipstation`, including `list_stores` for MAS Clothing → `fawad`) → skip `post-order-designs` → skip store `DTFOcean.co.uk WP` → `1014-ALL-RESEND` → blank ship-by → **today** → customised only with `1004- Personalised Design-Ready-` (else held) → write all eligible into **`1st Shift`** (testing; production later uses nth run = nth shift) → **fixed batches first** (`B80-{6 fields}.csv` / `B100-{6 fields}.csv` / …) → leftover `B1-{6 fields}.csv` / `B2-…` (skip reserved). Mix today+later in one process only when eligible **orders** ≤ 300; above 300 split by date.

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
- **Domain:** `scripts/grouping.py` (façade) plus `grouping_*.py` modules (`models`, `finish`, `intake`, `slots`, `peel`, `garments`, `fixed`, `shift`, `parts`, `names`, `bins`, `io`, `report`); also `fixed_batches.py`, `leftover_batches.py`, `catalogs.py`.
- **I/O:** Packing Input via `shared.paths.sorter_input_csv_path`; Logs; sorter DB under `database/order-grouping-sorter/`.
- **Legacy oversized:** `test_grouping.py` (see `../docs/ARCHITECTURE.md`). Production `grouping.py` is split.
- **Must not:** import Packing internals (CSV columns are copied, not imported); overwrite catalogs on a run; use universal 3-key `resolve_label` for grouping finish keys.
- Architecture: `.cursor/rules/architecture.mdc`.
