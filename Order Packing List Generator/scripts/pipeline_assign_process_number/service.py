from datetime import date
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers

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


def _emit(msg: str, log: Optional[Callable[[str], None]]) -> None:
    if log:
        log(msg)
    else:
        print(msg)


def _log_step5_process_assign_summary(df: pd.DataFrame, log: Optional[Callable[[str], None]]) -> None:
    if not log or "Process and Item Number" not in df.columns:
        return
    col = df["Process and Item Number"].fillna("").astype(str).str.strip()
    n_blank = int((col == "").sum())
    n_filled = len(df) - n_blank
    log(
        f"  Step 5 assign: Process and Item Number non-blank on {n_filled}/{len(df)} row(s); "
        f"blank on {n_blank}."
    )
    nonblank = col[col.ne("")]
    if nonblank.empty:
        return
    vc = nonblank.value_counts().head(30)
    log(
        "  Step 5 assign: top Process and Item Number values (up to 30): "
        + "; ".join(f"{k} ({v})" for k, v in vc.items())
    )
    if "Gender Apparel" in df.columns and n_blank:
        blank_mask = col == ""
        genders = (
            df.loc[blank_mask, "Gender Apparel"].fillna("").astype(str).str.strip().value_counts().head(10)
        )
        if not genders.empty:
            log(
                "  Step 5 assign: Gender Apparel among blank process rows (top 10): "
                + "; ".join(f"{repr(g)} ({c})" for g, c in genders.items())
            )


def assign_process_numbers(
    df: pd.DataFrame,
    gender_to_start: dict[str, str],
    shift_code: str,
    dispatch_date: date | None = None,
    logo_id_to_order_count: dict[str, int] | None = None,
    logo_id_threshold: int = 5,
    fixed_fallback: str | None = None,
    design_id_to_process_number: dict[str, str] | None = None,
    logo_id_full_logo_orders: set[tuple[str, str]] | None = None,
    logo_id_fallback_when_not_in_tracker: bool = True,
) -> pd.DataFrame:
    """Fill 'Process and Item Number' for each row. When logo_id_to_order_count is provided and
    a row's Logo ID has count >= logo_id_threshold (units per Logo ID from full-logo orders),
    and the row's order is a full-logo order for that Logo ID (logo_id_full_logo_orders),
    use Design ID Process Tracker lookup when design_id_to_process_number is provided; else Logo ID.
    When design_id_to_process_number is provided but the Logo ID is not listed, fall back to Logo ID
    only if logo_id_fallback_when_not_in_tracker is True; otherwise use 6-part / fixed assignment.
    """
    today = dispatch_date or date.today()
    process_numbers = []
    for _, row in df.iterrows():
        logo_id = _normalize(row.get("Logo ID", "")) if "Logo ID" in df.columns else ""
        logo_id_key = _normalize_key(logo_id) if logo_id else ""
        order_key = _normalize_key(str(row.get("Order Number", ""))) if "Order Number" in df.columns else ""
        over_threshold = (
            logo_id_to_order_count is not None
            and logo_id_key
            and logo_id_to_order_count.get(logo_id_key, 0) >= logo_id_threshold
        )
        in_full_logo_order = (
            logo_id_full_logo_orders is not None
            and order_key
            and logo_id_key
            and (order_key, logo_id_key) in logo_id_full_logo_orders
        )
        use_logo_id = over_threshold and (logo_id_full_logo_orders is None or in_full_logo_order)
        if use_logo_id:
            if design_id_to_process_number is not None:
                mapped = design_id_to_process_number.get(logo_id_key)
                if mapped:
                    process_numbers.append(mapped)
                    continue
                if logo_id_fallback_when_not_in_tracker:
                    process_numbers.append(logo_id)
                    continue
            else:
                process_numbers.append(logo_id)
                continue
        if fixed_fallback:
            process_numbers.append(fixed_fallback)
            continue
        gender = _normalize_key(row.get("Gender Apparel", ""))
        start = gender_to_start.get(gender, "") if gender else ""
        if not start:
            process_numbers.append("")
            continue
        prime_code = "P" if _prime_is_yes(row.get("Prime")) else "N"
        customise_code = "C" if _customise_is_yes(row.get("Customise")) else "N"
        ship_by_date = _parse_ship_by(row.get("Ship By"))
        dispatch_code = "D" if (ship_by_date and ship_by_date == today) else "D1"
        pos_code = _normalize(row.get("Position Code", ""))
        if not pos_code:
            pos_code = POSITION_FALLBACK
        parts = [str(start), shift_code, prime_code, customise_code, dispatch_code, pos_code]
        process_numbers.append("".join(parts))
    out = df.copy()
    out["Process and Item Number"] = process_numbers
    return out


def _token_from_step4_stem(stem: str) -> str:
    """Derive output token from step-4 filename stem."""
    if stem.startswith(PREFIX_STEP4):
        return stem[len(PREFIX_STEP4) :]
    return stem


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

    fixed = (fixed_process_number or "").strip()
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
        fixed_process_number,
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

