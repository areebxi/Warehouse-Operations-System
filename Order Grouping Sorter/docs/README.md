# Docs — Order Grouping Sorter

Living:

| File | What it is |
|------|------------|
| [`../AGENTS.md`](../AGENTS.md) | Domain handbook |
| [`HANDOFF.md`](HANDOFF.md) | Snapshot / continue |
| [`FINDINGS.md`](FINDINGS.md) | Locked facts from dry-runs |
| [`../order-grouping-locks.md`](../order-grouping-locks.md) | Grouping locks |
| [`../order-grouping-criteria.csv`](../order-grouping-criteria.csv) | CEO review table |
| [`../order-grouping-progress.xlsx`](../order-grouping-progress.xlsx) | Progress workbook |

Policy: parent `.cursor/rules/order-grouping-sorter/`.

```text
python "Order Grouping Sorter/scripts/run_sorter.py"
python "Order Grouping Sorter/scripts/run_sorter.py" --run-date 2026-09-11
python "Order Grouping Sorter/scripts/run_sorter.py" --run
python "Order Grouping Sorter/scripts/test_grouping.py"
python scripts/test_taxonomy_picklist.py
```
