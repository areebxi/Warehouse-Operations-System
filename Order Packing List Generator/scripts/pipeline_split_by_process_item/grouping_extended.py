import pandas as pd

from .common import _normalize_key, _normalize_numeric_process_base

def sort_group_by_size(group: pd.DataFrame, size_to_rank: dict[str, int] | None) -> pd.DataFrame:
    if size_to_rank is None or "Size" not in group.columns:
        return group
    max_rank = max(size_to_rank.values(), default=0) + 1

    def rank_for_row(row) -> int:
        key = _normalize_key(row.get("Size", ""))
        return size_to_rank.get(key, max_rank)

    order = group.apply(rank_for_row, axis=1)
    group_sorted = group.copy()
    group_sorted["_size_rank"] = order
    group_sorted["_orig_idx"] = group_sorted.index
    sort_cols = ["_size_rank", "_orig_idx"]
    drop_cols = ["_size_rank", "_orig_idx"]

    if "Order Number" in group_sorted.columns:
        order_counts = group_sorted["Order Number"].value_counts(dropna=False)
        multi_row = order_counts.index[order_counts >= 2]
        single_row_rank = len(multi_row)

        def _order_key(x):
            c = order_counts[x]
            return (-c, str(x) if pd.notna(x) else "")

        order_to_rank = {}
        for i, on in enumerate(sorted(multi_row, key=_order_key)):
            order_to_rank[on] = i
        for on in order_counts.index[order_counts < 2]:
            order_to_rank[on] = single_row_rank

        group_sorted["_order_rank"] = group_sorted["Order Number"].map(order_to_rank)
        group_sorted["_order_rank"] = group_sorted["_order_rank"].fillna(single_row_rank)
        sort_cols.insert(0, "_order_rank")
        drop_cols.insert(0, "_order_rank")

    if "Colour" in group_sorted.columns:
        group_sorted["_colour_sort"] = group_sorted["Colour"].fillna("").astype(str).str.strip().str.lower()
        sort_cols.insert(sort_cols.index("_orig_idx"), "_colour_sort")
        drop_cols.insert(drop_cols.index("_orig_idx"), "_colour_sort")
    group_sorted = group_sorted.sort_values(sort_cols).drop(columns=drop_cols)
    return group_sorted.reset_index(drop=True)


def assign_extended_process_and_item_number(
    group: pd.DataFrame,
    sequence_number: int | None = None,
    use_simple_process_format: bool = False,
    use_fixed_numeric_process: bool = False,
    fixed_process_number: str | None = None,
) -> pd.DataFrame:
    if group.empty:
        return group

    base_series = group["Process and Item Number"].fillna("").astype(str).str.strip()
    base = base_series.iloc[0] if not base_series.empty else ""

    numeric_increment_base = _normalize_numeric_process_base(base)

    order_counts = group["Order Number"].value_counts(dropna=False) if "Order Number" in group.columns else None
    merge_orders: set | None = None
    if order_counts is not None:
        merge_orders = set(order_counts[order_counts >= 2].index)

    additional = 0
    item = 0
    prev_size = None
    prev_colour = None
    new_values: list[str] = []

    for _, row in group.iterrows():
        size_norm = _normalize_key(row.get("Size", "")) if "Size" in group.columns else ""
        colour_norm = _normalize_key(row.get("Colour", "")) if "Colour" in group.columns else ""
        order_number = row.get("Order Number") if "Order Number" in group.columns else None

        qty = 1
        if "Item Quantity" in group.columns:
            try:
                raw_qty = row.get("Item Quantity", 1)
                if pd.notna(raw_qty):
                    qty = int(raw_qty)
            except (TypeError, ValueError):
                qty = 1
            if qty < 1:
                qty = 1

        if additional == 0:
            additional = 1
            item = 1
        else:
            is_merge_order = bool(merge_orders is not None and order_number in merge_orders)
            is_multi_quantity = qty > 1
            is_merge_row = is_merge_order or is_multi_quantity

            if is_merge_row:
                item += 1
            else:
                if size_norm == prev_size and colour_norm == prev_colour:
                    item += 1
                else:
                    additional += 1
                    item = 1

        prev_size = size_norm
        prev_colour = colour_norm

        ext_display = f"{base}-{additional} {item}" if base else f"{additional} {item}"

        if numeric_increment_base is not None:
            display_base = int(numeric_increment_base) + (additional - 1)
            value = f"Process {display_base} Item-{item}"
        elif use_simple_process_format or (use_fixed_numeric_process and numeric_increment_base is None):
            value = f"Process {base}-{additional} Item-{item}" if base else f"Process {additional} Item-{item}"
        elif sequence_number is not None:
            process_num = f"{sequence_number}{additional}"
            value = f"Process {process_num} Item-{item} ({ext_display})"
        else:
            value = f"{base}-{additional}-{item}" if base else f"{additional}-{item}"

        new_values.append(value)

    updated = group.copy()
    updated["Process and Item Number"] = new_values
    return updated

