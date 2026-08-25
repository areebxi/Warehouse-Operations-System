from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers

from .config import DEFAULT_POSITION_LABEL, PROCESS_INFO_SHEET, REQUIRED_COLUMNS, SCRIPT_NAME
from .io_process_info import load_logo_ids_to_positions, load_multiple_positions, load_process_info_pq
from .normalize import _is_blank, _normalize_logo_design_token
from .transform_logo_design import apply_x_xz_logo_design_image
from .transform_position_codes import (
    _token_from_step3_stem,
    apply_logo_id_positions,
    build_position_lookup,
    insert_position_code,
    split_matched_unmatched,
)


def _emit(msg: str, log: Optional[Callable[[str], None]]) -> None:
    if log:
        log(msg)
    else:
        print(msg)


def transform_step4_df(
    df: pd.DataFrame,
    *,
    logo_id_to_position: Optional[dict[str, str]] = None,
    default_code: str,
    position_to_code: dict[str, str],
    multiple_positions_df: Optional[pd.DataFrame] = None,
    log: Optional[Callable[[str], None]] = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    In-memory Step 4: normalize logo tokens, split matched/unmatched, assign
    positions / position codes, expand multi-position Logo/Design Image.
    Returns (matched, unmatched).
    """
    df = df.copy()
    if "Logo/Design Image" in df.columns:
        df["Logo/Design Image"] = df["Logo/Design Image"].map(_normalize_logo_design_token)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Step-3 data is missing required column(s): {', '.join(missing)}"
        )

    blank_count = int(df["Gender Apparel"].map(_is_blank).sum()) if "Gender Apparel" in df.columns else 0
    matched, unmatched = split_matched_unmatched(df)
    if log:
        sibling_pullins = max(0, len(unmatched) - blank_count)
        _emit(
            f"  Step 4: split by Gender Apparel — {len(matched)} matched, "
            f"{len(unmatched)} unmatched"
            + (f" ({sibling_pullins} merge-sibling pull-in(s))" if sibling_pullins else "")
            + ".",
            log,
        )

    if logo_id_to_position:
        matched = apply_logo_id_positions(matched, logo_id_to_position, log=log)
    elif log:
        _emit(
            "  Step 4: Logo IDs to Positions sheet not loaded (missing, empty, or no valid rows).",
            log,
        )

    if default_code == "":
        raise ValueError(
            f"Sheet '{PROCESS_INFO_SHEET}' must have a row with P = '{DEFAULT_POSITION_LABEL}'."
        )

    matched = insert_position_code(matched, default_code, position_to_code, log=log)

    if log:
        mp_n = (
            len(multiple_positions_df)
            if multiple_positions_df is not None and not multiple_positions_df.empty
            else 0
        )
        _emit(
            f"  Step 4: Multiple Positions sheet loaded ({mp_n} data row(s)) "
            "for Position Code -> logo suffix expansion.",
            log,
        )
    apply_x_xz_logo_design_image(matched, multiple_positions_df, log=log)
    return matched, unmatched


def run(
    step3_csv_path: Path,
    workbook_path: Path,
    output_dir: Path,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Read step-3 CSV, split by Gender Apparel, assign position codes to matched
    rows, write 4_unmatched_*.csv and 4_matched_*.csv.
    """
    df = read_csv_with_order_numbers(step3_csv_path)
    _emit(f"Step 4 (split position): read {len(df)} rows from {step3_csv_path.name}", log)

    logo_id_to_position = load_logo_ids_to_positions(workbook_path)
    pq_df = load_process_info_pq(workbook_path)
    default_code, position_to_code = build_position_lookup(pq_df)
    multiple_positions_df = load_multiple_positions(workbook_path)

    matched, unmatched = transform_step4_df(
        df,
        logo_id_to_position=logo_id_to_position,
        default_code=default_code,
        position_to_code=position_to_code,
        multiple_positions_df=multiple_positions_df,
        log=log,
    )

    token = _token_from_step3_stem(step3_csv_path.stem)
    unmatched_path = output_dir / f"unmatched_orders_{token}.csv"
    matched_path = output_dir / f"4_matched_{SCRIPT_NAME}_{token}.csv"

    output_dir.mkdir(parents=True, exist_ok=True)
    if len(unmatched) > 0:
        unmatched.to_csv(unmatched_path, index=False, encoding="utf-8")
    matched.to_csv(matched_path, index=False, encoding="utf-8")
    if len(unmatched) > 0:
        _emit(f"  Unmatched: {len(unmatched)} rows -> {unmatched_path.name}", log)
    else:
        _emit("  Unmatched: 0 rows (no file written).", log)
    _emit(f"  Matched: {len(matched)} rows -> {matched_path.name}", log)

