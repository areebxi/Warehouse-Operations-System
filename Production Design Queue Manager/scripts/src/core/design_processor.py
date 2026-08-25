"""
Design processing utilities for standard and personalised processing modes.
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Union

from src.core.size_code_extractor import extract_size_code
from src.core.design_processing import (
    process_single_designs,
    process_personalised_designs,
)

__all__ = [
    "extract_size_code",
    "process_single_designs",
    "process_personalised_designs",
    "save_missing_size_reference_rows",
]


def save_missing_size_reference_rows(
    df: pd.DataFrame,
    missing_row_indices: List[int],
    source_file_path: Optional[str] = None,
    app_dir: Optional[Union[str, Path]] = None,
) -> Optional[str]:
    """Save rows with missing size references to a new DTF Des file."""
    if not missing_row_indices:
        return None

    try:
        if app_dir is None:
            src_dir = Path(__file__).parent
            app_dir = src_dir.parent

        missing_folder = Path(app_dir) / "Missing Size Reference"
        missing_folder.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        if source_file_path:
            stem = Path(source_file_path).stem
        else:
            stem = "DTF Des-Missing Size Reference"

        base_name = f"{stem} ({timestamp})"
        file_path = missing_folder / f"{base_name}.xlsx"
        suffix = 2
        while file_path.exists():
            file_path = missing_folder / f"{base_name} {suffix}.xlsx"
            suffix += 1

        missing_rows = df.iloc[missing_row_indices].copy()
        missing_rows.to_excel(file_path, index=False, engine="openpyxl")

        return str(file_path)
    except Exception as e:
        print(f"Error saving missing size reference rows: {e}")
        import traceback

        traceback.print_exc()
        return None
