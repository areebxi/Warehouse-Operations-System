"""
File loading utilities for loading color bars, size reference, and print-size overrides.
"""

import os
import re
from typing import Optional, Tuple, Set, List, Dict

import pandas as pd
from PIL import Image

# SKU Contain token -> (width_mm, height_mm); either dim may be None when blank in sheet
PrintSizeOverrides = Dict[str, Tuple[Optional[float], Optional[float]]]

_SIZE_REFERENCE_COLUMN_ALIASES = {
    "Number of Designs": "Number of Positions",
    "SKU Value": "Merge",
    "Suffix": "Position",
}


def _resolve_project_root_from_module() -> str:
    """Resolve project root from scripts/src/io module location."""
    io_dir = os.path.dirname(os.path.abspath(__file__))          # .../scripts/src/io
    src_dir = os.path.dirname(io_dir)                            # .../scripts/src
    scripts_dir = os.path.dirname(src_dir)                       # .../scripts
    project_root = os.path.dirname(scripts_dir)                  # project root
    return project_root


def _warehouse_queue_paths():
    import sys
    from pathlib import Path

    app_root = Path(_resolve_project_root_from_module())
    warehouse = app_root.parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    return wh


def load_color_bar_from_app_dir(app_dir: Optional[str] = None) -> Tuple[Optional[Image.Image], Optional[str]]:
    """Auto-load Color Bar file from Data/Queue (or legacy app dirs)."""
    try:
        wh = _warehouse_queue_paths()
        color_bar_names = ["Color Bar.png", "ColorBar.png", "color_bar.png", "colorbar.png"]
        search_dirs = [str(wh.queue_data_dir())]
        if app_dir is None:
            app_dir = _resolve_project_root_from_module()
        search_dirs.extend([os.path.join(app_dir, "config"), app_dir])

        for search_dir in search_dirs:
            for name in color_bar_names:
                file_path = os.path.join(search_dir, name)
                if not os.path.exists(file_path):
                    continue
                try:
                    color_bar_image = Image.open(file_path)
                    print(f"Color Bar loaded from: {file_path}")
                    return color_bar_image, file_path
                except Exception as e:
                    print(f"Error loading Color Bar from {file_path}: {e}")
                    continue
    except Exception as e:
        print(f"Error loading Color Bar from app directory: {e}")

    return None, None


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


def _parse_optional_mm(value: object) -> Optional[float]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if not text or text.lower() in ("nan", "none"):
        return None
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _parse_print_size_overrides(override_df: Optional[pd.DataFrame]) -> PrintSizeOverrides:
    """Parse Override Print Size (or legacy pocket ID) sheet into a contain->dims map."""
    overrides: PrintSizeOverrides = {}
    if override_df is None or len(override_df.columns) == 0:
        return overrides

    columns = {str(col).strip(): col for col in override_df.columns}
    contain_col = None
    for name in ("SKU Contain", "Logo/Design ID", "Pocket Design IDs"):
        if name in columns:
            contain_col = columns[name]
            break
    if contain_col is None:
        contain_col = override_df.columns[0]

    width_col = columns.get("Width")
    height_col = columns.get("Height")

    for _, row in override_df.iterrows():
        raw = row.get(contain_col)
        if pd.isna(raw):
            continue
        token = str(raw).strip()
        if not token:
            continue
        width_mm = _parse_optional_mm(row.get(width_col)) if width_col is not None else None
        height_mm = _parse_optional_mm(row.get(height_col)) if height_col is not None else None
        overrides[token] = (width_mm, height_mm)

    return overrides


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


def load_print_size_overrides(app_dir: Optional[str] = None) -> PrintSizeOverrides:
    """Auto-load Override Print Size rows as SKU Contain -> (width_mm, height_mm)."""
    try:
        config_workbook_path, _, override_df, _, sheet_info = _load_configuration_workbook_sheets(app_dir)

        if not os.path.exists(config_workbook_path or ""):
            print(f"Configuration Workbook.xlsx not found at: {config_workbook_path}")
            print("  Continuing without print size overrides")
            return {}

        if override_df is None:
            print(f"Warning: Override Print Size sheet missing: {config_workbook_path}")
            return {}

        overrides = _parse_print_size_overrides(override_df)
        print(f"Override Print Size loaded from: {config_workbook_path} ({sheet_info})")
        print(f"  Found {len(overrides)} SKU Contain entries")
        return overrides
    except Exception as e:
        print(f"Error loading Override Print Size from app directory: {e}")
        return {}


def load_pocket_design_ids_database(app_dir: Optional[str] = None) -> Set[str]:
    """Legacy set API: return Override Print Size SKU Contain tokens only."""
    try:
        return set(load_print_size_overrides(app_dir).keys())
    except Exception as e:
        print(f"Error loading Override Print Size from app directory: {e}")
        return set()


def load_configuration_workbook(
    app_dir: Optional[str] = None,
) -> Tuple[Optional[pd.DataFrame], Optional[str], PrintSizeOverrides]:
    """
    Load Size Reference + Override Print Size from Configuration Workbook in one open.

    Returns:
        (size_reference_df, workbook_path, print_size_overrides)
    """
    try:
        config_workbook_path, size_df, override_df, size_sheet_info, override_sheet_info = (
            _load_configuration_workbook_sheets(app_dir)
        )

        if size_df is None:
            print(f"Configuration Workbook.xlsx not found at: {config_workbook_path}")
            print("  Continuing without size reference (you can load it manually)")
            return None, None, {}

        df = _prepare_size_reference_df(size_df)
        print(f"Size Reference loaded from: {config_workbook_path} ({size_sheet_info})")
        print(f"  Found {len(df)} entries")

        overrides = _parse_print_size_overrides(override_df)
        if overrides:
            print(
                f"Override Print Size loaded from: {config_workbook_path} ({override_sheet_info})"
            )
            print(f"  Found {len(overrides)} SKU Contain entries")
        else:
            print(f"Warning: Override Print Size sheet missing/empty: {config_workbook_path}")

        return df, config_workbook_path, overrides
    except Exception as e:
        print(f"Error loading Configuration Workbook: {e}")
        return None, None, {}
