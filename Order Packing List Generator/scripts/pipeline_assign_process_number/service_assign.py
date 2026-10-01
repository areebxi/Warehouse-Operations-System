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
