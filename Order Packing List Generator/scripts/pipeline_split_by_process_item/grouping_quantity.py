import pandas as pd


def _get_qty(row: pd.Series, group: pd.DataFrame) -> int:
    """Item Quantity for row; default 1 if missing or invalid."""
    if "Item Quantity" not in group.columns:
        return 1
    try:
        raw = row.get("Item Quantity", 1)
        if pd.isna(raw):
            return 1
        q = int(raw)
        return max(1, q)
    except (TypeError, ValueError):
        return 1


def _expand_df_by_quantity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand each row by Item Quantity: one row with qty=N becomes N rows with qty=1.
    So each unit gets its own row before grouping and extended code assignment (each unit
    then gets a distinct Process and Item Number). If Item Quantity is missing, leave df unchanged.
    """
    if "Item Quantity" not in df.columns or df.empty:
        return df
    expanded = []
    for _, row in df.iterrows():
        qty = _get_qty(row, df)
        for _ in range(qty):
            new_row = row.copy()
            # Keep as string so pandas StringDtype (infer_string / pandas 3) accepts it.
            new_row["Item Quantity"] = "1"
            expanded.append(new_row)
    out = pd.DataFrame(expanded).reset_index(drop=True)
    return out

