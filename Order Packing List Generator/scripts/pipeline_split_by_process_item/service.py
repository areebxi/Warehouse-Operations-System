import sys
from datetime import date
from functools import partial
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.runtime_api import load_position_code_to_draw
from scripts.pipeline_generate_packing_list_pdf.runtime_config import DEFAULT_POSITION_CODE

from scripts.pipeline_runtime.order_number_csv import (
    coerce_order_number_columns,
    read_csv_with_order_numbers,
)

from .common import (
    _normalize_key,
    _position_after_merge,
    _reorder_columns_for_output,
    pin_batch_shift,
    sanitize_filename,
)
from .config import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WORKBOOK,
    REQUIRED_COLUMNS,
)
from .grouping import _expand_df_by_quantity, _sort_and_assign_merge_first
from .size_sequence import load_sequence_by_size


def _emit(msg: str, log: Optional[Callable[[str], None]], *, err: bool = False) -> None:
    if log:
        log(msg)
    elif err:
        print(msg, file=sys.stderr)
    else:
        print(msg)


def run(
    step5_csv_path: Path,
    output_dir: Path,
    workbook_path: Path | None,
    run_date: date | None = None,
    use_simple_process_format: bool = False,
    use_fixed_numeric_process: bool = False,
    fixed_process_number: str | None = None,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    df = read_csv_with_order_numbers(step5_csv_path)
    _emit(f"Step 6 (split by process): read {len(df)} rows from {step5_csv_path.name}", log)
    new_cols = []
    for c in df.columns:
        c2 = str(c).strip().lstrip("\ufeff")
        if _normalize_key(c2) == "order number" and c2 != "Order Number":
            c2 = "Order Number"
        new_cols.append(c2)
    df.columns = new_cols
    df = coerce_order_number_columns(df)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Step-5 CSV is missing required column(s): {', '.join(missing)}")

    df["_orig_idx"] = range(len(df))
    df = _expand_df_by_quantity(df)

    size_to_rank = None
    position_code_to_draw: dict[str, str] = {}
    if workbook_path is not None:
        size_to_rank = load_sequence_by_size(workbook_path)
        try:
            position_code_to_draw = load_position_code_to_draw(workbook_path)
        except Exception:
            position_code_to_draw = {}
    if size_to_rank is None:
        _emit(
            "Warning: Size sequence not loaded (workbook missing or no 'Sequence by Size' column in Process Info Sheet). Rows will not be sorted by size.",
            log,
            err=True,
        )
    else:
        _emit(
            f"Sorting by size using {len(size_to_rank)} sizes from 'Sequence by Size'.",
            log,
            err=True,
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    pin = df["Process and Item Number"].fillna("").astype(str).str.strip()
    df_grouped = df.assign(_pin_key=pin)
    groups: list[tuple[str, pd.DataFrame]] = []
    for key, group in df_grouped.groupby("_pin_key", sort=False):
        groups.append((str(key), group.drop(columns=["_pin_key"])))

    # Sorter filename is the batch name. Never the Workbook Process Number Tracker.
    # Visible base + file stem: B1-S1 only (not B1-S1-PLAIN-2-SUPPLY ON DEMAND-R-9).
    # Display PIN: B100-S1-1 Item 1 (batch+shift + process number + item).
    # run_date / use_simple_process_format / use_fixed_numeric_process kept on the
    # signature for callers; tracker path is gone.

    written = 0
    for base, group in groups:
        process_name = sanitize_filename(pin_batch_shift(base) if base else "")
        group_sorted = _sort_and_assign_merge_first(
            group,
            size_to_rank,
            sequence_number=None,
            use_simple_process_format=True,
            use_fixed_numeric_process=False,
            fixed_process_number=fixed_process_number,
        )
        if (
            "Position" in group_sorted.columns
            and "Logo/Design Image" in group_sorted.columns
            and "Item SKU" in group_sorted.columns
        ):
            group_sorted = group_sorted.copy()
            position_merge = partial(
                _position_after_merge,
                position_code_to_draw=position_code_to_draw or None,
                default_position_code=DEFAULT_POSITION_CODE,
            )
            group_sorted["Position"] = group_sorted.apply(position_merge, axis=1)
        path = output_dir / f"{process_name}.csv"
        group_sorted = group_sorted.drop(columns=["_orig_idx"], errors="ignore")
        group_sorted = _reorder_columns_for_output(group_sorted)
        group_sorted.to_csv(path, index=False, encoding="utf-8")
        written += 1

    if log and written:
        proc_names = sorted({sanitize_filename(base if base else "") for base, _ in groups})
        for n in proc_names[:35]:
            _emit(f"  {n}.csv", log)
        if len(proc_names) > 35:
            _emit(f"  ... and {len(proc_names) - 35} more process file(s)", log)

    _emit(f"Split into {written} process CSV file(s) under {output_dir.resolve()}", log)


__all__ = ["run", "DEFAULT_OUTPUT_DIR", "DEFAULT_WORKBOOK"]

