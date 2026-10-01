from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from pipeline_runtime.runner_utils_paths import (
    ALL_ORDERS_PATH,
    _ensure_dir,
    _parse_process_and_item,
    _path_display,
)

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
