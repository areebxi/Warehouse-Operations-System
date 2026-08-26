from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_runtime.order_number_csv import (
    read_csv_with_order_numbers,
)
from scripts.pipeline_generate_packing_list_pdf.core_helpers import (
    parse_process_and_item_impl,
    safe_str_impl,
)

import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

UNMATCHED_ROOT_DIR = wh.packing_runtime_dir() / "Unmatched SKU Files"
MISSING_LOGO_ROOT_DIR = wh.packing_missing_logo_dir()
DATA_DIR = wh.packing_data_dir()
ALL_ORDERS_PATH = wh.packing_all_orders_path()
_PROCESS_ITEM_RE = re.compile(r"^Process\s+(\S+)\s+Item-(\d+)")

# Characters not allowed in Windows filenames
_FILENAME_UNSAFE = re.compile(r'[<>:"/\\|?*]')


def _sanitize_process_for_filename(name: str) -> str:
    """Return a safe filename segment (no path/Windows-unsafe chars)."""
    if not name:
        return "process"
    return _FILENAME_UNSAFE.sub("_", name.strip()).strip("_") or "process"


# Preferred column order for pipeline CSV previews (only columns present in the file are shown).
PIPELINE_PREVIEW_COLUMNS: tuple[str, ...] = (
    "Date",
    "Process",
    "Item Number",
    "Order Number",
    "Item SKU",
    "Item Name",
    "Customise",
    "Prime",
    "Gender Apparel",
    "Position",
    "Position Code",
    "Process and Item Number",
    "Logo ID",
    "Logo/Design Image",
    "Apparel Image",
    "Size",
    "Colour",
    "Item Quantity",
    "Ship By",
    "Recipient Name",
    "Tags",
)


def log_csv_preview(
    log: Optional[Callable[[str], None]],
    csv_path: Path,
    title: str,
    *,
    max_rows: int = 12,
    max_cols: int = 22,
    max_cell_chars: int = 100,
) -> None:
    """Log the first few rows of a CSV with a stable column order for broad session logs."""
    if not log or not csv_path.is_file():
        return
    try:
        df = read_csv_with_order_numbers(csv_path, encoding="utf-8", nrows=max_rows)
    except Exception as exc:
        log(f"  {title}: preview skipped ({exc})")
        return
    if df.empty:
        log(f"  {title}: (empty file) {csv_path.name}")
        return
    ordered: list[str] = []
    for c in PIPELINE_PREVIEW_COLUMNS:
        if c in df.columns and c not in ordered:
            ordered.append(c)
    for c in df.columns:
        if c not in ordered:
            ordered.append(c)
    cols = ordered[:max_cols]
    extra = len(df.columns) - len(cols)
    log(
        f"  {title}: {csv_path.name} — {len(df)} row(s) in preview (max {max_rows}), "
        f"{len(df.columns)} column(s); showing {len(cols)}"
        + (f" (+{extra} more column names omitted)" if extra > 0 else "")
    )
    log(f"    columns: {', '.join(cols)}")
    for i, (_, row) in enumerate(df.iterrows(), start=1):
        parts: list[str] = []
        for c in cols:
            v = row.get(c, "")
            if pd.isna(v):
                s = ""
            else:
                s = str(v).replace("\n", " ").strip()
            if len(s) > max_cell_chars:
                s = s[: max_cell_chars - 3] + "..."
            parts.append(f"{c}={s}")
        log(f"    row {i}: " + " | ".join(parts))


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _parse_process_and_item(val):
    return parse_process_and_item_impl(val, safe_str=safe_str_impl, process_item_re=_PROCESS_ITEM_RE)


def _shift_subdir_name(shift_label: str) -> str:
    return (
        f"{shift_label} Shift"
        if shift_label and " Shift" not in shift_label
        else (shift_label or "Shift")
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


def _update_all_orders_log(
    step6_csv_path: Path,
    date_dd_mm_yyyy: str,
    log: Optional[Callable[[str], None]] = None,
) -> None:
    if not step6_csv_path.exists():
        return
    df_new = read_csv_with_order_numbers(step6_csv_path)
    if df_new.empty or "Process and Item Number" not in df_new.columns:
        return

    process_ids: list[str] = []
    item_indices: list[str] = []
    keep_mask: list[bool] = []
    for val in df_new["Process and Item Number"]:
        proc, item = _parse_process_and_item(val)
        if proc and item:
            process_ids.append(str(proc))
            item_indices.append(str(item))
            keep_mask.append(True)
        else:
            process_ids.append("")
            item_indices.append("")
            keep_mask.append(False)

    if not any(keep_mask):
        return

    df_new = df_new.loc[keep_mask].copy()
    df_new.insert(0, "Date", date_dd_mm_yyyy)
    df_new.insert(1, "Process", process_ids)
    df_new.insert(2, "Item Number", item_indices)

    if ALL_ORDERS_PATH.exists():
        df_all = read_csv_with_order_numbers(ALL_ORDERS_PATH)
        bad_cols = [c for c in df_all.columns if "\t" in str(c)]
        if bad_cols:
            df_all = df_all.drop(columns=bad_cols)
    else:
        df_all = pd.DataFrame(columns=df_new.columns)

    key_cols = ["Date", "Process and Item Number"]
    combined = pd.concat([df_all, df_new], ignore_index=True)
    combined = combined.drop_duplicates(subset=key_cols, keep="last").reset_index(drop=True)

    _ensure_dir(ALL_ORDERS_PATH.parent)
    combined.to_csv(ALL_ORDERS_PATH, index=False, encoding="utf-8")
    if log:
        log(
            f"  All Orders log: merged {len(df_new)} row(s) from {step6_csv_path.name} into "
            f"{ALL_ORDERS_PATH.name} (total {len(combined)} rows after dedupe on Date + Process and Item Number)."
        )


def log_image_trace_block(
    log: Optional[Callable[[str], None]],
    body: str,
    *,
    line_prefix: str = "  ",
    max_lines: int = 250_000,
) -> None:
    """Write a multi-line image/PDF trace into the main pipeline log (one line per log call)."""
    if not log:
        return
    text = (body or "").strip()
    if not text:
        return
    lines = text.splitlines()
    omitted = 0
    if len(lines) > max_lines:
        omitted = len(lines) - max_lines
        lines = lines[:max_lines]
    for line in lines:
        log(line_prefix + line)
    if omitted:
        log(f"{line_prefix}... ({omitted} more line(s) omitted; max_lines={max_lines})")



def _path_display(p: Path | str | None) -> str:
    if p is None or (isinstance(p, str) and not p.strip()):
        return "(not set)"
    try:
        q = Path(p)
        return str(q.resolve())
    except OSError:
        return str(p)


def build_image_trace_log_file_body(
    *,
    step_label: str,
    run_timestamp: str,
    source_csv: Path,
    row_count: int,
    workbook_path: Path | None,
    output_pdf: Path | None,
    output_folder: Path | None,
    apparel_dir: Path | str | None,
    logo_custom_single_dir: Path | str | None,
    logo_custom_double_dir: Path | str | None,
    logo_normal_dir: Path | str | None,
    unique_apparel_stems: int,
    unique_logo_custom_stems: int,
    unique_logo_normal_stems: int,
    detail_text: str,
    apparel_found: int,
    apparel_total: int,
    logo_found: int,
    logo_total: int,
) -> str:
    """
    Build the Step 8 image-resolution section (context + per-row lines + summary).
    Intended to be appended to the main pipeline transcript log (no separate trace file).
    """
    lines: list[str] = [
        "=" * 72,
        "IMAGE RESOLUTION & ASSET LOOKUP TRACE",
        "(Embedded in the main pipeline log for this run.)",
        "=" * 72,
        f"Step / phase:     {step_label}",
        f"Timestamp:        {run_timestamp}",
        f"Process CSV:      {_path_display(source_csv)}",
        f"Rows in CSV:      {row_count}",
        f"Workbook:         {_path_display(workbook_path)}",
        f"PDF written:      {_path_display(output_pdf)}",
        f"Output folder:    {_path_display(output_folder)}",
        "",
        "Configured image directories (search roots):",
        f"  Apparel:              {_path_display(apparel_dir)}",
        f"  Logo custom (single): {_path_display(logo_custom_single_dir)}",
        f"  Logo custom (double): {_path_display(logo_custom_double_dir)}",
        f"  Logo normal:          {_path_display(logo_normal_dir)}",
        "",
        "Indexed filenames (unique stems discovered in those folders):",
        f"  Apparel stems:        {unique_apparel_stems}",
        f"  Logo custom stems:    {unique_logo_custom_stems}",
        f"  Logo normal stems:    {unique_logo_normal_stems}",
        "",
        "NOTE: Main pipeline detail logs: logs/<input_stem>_<DD-MM-YYYY_HH-MM-SS>.log (one file per input CSV per run).",
        "PDF drawing warnings (e.g. corrupt image files) may still appear only on the console (stderr).",
        "",
        "-" * 72,
        "Per-row lookups (same as GUI / session log image block)",
        "-" * 72,
        "",
        (detail_text or "").strip() or "(no apparel or logo lookup rows for this CSV)",
        "",
        "-" * 72,
        "Summary",
        "-" * 72,
        f"Apparel files resolved: {apparel_found} / {apparel_total}",
        f"Logo files resolved:   {logo_found} / {logo_total}",
        "=" * 72,
    ]
    return "\n".join(lines) + "\n"
