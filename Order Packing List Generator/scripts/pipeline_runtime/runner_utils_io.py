from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from pipeline_runtime.runner_utils_paths import (
    MISSING_LOGO_ROOT_DIR,
    PROJECT_ROOT,
    UNMATCHED_ROOT_DIR,
    _ensure_dir,
    _shift_subdir_name,
)

def copy_dtf_des_to_shared_inbox(
    dtf_path: Path,
    *,
    date_dd_mm_yyyy: str,
    shift_label: str,
    log: Optional[Callable[[str], None]] = None,
) -> Optional[Path]:
    """
    Copy a DTF Des workbook into Shared Inbox/DTF Des/{date}/{shift}/.
    Packing Output copy remains the source of truth for packing; inbox is the handoff.
    """
    import sys

    warehouse_root = PROJECT_ROOT.parent
    if str(warehouse_root) not in sys.path:
        sys.path.insert(0, str(warehouse_root))
    from shared.cl_sku_match import shared_inbox_dtf_des_root

    src = Path(dtf_path)
    if not src.is_file():
        return None
    date_part = (date_dd_mm_yyyy or "").replace("/", "-").strip()
    shift_part = _shift_subdir_name(shift_label)
    if not date_part:
        if log:
            log("  Shared inbox: skipped (empty date)")
        return None
    dest_dir = shared_inbox_dtf_des_root(PROJECT_ROOT) / date_part / shift_part
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / src.name
        shutil.copy2(src, dest)
        return dest
    except OSError as e:
        if log:
            log(f"  Shared inbox: copy failed ({e})")
        return None


def _copy_outputs_to_shift_dirs(
    output_root: Path,
    shift_label: str,
    pdf_copy_dir: Optional[str | Path],
    excel_copy_dir: Optional[str | Path],
    log=None,
    *,
    nest_pdf_under_shift: bool = True,
    nest_excel_under_shift: bool = True,
) -> list[str]:
    """Copy PDF/Excel outputs to optional destinations. Returns failure messages (empty if all ok)."""
    warnings: list[str] = []
    if not pdf_copy_dir and not excel_copy_dir:
        return warnings
    shift_part = _shift_subdir_name(shift_label)
    if excel_copy_dir:
        dest = Path(excel_copy_dir) / shift_part if nest_excel_under_shift else Path(excel_copy_dir)
        try:
            _ensure_dir(dest)
            xlsx_files = list(output_root.glob("*.xlsx"))
            for f in xlsx_files:
                shutil.copy2(f, dest / f.name)
            if log and xlsx_files:
                log(f"Copied {len(xlsx_files)} Excel file(s) to {dest}")
        except Exception as e:
            msg = f"Copy Excel to {dest} failed: {e}"
            warnings.append(msg)
            if log:
                log(msg)
    if pdf_copy_dir:
        dest = Path(pdf_copy_dir) / shift_part if nest_pdf_under_shift else Path(pdf_copy_dir)
        try:
            _ensure_dir(dest)
            pdf_files = list(output_root.glob("*.pdf"))
            for f in pdf_files:
                shutil.copy2(f, dest / f.name)
            if log and pdf_files:
                log(f"Copied {len(pdf_files)} PDF file(s) to {dest}")
        except Exception as e:
            msg = f"Copy PDF to {dest} failed: {e}"
            warnings.append(msg)
            if log:
                log(msg)
    return warnings

def _move_unmatched_to_root(
    unmatched_csv_path: Path,
    date_dd_mm_yyyy: str,
    shift_label: str,
) -> Optional[Path]:
    return _move_sideline_csv_to_root(
        unmatched_csv_path, date_dd_mm_yyyy, shift_label, UNMATCHED_ROOT_DIR
    )


def _move_missing_logo_to_root(
    missing_logo_csv_path: Path,
    date_dd_mm_yyyy: str,
    shift_label: str,
) -> Optional[Path]:
    return _move_sideline_csv_to_root(
        missing_logo_csv_path, date_dd_mm_yyyy, shift_label, MISSING_LOGO_ROOT_DIR
    )


def _move_sideline_csv_to_root(
    csv_path: Path,
    date_dd_mm_yyyy: str,
    shift_label: str,
    root_dir: Path,
) -> Optional[Path]:
    if not csv_path or not csv_path.is_file():
        return None
    try:
        normalized_date = datetime.strptime(date_dd_mm_yyyy, "%d-%m-%Y").strftime("%d-%m-%Y")
    except ValueError:
        normalized_date = date_dd_mm_yyyy
    shift_part = f"{shift_label} Shift" if shift_label and " Shift" not in shift_label else (shift_label or "Shift")
    dest_dir = root_dir / normalized_date / shift_part
    dest_file = dest_dir / csv_path.name
    try:
        _ensure_dir(dest_dir)
        shutil.move(str(csv_path), str(dest_file))
        return dest_file
    except Exception:
        return csv_path
