"""Size Reference sheet parse + Configuration Workbook sheet open."""

from __future__ import annotations

import os
import re
from typing import List, Optional, Tuple

import pandas as pd

from src.io.file_loaders_paths import _resolve_project_root_from_module, _warehouse_queue_paths

_SIZE_REFERENCE_COLUMN_ALIASES = {
    "Number of Designs": "Number of Positions",
    "SKU Value": "Merge",
    "Suffix": "Position",
}


def _parse_brackets_from_merge(merge_value: str) -> Tuple[str, List[str]]:
    """Parse base code + bracket codes from the `Merge` / `SKU Value` column string."""
    if pd.isna(merge_value):
        return "", []

    merge_str = str(merge_value).strip()
    first_bracket_pos = merge_str.find("(")
    if first_bracket_pos == -1:
        return merge_str, []

    base_code = merge_str[:first_bracket_pos].strip()
    bracket_pattern = r"\(([^)]+)\)"
    bracket_matches = re.findall(bracket_pattern, merge_str)
    bracket_codes = [code.strip() for code in bracket_matches if code.strip()]
    return base_code, bracket_codes


def _normalize_size_reference_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map WorkbookX headers onto the internal names used by lookup logic."""
    rename_map = {
        src: dst
        for src, dst in _SIZE_REFERENCE_COLUMN_ALIASES.items()
        if src in df.columns and dst not in df.columns
    }
    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def _prepare_size_reference_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize headers, parse Merge columns, and attach lookup indexes."""
    from src.core.size_lookup_index import attach_size_reference_index

    df = _normalize_size_reference_columns(df)

    if "Merge" in df.columns:
        parsed = df["Merge"].apply(
            lambda x: _parse_brackets_from_merge(x) if pd.notna(x) else ("", [])
        )
        df["Merge_clean"] = parsed.apply(lambda pair: pair[0])
        df["Merge_brackets"] = parsed.apply(lambda pair: pair[1])

    return attach_size_reference_index(df)


def _load_configuration_workbook_sheets(
    app_dir: Optional[str] = None,
) -> Tuple[Optional[str], Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[str], Optional[str]]:
    """
    Open Configuration Workbook once and return both sheets.

    Returns:
        (path, size_df, override_df, size_sheet_info, override_sheet_info)
    """
    if app_dir is None:
        app_dir = _resolve_project_root_from_module()

    wh = _warehouse_queue_paths()
    config_workbook_path = str(wh.queue_config_workbook_path())

    if not os.path.exists(config_workbook_path):
        return config_workbook_path, None, None, None, None

    xl = pd.ExcelFile(config_workbook_path)
    sheet_names = set(xl.sheet_names)

    size_sheet_info = "Size References" if "Size References" in sheet_names else None
    if "Override Print Size" in sheet_names:
        override_sheet_info = "Override Print Size"
    elif "Pocket Design IDs Database" in sheet_names:
        override_sheet_info = "Pocket Design IDs Database"
    else:
        override_sheet_info = None

    size_df = (
        pd.read_excel(xl, sheet_name="Size References")
        if size_sheet_info
        else pd.read_excel(xl, sheet_name=0)
    )
    if not size_sheet_info:
        size_sheet_info = "Sheet 1"

    if override_sheet_info:
        override_df = pd.read_excel(xl, sheet_name=override_sheet_info)
    elif len(xl.sheet_names) > 1:
        override_df = pd.read_excel(xl, sheet_name=1)
        override_sheet_info = "Sheet 2"
    else:
        override_df = None

    return config_workbook_path, size_df, override_df, size_sheet_info, override_sheet_info


def load_size_reference_from_app_dir(
    app_dir: Optional[str] = None,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Auto-load Size Reference from `config/Configuration Workbook.xlsx`."""
    try:
        config_workbook_path, size_df, _, sheet_info, _ = _load_configuration_workbook_sheets(app_dir)

        if size_df is None:
            print(f"Configuration Workbook.xlsx not found at: {config_workbook_path}")
            print("  Continuing without size reference (you can load it manually)")
            return None, None

        df = _prepare_size_reference_df(size_df)

        print(f"Size Reference loaded from: {config_workbook_path} ({sheet_info})")
        print(f"  Found {len(df)} entries")
        return df, config_workbook_path
    except Exception as e:
        print(f"Error loading Size Reference from app directory: {e}")
        return None, None
