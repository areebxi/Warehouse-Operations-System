from __future__ import annotations
from datetime import date
from pathlib import Path
from typing import Callable, Optional
import pandas as pd
from pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from .config import (
    LOGO_ID_REQUIRED_COLUMNS,
    POSITION_FALLBACK,
    PREFIX_STEP4,
    REQUIRED_COLUMNS,
    SCRIPT_NAME,
)
from .design_id_process_tracker import prepare_tracker_assign_kwargs
from .logo_logic import compute_logo_id_unit_counts
from .normalize import _customise_is_yes, _normalize, _normalize_key, _parse_ship_by, _prime_is_yes
from .workbook import build_gender_to_start_number, get_shift_code, load_process_info_sheet

def run(
    step4_csv_path: Path,
    shift_input: str,
    workbook_path: Path,
    output_dir: Path,
    dispatch_date: date | None = None,
    separate_by_logo_id: bool = False,
    logo_id_threshold: int = 5,
    fixed_process_number: str | None = None,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Read step-4 matched CSV, assign Process Number to each row, write output CSV.
    When only fixed_process_number is set: every row gets that value; Process Info Sheet and Logo ID are not used.
    When both separate_by_logo_id and fixed_process_number are set: above-threshold Logo IDs get Design ID lookup
    (or Logo ID); all other rows get fixed_process_number; Process Info Sheet is not loaded.
    When only separate_by_logo_id is set: above-threshold rows get Logo ID; others get 6-part number from workbook.
    """
    df = read_csv_with_order_numbers(step4_csv_path)
    _emit(f"Step 5 (assign process): read {len(df)} rows from {step4_csv_path.name}", log)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Step-4 CSV is missing required column(s): {', '.join(missing)}")

    from pipeline_split_by_process_item.common import pin_batch_shift

    fixed = pin_batch_shift((fixed_process_number or "").strip())
    if fixed and not separate_by_logo_id:
        df = df.copy()
        df["Process and Item Number"] = fixed
        token = _token_from_step4_stem(step4_csv_path.stem)
        output_path = output_dir / f"5_{SCRIPT_NAME}_{token}.csv"
        output_dir.mkdir(parents=True, exist_ok=True)
        _log_step5_process_assign_summary(df, log)
        df.to_csv(output_path, index=False, encoding="utf-8")
        _emit(f"Assigned fixed process number '{fixed}': {len(df)} rows -> {output_path.name}", log)
        return

    if separate_by_logo_id:
        logo_missing = [c for c in LOGO_ID_REQUIRED_COLUMNS if c not in df.columns]
        if logo_missing:
            raise ValueError(
                f"When separate_by_logo_id is True, step-4 CSV must have: {', '.join(LOGO_ID_REQUIRED_COLUMNS)}; missing: {', '.join(logo_missing)}"
            )

    logo_id_to_unit_count: dict[str, int] | None = None
    logo_id_full_logo_orders: set[tuple[str, str]] | None = None
    if separate_by_logo_id and "Logo ID" in df.columns and "Order Number" in df.columns:
        logo_id_to_unit_count, logo_id_full_logo_orders = compute_logo_id_unit_counts(df)

    tracker_kwargs = prepare_tracker_assign_kwargs(
        workbook_path,
        separate_by_logo_id,
        fixed or None,
        shift_input=shift_input,
        log=log,
    )

    both_set = bool(fixed and separate_by_logo_id)
    if both_set:
        df = assign_process_numbers(
            df,
            gender_to_start={},
            shift_code="",
            dispatch_date=dispatch_date,
            logo_id_to_order_count=logo_id_to_unit_count,
            logo_id_threshold=logo_id_threshold,
            fixed_fallback=fixed,
            logo_id_full_logo_orders=logo_id_full_logo_orders,
            **tracker_kwargs,
        )
    else:
        sheet = load_process_info_sheet(workbook_path)
        gender_to_start = build_gender_to_start_number(sheet)
        shift_code = get_shift_code(sheet, shift_input)
        if not shift_code:
            raise ValueError(
                f"Shift '{shift_input}' could not be matched to a code in Process Info Sheet column Shift (D) / Code (E)."
            )
        df = assign_process_numbers(
            df,
            gender_to_start,
            shift_code,
            dispatch_date=dispatch_date,
            logo_id_to_order_count=logo_id_to_unit_count,
            logo_id_threshold=logo_id_threshold,
            fixed_fallback=None,
            logo_id_full_logo_orders=logo_id_full_logo_orders,
            **tracker_kwargs,
        )

    token = _token_from_step4_stem(step4_csv_path.stem)
    output_path = output_dir / f"5_{SCRIPT_NAME}_{token}.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    _log_step5_process_assign_summary(df, log)
    df.to_csv(output_path, index=False, encoding="utf-8")
    _emit(f"Assigned process numbers: {len(df)} rows -> {output_path.name}", log)
def _token_from_step4_stem(stem: str) -> str:
    """Derive output token from step-4 filename stem."""
    if stem.startswith(PREFIX_STEP4):
        return stem[len(PREFIX_STEP4) :]
    return stem
