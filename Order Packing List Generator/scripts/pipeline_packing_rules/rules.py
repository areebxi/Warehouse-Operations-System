from __future__ import annotations

from typing import Any, Callable, Optional

import pandas as pd

from .config import PACKING_RULES

RULE_TYPE_SET_ITEM_QUANTITY = "set_item_quantity"


def _norm_str(val: Any) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


def _norm_lower(val: Any) -> str:
    return _norm_str(val).casefold()


def get_packing_rules() -> list[dict[str, Any]]:
    """Return validated packing rules from config."""
    rules = PACKING_RULES
    if not rules:
        return []
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ValueError(f"Packing rule at index {i} must be a dict")
        _validate_rule(rule, index=i)
    return list(rules)


def _validate_rule(rule: dict[str, Any], *, index: int) -> None:
    rule_type = rule.get("type", RULE_TYPE_SET_ITEM_QUANTITY)
    if rule_type != RULE_TYPE_SET_ITEM_QUANTITY:
        raise ValueError(
            f"Unsupported packing rule type {rule_type!r} at index {index}"
        )
    for key in ("sku", "item_name_contains", "set_item_quantity"):
        if key not in rule:
            raise ValueError(
                f"Packing rule at index {index} missing required field {key!r}"
            )
    try:
        qty = int(rule["set_item_quantity"])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Packing rule at index {index} has invalid set_item_quantity"
        ) from exc
    if qty < 1:
        raise ValueError(
            f"Packing rule at index {index} set_item_quantity must be >= 1"
        )


def row_matches_rule(row: pd.Series, rule: dict[str, Any]) -> bool:
    """Return True when row matches a set_item_quantity rule."""
    rule_type = rule.get("type", RULE_TYPE_SET_ITEM_QUANTITY)
    if rule_type != RULE_TYPE_SET_ITEM_QUANTITY:
        return False
    sku = _norm_lower(row.get("Item SKU", ""))
    name = _norm_lower(row.get("Item Name", ""))
    rule_sku = _norm_lower(rule.get("sku", ""))
    phrase = _norm_lower(rule.get("item_name_contains", ""))
    if not rule_sku or not phrase:
        return False
    return sku == rule_sku and phrase in name


def apply_packing_rules(
    df: pd.DataFrame,
    rules: list[dict[str, Any]],
    *,
    warn: Optional[Callable[[str], None]] = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Apply packing rules to a copy of df.

    Returns (updated_df, stats) where stats has keys:
      total_updated, rule_hits (list of dicts with index, sku, count).
    """
    if df.empty or not rules:
        return df, {"total_updated": 0, "rule_hits": []}

    required = ("Item SKU", "Item Name", "Item Quantity")
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        if warn:
            warn(
                "Packing rules: skipped — missing column(s): "
                + ", ".join(missing_cols)
            )
        return df, {"total_updated": 0, "rule_hits": []}

    out = df.copy()
    total_updated = 0
    rule_hits: list[dict[str, Any]] = []

    for index, rule in enumerate(rules):
        target_qty = int(rule["set_item_quantity"])
        count = 0
        for row_idx in out.index:
            if not row_matches_rule(out.loc[row_idx], rule):
                continue
            current = out.at[row_idx, "Item Quantity"]
            try:
                current_qty = int(current) if not pd.isna(current) else 0
            except (TypeError, ValueError):
                current_qty = 0
            if current_qty != target_qty:
                out.at[row_idx, "Item Quantity"] = target_qty
                total_updated += 1
            count += 1
        rule_hits.append(
            {
                "index": index,
                "sku": _norm_str(rule.get("sku", "")),
                "count": count,
            }
        )

    return out, {"total_updated": total_updated, "rule_hits": rule_hits}
