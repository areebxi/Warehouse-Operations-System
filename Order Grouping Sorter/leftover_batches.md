# Leftover batches

Each sorter run writes the leftover piles (`B1`, `B2`, …) for that **run date** into:

[`database/order-grouping-sorter/leftover_batches/{YYYY-MM-DD}.csv`](../database/order-grouping-sorter/leftover_batches/)

Same columns as [`fixed_batches.csv`](../database/order-grouping-sorter/fixed_batches.csv). One file per date; overwritten on the next sorter run for that date (dry-run and `--run`). Fixed-batch codes (`B80`, `B100`, …) are **not** listed — only Graph + 30-chain leftovers.

| Meta | Meaning |
|------|---------|
| `batch_code` | `B1` / `B2` / … assigned that run |
| `name` | `Leftover B{n}` |
| `notes` | Filename + order/line/unit counts |

Criteria cells are the actual Graph / peel slots for that pile (`x` = not peeled / don't care). `ship-by-date` is `today` / `future`, or `x` when the Hashim 300 gate mixes dates.

Path helper: `shared.paths.sorter_leftover_batches_path(run_date)`.  
Writer: `scripts/leftover_batches.py` (called from `run_sorter.py`).
