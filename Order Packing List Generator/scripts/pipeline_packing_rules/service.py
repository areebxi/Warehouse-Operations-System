from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers

from .rules import apply_packing_rules, get_packing_rules


def _emit(msg: str, log: Optional[Callable[[str], None]]) -> None:
    if log:
        log(msg)


def apply_packing_rules_to_csv(
    step1_path: Path,
    *,
    token: str,
    log: Optional[Callable[[str], None]] = None,
) -> dict:
    """
    Load Step 1 CSV, apply packing rules, write audit snapshot and overwrite Step 1.

    Returns stats dict from apply_packing_rules (total_updated, rule_hits).
    """
    step1_path = Path(step1_path)
    rules = get_packing_rules()
    if not rules:
        return {"total_updated": 0, "rule_hits": []}

    df = read_csv_with_order_numbers(step1_path)
    df_out, stats = apply_packing_rules(df, rules, warn=log)

    output_root = step1_path.parent
    audit_path = output_root / f"1b_apply_rules_{token}.csv"
    df_out.to_csv(audit_path, index=False, encoding="utf-8")
    df_out.to_csv(step1_path, index=False, encoding="utf-8")

    total = stats.get("total_updated", 0)
    if total:
        _emit(f"Packing rules: updated Item Quantity on {total} row(s).", log)
    for hit in stats.get("rule_hits", []):
        if hit.get("count", 0):
            _emit(
                f"  rule {hit['index']} (sku={hit['sku']!r}): {hit['count']} row(s)",
                log,
            )

    return stats
