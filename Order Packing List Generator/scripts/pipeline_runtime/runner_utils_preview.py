from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from pipeline_runtime.order_number_csv import read_csv_with_order_numbers

PIPELINE_PREVIEW_COLUMNS: tuple[str, ...] = (
    "Date",
    "Process",
    "Item Number",
    "Order Number",
    "Item SKU",
    "Item Name",
    "Customise",
    "Prime",
    "Gender Apparel",
    "Position",
    "Position Code",
    "Process and Item Number",
    "Logo ID",
    "Logo/Design Image",
    "Apparel Image",
    "Size",
    "Colour",
    "Item Quantity",
    "Ship By",
    "Recipient Name",
    "Notes From Buyer",
    "Tags",
)


def log_csv_preview(
    log: Optional[Callable[[str], None]],
    csv_path: Path,
    title: str,
    *,
    max_rows: int = 12,
    max_cols: int = 22,
    max_cell_chars: int = 100,
) -> None:
    """Log the first few rows of a CSV with a stable column order for broad session logs."""
    if not log or not csv_path.is_file():
        return
    try:
        df = read_csv_with_order_numbers(csv_path, encoding="utf-8", nrows=max_rows)
    except Exception as exc:
        log(f"  {title}: preview skipped ({exc})")
        return
    if df.empty:
        log(f"  {title}: (empty file) {csv_path.name}")
        return
    ordered: list[str] = []
    for c in PIPELINE_PREVIEW_COLUMNS:
        if c in df.columns and c not in ordered:
            ordered.append(c)
    for c in df.columns:
        if c not in ordered:
            ordered.append(c)
    cols = ordered[:max_cols]
    extra = len(df.columns) - len(cols)
    log(
        f"  {title}: {csv_path.name} — {len(df)} row(s) in preview (max {max_rows}), "
        f"{len(df.columns)} column(s); showing {len(cols)}"
        + (f" (+{extra} more column names omitted)" if extra > 0 else "")
    )
    log(f"    columns: {', '.join(cols)}")
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        parts: list[str] = []
        for c in cols:
            v = row.get(c, "")
            if pd.isna(v):
                s = ""
            else:
                s = str(v).replace("\n", " ").strip()
            if len(s) > max_cell_chars:
                s = s[: max_cell_chars - 3] + "..."
            parts.append(f"{c}={s}")
        log(f"    row {i}: " + " | ".join(parts))


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _parse_process_and_item(val):
    return parse_process_and_item_impl(val, safe_str=safe_str_impl, process_item_re=_PROCESS_ITEM_RE)


def _shift_subdir_name(shift_label: str) -> str:
    return (
        f"{shift_label} Shift"
        if shift_label and " Shift" not in shift_label
        else (shift_label or "Shift")
    )
