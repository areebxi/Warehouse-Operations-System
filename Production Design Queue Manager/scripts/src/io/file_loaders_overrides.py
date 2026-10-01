"""Override Print Size / pocket override loaders + Queue data-source bootstrap."""

from __future__ import annotations

import os
from typing import Dict, Optional, Set, Tuple

import pandas as pd

from src.io.file_loaders_paths import _warehouse_queue_paths
from src.io.file_loaders_size_ref import _load_configuration_workbook_sheets

# SKU Contain token -> (width_mm, height_mm); either dim may be None when blank in sheet
PrintSizeOverrides = Dict[str, Tuple[Optional[float], Optional[float]]]


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


def _load_override_sheet(workbook_path: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Read Override Print Size (or legacy Pocket sheet) from Configuration Workbook."""
    if not os.path.exists(workbook_path):
        return None, None
    xl = pd.ExcelFile(workbook_path)
    sheet_names = set(xl.sheet_names)
    if "Override Print Size" in sheet_names:
        return pd.read_excel(xl, sheet_name="Override Print Size"), "Override Print Size"
    if "Pocket Design IDs Database" in sheet_names:
        return pd.read_excel(xl, sheet_name="Pocket Design IDs Database"), "Pocket Design IDs Database"
    if len(xl.sheet_names) > 1:
        return pd.read_excel(xl, sheet_name=1), "Sheet 2"
    return None, None


def load_print_size_overrides_from_workbook(
    config_workbook_path: Optional[str] = None,
    app_dir: Optional[str] = None,
) -> Tuple[PrintSizeOverrides, Optional[str], Optional[str]]:
    """Load pocket / Override Print Size only (not Size References archive)."""
    wh = _warehouse_queue_paths()
    workbook_path = config_workbook_path or str(wh.queue_config_workbook_path())
    try:
        override_df, sheet_info = _load_override_sheet(workbook_path)
        if override_df is None:
            print(f"Pocket overrides: workbook not found -> {workbook_path}")
            return {}, workbook_path, None
        overrides = _parse_print_size_overrides(override_df)
        if overrides:
            print(
                f"Pocket overrides: Configuration Workbook -> {workbook_path} "
                f"({sheet_info}, {len(overrides)} SKU Contain entries)"
            )
        else:
            print(
                f"Pocket overrides: Override Print Size sheet missing/empty -> {workbook_path}"
            )
        return overrides, workbook_path, sheet_info
    except Exception as exc:
        print(f"Pocket overrides: error loading {workbook_path} -> {exc}")
        return {}, workbook_path, None


def load_queue_data_sources(
    cl_csv_path: Optional[str] = None,
    config_workbook_path: Optional[str] = None,
    app_dir: Optional[str] = None,
) -> Tuple[str, PrintSizeOverrides, str]:
    """
    Load live Queue data sources with clear startup logging.

    Print sizes come from CL CSV only. Configuration Workbook supplies pocket overrides.
    """
    from pathlib import Path

    from src.core.cl_print_sizes import clear_cl_size_cache, load_cl_size_table

    wh = _warehouse_queue_paths()
    cl_path = Path(cl_csv_path) if cl_csv_path else wh.cl_csv_path()
    wb_path = config_workbook_path or str(wh.queue_config_workbook_path())

    clear_cl_size_cache()
    try:
        df = load_cl_size_table(cl_path)
        print(f"Print sizes: Custom Label Database -> {cl_path} ({len(df):,} rows)")
    except FileNotFoundError:
        print(f"Print sizes: CL database not found -> {cl_path}")
        print("  Unmatched SKUs will export to Missing Size Reference")
    except ValueError as exc:
        print(f"Print sizes: CL database error -> {exc}")

    overrides, _, _ = load_print_size_overrides_from_workbook(wb_path, app_dir=app_dir)
    return str(cl_path), overrides, wb_path


def load_configuration_workbook(
    app_dir: Optional[str] = None,
    *,
    cl_csv_path: Optional[str] = None,
    config_workbook_path: Optional[str] = None,
) -> Tuple[Optional[pd.DataFrame], Optional[str], PrintSizeOverrides, str, str]:
    """
    Load Queue data sources. Size References sheet is not loaded (CL CSV is live).

    Returns:
        (None, workbook_path, print_size_overrides, cl_csv_path, config_workbook_path)
    """
    try:
        cl_path, overrides, wb_path = load_queue_data_sources(
            cl_csv_path=cl_csv_path,
            config_workbook_path=config_workbook_path,
            app_dir=app_dir,
        )
        return None, wb_path, overrides, cl_path, wb_path
    except Exception as e:
        print(f"Error loading Queue data sources: {e}")
        wh = _warehouse_queue_paths()
        return None, None, {}, str(wh.cl_csv_path()), str(wh.queue_config_workbook_path())
