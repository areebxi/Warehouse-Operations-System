from datetime import date
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from scripts.pipeline_runtime.runner_utils import copy_dtf_des_to_shared_inbox

from .config import DTF_SKU_MAP_CSV, REQUIRED
from .helpers import _file_level_seq, load_dtf_sku_mapping
from .writers import _write_dtf_des, _write_orders_details, _write_picking


def run(
    csv_path: Path,
    output_dir: Path,
    dispatch_date: date,
    use_fixed_process_number: bool = False,
    use_fixed_numeric_process: bool = False,
    log: Optional[Callable[[str], None]] = None,
    *,
    date_dd_mm_yyyy: Optional[str] = None,
    shift_label: Optional[str] = None,
) -> None:
    df = read_csv_with_order_numbers(csv_path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required column(s): {', '.join(missing)}")

    dtf_sku_map = load_dtf_sku_mapping(DTF_SKU_MAP_CSV)

    process_base = csv_path.stem
    file_level_seq = _file_level_seq(df, process_base)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    picking_path = output_dir / f"{process_base}-Picking.xlsx"
    orders_path = output_dir / f"Orders Details-P{process_base}.xlsx"
    dtf_path = output_dir / f"DTF Des-P{process_base}.xlsx"

    if log:
        log(
            f"  Step 7 Excel: begin {csv_path.name} -> 3 workbooks in {output_dir.resolve()} "
            f"({len(df)} data row(s)); use_fixed_process_number={use_fixed_process_number}, "
            f"use_fixed_numeric_process={use_fixed_numeric_process}"
        )

    _write_picking(df, process_base, file_level_seq, dispatch_date, picking_path)
    if log and picking_path.is_file():
        log(f"  Step 7 Excel: Picking -> {picking_path.resolve()} ({picking_path.stat().st_size} bytes)")

    _write_orders_details(df, process_base, orders_path)
    if log and orders_path.is_file():
        log(f"  Step 7 Excel: Orders Details -> {orders_path.resolve()} ({orders_path.stat().st_size} bytes)")

    _write_dtf_des(
        df,
        dtf_path,
        use_fixed_process_number=use_fixed_process_number,
        use_fixed_numeric_process=use_fixed_numeric_process,
        dtf_sku_map=dtf_sku_map,
    )
    if log and dtf_path.is_file():
        log(f"  Step 7 Excel: DTF Des -> {dtf_path.resolve()} ({dtf_path.stat().st_size} bytes)")

    if dtf_path.is_file() and date_dd_mm_yyyy and shift_label:
        inbox_path = copy_dtf_des_to_shared_inbox(
            dtf_path,
            date_dd_mm_yyyy=date_dd_mm_yyyy,
            shift_label=shift_label,
            log=log,
        )
        if log and inbox_path is not None:
            log(f"  Step 7 Excel: DTF Des shared inbox -> {inbox_path.resolve()}")

    if log:
        log(f"  Step 7 Excel: finished all three for process base {process_base!r}")
