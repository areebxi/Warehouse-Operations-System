# Docs — Order Grouping Sorter

Living:

| File | What it is |
|------|------------|
| [`../../Order Grouping Sorter/AGENTS.md`](../../Order%20Grouping%20Sorter/AGENTS.md) | Domain handbook |
| [`HANDOFF.md`](HANDOFF.md) | Snapshot / continue |
| [`FINDINGS.md`](FINDINGS.md) | Locked facts from dry-runs |
| [`../../Order Grouping Sorter/order-grouping-locks.md`](../../Order%20Grouping%20Sorter/order-grouping-locks.md) | Grouping locks |
| [`../../Order Grouping Sorter/order-grouping-criteria.csv`](../../Order%20Grouping%20Sorter/order-grouping-criteria.csv) | CEO review table |
| [`../../Order Grouping Sorter/order-grouping-progress.xlsx`](../../Order%20Grouping%20Sorter/order-grouping-progress.xlsx) | Progress workbook |

Policy: parent `.cursor/rules/order-grouping-sorter/`.

```text
python "Order Grouping Sorter/scripts/run_sorter.py"
python "Order Grouping Sorter/scripts/run_sorter.py" --run-date 2026-09-11
python "Order Grouping Sorter/scripts/run_sorter.py" --run
python "Order Grouping Sorter/scripts/test_grouping.py"
python scripts/test_taxonomy_picklist.py
```
