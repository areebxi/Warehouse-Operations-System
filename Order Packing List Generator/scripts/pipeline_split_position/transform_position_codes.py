import pandas as pd

from typing import Callable, Optional

from .config import DEFAULT_POSITION_LABEL, DEFAULT_POSITION_TEXT_TO_CODE, PREFIX_STEP3, PROCESS_INFO_SHEET
from .normalize import _is_blank, _normalize_label, _normalize_logo_id_key, _normalize_position_key


def build_position_lookup(pq_df: pd.DataFrame) -> tuple[str, dict[str, str]]:
    """
    Parse Process Info P/Q: build default code and position-text -> code lookup.
    Row where P = 'Default Position' (case-insensitive) -> default_code.
    Every other non-empty P -> normalized key (strip + lowercase) -> Q code.
    Duplicate P: last row wins. Returns (default_code, position_to_code).
    """
    default_code = ""
    position_to_code: dict[str, str] = {}
    for _, row in pq_df.iterrows():
        p_val = _normalize_label(row["P"])
        q_val = row["Q"]
        q_str = "" if pd.isna(q_val) else str(q_val).strip()
        if not p_val:
            continue
        if _normalize_position_key(p_val) == _normalize_position_key(DEFAULT_POSITION_LABEL):
            default_code = q_str
            continue
        key = _normalize_position_key(p_val)
        position_to_code[key] = q_str  # last row wins for duplicates
    if default_code == "" and not position_to_code:
        raise ValueError(
            f"Sheet '{PROCESS_INFO_SHEET}' must have a row with P = '{DEFAULT_POSITION_LABEL}' "
            "and optionally rows with P = actual position text (e.g. 'Front Top Center, Back Top Center')."
        )
    # Merge built-in mapping so standard position texts get X1–X4 even if sheet only has "Position Combination 1" etc.
    for key, code in DEFAULT_POSITION_TEXT_TO_CODE.items():
        position_to_code.setdefault(key, code)
    return default_code, position_to_code


def apply_logo_id_positions(
    matched_df: pd.DataFrame,
    logo_id_to_position: dict[str, str],
    log: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """
    Set Position from Logo IDs to Positions sheet when Logo ID matches.
    Logo ID sheet overrides any existing Position value.
    """
    if not logo_id_to_position or "Logo ID" not in matched_df.columns:
        return matched_df
    if "Position" not in matched_df.columns:
        return matched_df

    overridden = 0
    no_match = 0
    for idx, row in matched_df.iterrows():
        logo_key = _normalize_logo_id_key(row.get("Logo ID"))
        if not logo_key:
            continue
        position_val = logo_id_to_position.get(logo_key)
        if position_val:
            matched_df.at[idx, "Position"] = position_val
            overridden += 1
        else:
            no_match += 1

    if log:
        log(
            f"  Step 4 Logo IDs to Positions: {len(logo_id_to_position)} sheet row(s) loaded; "
            f"{overridden} matched row(s) Position set from Logo ID; "
            f"{no_match} row(s) with Logo ID but no sheet match."
        )
    return matched_df


def split_matched_unmatched(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split into matched and unmatched.

    Unmatched starts as blank Gender Apparel, then expands to whole merge groups
    (Order Number count >= 2 or Item Quantity > 1) so siblings never continue alone.
    """
    if "Gender Apparel" not in df.columns:
        raise ValueError("Step-3 CSV must contain column 'Gender Apparel'.")
    from scripts.pipeline_split_by_process_item.merge_group_mask import (
        expand_issue_mask_to_merge_groups,
    )

    blank = df["Gender Apparel"].apply(_is_blank)
    unmatched_mask = expand_issue_mask_to_merge_groups(df, blank)
    matched = df[~unmatched_mask].copy()
    unmatched = df[unmatched_mask].copy()
    return matched, unmatched


def insert_position_code(
    matched_df: pd.DataFrame,
    default_code: str,
    position_to_code: dict[str, str],
    log: Optional[Callable[[str], None]] = None,
) -> pd.DataFrame:
    """Insert 'Position Code' column immediately after 'Position'."""
    if "Position" not in matched_df.columns:
        raise ValueError("Step-3 CSV must contain column 'Position'.")
    pos_idx = matched_df.columns.get_loc("Position") + 1
    codes = []
    for _, row in matched_df.iterrows():
        pos = _normalize_label(row.get("Position"))
        if not pos:
            codes.append(default_code)
        else:
            key = _normalize_position_key(pos)
            codes.append(position_to_code.get(key, default_code))
    matched_df.insert(pos_idx, "Position Code", codes)
    if log:
        n = len(codes)
        used_default = sum(1 for c in codes if c == default_code)
        mapped = n - used_default
        log(
            f"  Step 4 Position Code: inserted after 'Position' for {n} matched row(s). "
            f"Mapped from Process Info Sheet position text -> {mapped} row(s); "
            f"used default code {default_code!r} where Position empty or unknown: {used_default} row(s). "
            f"({len(position_to_code)} distinct position keys in workbook lookup.)"
        )
    return matched_df


def _token_from_step3_stem(stem: str) -> str:
    """Derive output token from step-3 filename stem."""
    if stem.startswith(PREFIX_STEP3):
        return stem[len(PREFIX_STEP3) :]
    return stem

