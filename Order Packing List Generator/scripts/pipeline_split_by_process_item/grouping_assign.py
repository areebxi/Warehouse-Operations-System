import pandas as pd

from scripts.pipeline_runtime.order_number_csv import coerce_order_number_columns

from .common import _normalize, _normalize_key, _normalize_numeric_process_base, _order_number_column
from .duplicate_order_suffixes import assign_order_number_suffixes_for_customise
from .grouping_quantity import _get_qty


def _gender_apparel_rank(val: str) -> int:
    """Rank for sort: Men=0, Women=1, Kids=2; check 'women' before 'men'. Else 99."""
    val_lower = (val or "").strip().lower()
    if "women" in val_lower:
        return 1
    if "men" in val_lower:
        return 0
    if "kids" in val_lower:
        return 2
    return 99


def _sort_and_assign_merge_first(
    group: pd.DataFrame,
    size_to_rank: dict[str, int] | None,
    sequence_number: int | None = None,
    use_simple_process_format: bool = False,
    use_fixed_numeric_process: bool = False,
    fixed_process_number: str | None = None,
) -> pd.DataFrame:
    if group.empty:
        return group

    group = coerce_order_number_columns(group)

    on_col = _order_number_column(group)
    base_series = group["Process and Item Number"].fillna("").astype(str).str.strip()
    base = base_series.iloc[0] if not base_series.empty else ""

    numeric_increment_base = _normalize_numeric_process_base(base)

    order_counts = group[on_col].value_counts(dropna=False) if on_col is not None else None

    is_merge_list = []
    for _, row in group.iterrows():
        on = row.get(on_col) if on_col is not None else None
        order_count = order_counts.get(on, 0) if order_counts is not None else 0
        qty = _get_qty(row, group)
        is_merge_list.append(order_count >= 2 or qty > 1)

    group = group.copy()
    group["_is_merge"] = is_merge_list
    merge_df = group[group["_is_merge"]].drop(columns=["_is_merge"])
    non_merge_df = group[~group["_is_merge"]].drop(columns=["_is_merge"])

    if on_col is not None and on_col in merge_df.columns:
        merge_df = merge_df.copy()
        merge_df["Order Number (Base)"] = merge_df[on_col].apply(_normalize)
    if on_col is not None and on_col in non_merge_df.columns:
        non_merge_df = non_merge_df.copy()
        non_merge_df["Order Number (Base)"] = non_merge_df[on_col].apply(_normalize)

    out_parts = []
    max_rank = max(size_to_rank.values(), default=0) + 1 if size_to_rank else 0

    if not merge_df.empty:
        merge_df = merge_df.copy()
        if "Recipient Name" in merge_df.columns:
            merge_df["_recipient_sort"] = merge_df["Recipient Name"].fillna("").astype(str).str.strip().str.lower()
        else:
            merge_df["_recipient_sort"] = ""

        sort_cols = ["_recipient_sort"]
        if on_col is not None and on_col in merge_df.columns:
            sort_cols.append(on_col)
        if "_orig_idx" in merge_df.columns:
            sort_cols.append("_orig_idx")

        merge_df = merge_df.sort_values(sort_cols).drop(columns=["_recipient_sort"], errors="ignore")
        merge_df = merge_df.reset_index(drop=True)
        new_vals = []
        for i in range(len(merge_df)):
            item = i + 1
            ext_display = f"{base}-1 {item}" if base else f"1 {item}"
            if numeric_increment_base is not None:
                display_base = int(numeric_increment_base)
                val = f"Process {display_base} Item-{item}"
            elif use_simple_process_format or (use_fixed_numeric_process and numeric_increment_base is None):
                val = f"Process {base}-1 Item-{item}" if base else f"Process 1 Item-{item}"
            elif sequence_number is not None:
                val = f"Process {sequence_number}1 Item-{item} ({ext_display})"
            else:
                val = f"{base}-1-{item}" if base else f"1-{item}"
            new_vals.append(val)
        merge_df = merge_df.copy()
        merge_df["Process and Item Number"] = new_vals

        merge_df = assign_order_number_suffixes_for_customise(merge_df)
        out_parts.append(merge_df)

    if not non_merge_df.empty:
        start_additional = 2 if not merge_df.empty else 1
        non_merge_df = non_merge_df.copy()
        sort_cols = []
        if "Gender Apparel" in non_merge_df.columns:
            non_merge_df["_gender_rank"] = non_merge_df["Gender Apparel"].fillna("").astype(str).apply(_gender_apparel_rank)
            sort_cols.append("_gender_rank")
        if size_to_rank is not None and "Size" in non_merge_df.columns:
            non_merge_df["_size_rank"] = non_merge_df.apply(
                lambda r: size_to_rank.get(_normalize_key(r.get("Size", "")), max_rank),
                axis=1,
            )
            sort_cols.append("_size_rank")
        if "Colour" in non_merge_df.columns:
            non_merge_df["_colour_sort"] = non_merge_df["Colour"].fillna("").astype(str).str.strip().str.lower()
            sort_cols.append("_colour_sort")
        if "Recipient Name" in non_merge_df.columns:
            non_merge_df["_recipient_sort"] = non_merge_df["Recipient Name"].fillna("").astype(str).str.strip().str.lower()
            sort_cols.append("_recipient_sort")
        if sort_cols:
            non_merge_df = non_merge_df.sort_values(sort_cols).drop(columns=sort_cols, errors="ignore")
        non_merge_df = non_merge_df.reset_index(drop=True)

        additional = start_additional
        item = 1
        prev_gender = None
        prev_size = None
        prev_colour = None
        new_vals = []
        for _, row in non_merge_df.iterrows():
            gender_norm = _normalize_key(row.get("Gender Apparel", "")) if "Gender Apparel" in non_merge_df.columns else ""
            size_norm = _normalize_key(row.get("Size", "")) if "Size" in non_merge_df.columns else ""
            colour_norm = _normalize_key(row.get("Colour", "")) if "Colour" in non_merge_df.columns else ""
            if prev_gender is not None and (gender_norm != prev_gender or size_norm != prev_size or colour_norm != prev_colour):
                additional += 1
                item = 1
            prev_gender = gender_norm
            prev_size = size_norm
            prev_colour = colour_norm
            ext_display = f"{base}-{additional} {item}" if base else f"{additional} {item}"
            if numeric_increment_base is not None:
                display_base = int(numeric_increment_base) + (additional - 1)
                val = f"Process {display_base} Item-{item}"
            elif use_simple_process_format or (use_fixed_numeric_process and numeric_increment_base is None):
                val = f"Process {base}-{additional} Item-{item}" if base else f"Process {additional} Item-{item}"
            elif sequence_number is not None:
                val = f"Process {sequence_number}{additional} Item-{item} ({ext_display})"
            else:
                val = f"{base}-{additional}-{item}" if base else f"{additional}-{item}"
            new_vals.append(val)
            item += 1

        non_merge_df = non_merge_df.copy()
        non_merge_df["Process and Item Number"] = new_vals
        out_parts.append(non_merge_df)

    if not out_parts:
        return group.drop(columns=["_is_merge"], errors="ignore")

    return pd.concat(out_parts, ignore_index=True)



