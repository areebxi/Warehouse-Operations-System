from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.core_helpers import parse_process_and_item_impl, safe_str_impl
from scripts.pipeline_runtime.pipeline_log import PipelineLog
from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from scripts.pipeline_runtime.runner import ALL_ORDERS_PATH, PROJECT_ROOT, _run_step6_style_outputs
import sys

_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

_PROCESS_ITEM_RE = re.compile(r"^Process\s+(\S+)\s+Item-(\d+)")

MISSING_DIR = wh.packing_missing_input_dir()
DEFAULT_MISSING_INPUT = MISSING_DIR / "Missing Input.csv"
CONFIG_DIR = wh.packing_config_dir()
MISSING_RUN_CONFIG = CONFIG_DIR / "missing_run_config.json"

MISSING_PDF_SUBDIRS = ("Missing Logo", "Missing Apparel")
DEFAULT_MISSING_TYPE = "Missing Logo"


def resolve_missing_pdf_copy_dir(
    base: str | Path | None,
    missing_type: str,
) -> Path | None:
    """Append Missing Logo / Missing Apparel under the PDF copy base (if set)."""
    raw = (str(base).strip() if base is not None else "")
    if not raw:
        return None
    kind = (missing_type or "").strip()
    if kind not in MISSING_PDF_SUBDIRS:
        raise ValueError(
            f"missing_type must be one of {MISSING_PDF_SUBDIRS}, got {missing_type!r}"
        )
    path = Path(raw)
    # Avoid nesting when the field already ends with either subtype folder.
    if path.name in MISSING_PDF_SUBDIRS:
        path = path.parent
    return path / kind


def _normalise_match_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    if text.endswith(".0"):
        whole, dot, frac = text.partition(".")
        if dot and frac == "0" and whole.lstrip("-").isdigit():
            return whole
    return text


def _prepare_missing_input_queries(df_q: pd.DataFrame, fallback_date: str = "") -> pd.DataFrame:
    """Build Date/Process/Item Number queries from step-6 output when those columns are absent."""
    if all(col in df_q.columns for col in ("Date", "Process", "Item Number")):
        return df_q
    if "Process and Item Number" not in df_q.columns:
        return df_q
    fallback_date = str(fallback_date or "").strip().replace("/", "-")
    if not fallback_date:
        return df_q
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for _, q in df_q.iterrows():
        proc, item = parse_process_and_item_impl(
            q.get("Process and Item Number", ""),
            safe_str=safe_str_impl,
            process_item_re=_PROCESS_ITEM_RE,
        )
        if not proc or not item:
            continue
        key = (fallback_date, proc, item)
        if key in seen:
            continue
        seen.add(key)
        rows.append({"Date": fallback_date, "Process": proc, "Item Number": item})
    return pd.DataFrame(rows) if rows else df_q


def _coerce_pipeline_log(log: Optional[Callable[[str], None]] | PipelineLog) -> Optional[PipelineLog]:
    if log is None:
        return None
    if isinstance(log, PipelineLog):
        return log
    return PipelineLog(log)


def _build_missing_run_df(
    all_orders_path: Path,
    missing_input_path: Path,
    *,
    fallback_date: str = "",
) -> pd.DataFrame:
    if not all_orders_path.exists():
        raise FileNotFoundError(f"All Orders log not found: {all_orders_path}")
    if not missing_input_path.exists():
        raise FileNotFoundError(f"Missing Input CSV not found: {missing_input_path}")

    df_all = read_csv_with_order_numbers(all_orders_path)
    df_q = read_csv_with_order_numbers(missing_input_path, encoding="utf-8")
    df_q = _prepare_missing_input_queries(df_q, fallback_date)
    if df_all.empty or df_q.empty:
        return pd.DataFrame()

    if "Date" in df_all.columns:
        df_all["Date"] = df_all["Date"].astype(str).str.strip().str.replace("/", "-", regex=False)
    if "Date" in df_q.columns:
        df_q["Date"] = df_q["Date"].astype(str).str.strip().str.replace("/", "-", regex=False)
    for frame in (df_all, df_q):
        for col in ("Process", "Item Number"):
            if col in frame.columns:
                frame[col] = frame[col].map(_normalise_match_value)

    for col in ("Date", "Process", "Item Number", "Order Number"):
        if col not in df_all.columns:
            raise ValueError(f"Missing required column '{col}' in All Orders log.")

    df_all["Order Number"] = df_all["Order Number"].map(_normalise_match_value)
    if "Order Number (Base)" not in df_all.columns:
        df_all["Order Number (Base)"] = df_all["Order Number"]
    else:
        df_all["Order Number (Base)"] = df_all["Order Number (Base)"].map(_normalise_match_value)
        df_all["Order Number (Base)"] = df_all["Order Number (Base)"].where(df_all["Order Number (Base)"].ne(""), df_all["Order Number"])

    frames: list[pd.DataFrame] = []
    seen_orders: set[tuple[str, str, str]] = set()
    for _, q in df_q.iterrows():
        date = str(q.get("Date", "")).strip()
        proc = _normalise_match_value(q.get("Process", ""))
        item = _normalise_match_value(q.get("Item Number", ""))
        if not date or not proc or not item:
            continue
        mask_anchor = df_all["Date"].astype(str).str.strip().eq(date) & df_all["Process"].eq(proc) & df_all["Item Number"].eq(item)
        df_anchor = df_all[mask_anchor]
        if df_anchor.empty:
            continue
        anchor = df_anchor.iloc[-1]
        order_no = _normalise_match_value(anchor.get("Order Number (Base)", ""))
        if not order_no:
            continue
        order_key = (date, proc, order_no)
        if order_key in seen_orders:
            continue
        mask_rows = df_all["Date"].astype(str).str.strip().eq(date) & df_all["Order Number (Base)"].eq(order_no) & df_all["Process"].eq(proc)
        df_rows = df_all[mask_rows]
        if not df_rows.empty:
            frames.append(df_rows)
            seen_orders.add(order_key)

    if not frames:
        return pd.DataFrame()
    df_run = pd.concat(frames, ignore_index=True)
    return df_run.drop_duplicates(subset=["Date", "Process and Item Number"], keep="last").reset_index(drop=True)


def run_missing_run_from_all_orders(
    missing_input_path: str | Path,
    all_orders_path: str | Path = ALL_ORDERS_PATH,
    process_name: str = "missing_run",
    date_dd_mm_yyyy: str = "",
    shift: str | None = None,
    output_dir: str | Path = PROJECT_ROOT / "Output",
    apparel_dir: str | Path | None = None,
    logo_custom_single_dir: str | Path | None = None,
    logo_custom_double_dir: str | Path | None = None,
    logo_normal_dir: str | Path | None = None,
    pdf_copy_dir: str | Path | None = None,
    excel_copy_dir: str | Path | None = None,
    log: Optional[Callable[[str], None]] = None,
) -> Path:
    if not date_dd_mm_yyyy:
        raise ValueError("date_dd_mm_yyyy is required (DD-MM-YYYY).")
    date_dd_mm_yyyy = date_dd_mm_yyyy.replace("/", "-")
    df_run = _build_missing_run_df(
        Path(all_orders_path),
        Path(missing_input_path),
        fallback_date=date_dd_mm_yyyy,
    )
    if df_run.empty:
        missing_input_path = Path(missing_input_path)
        try:
            cols = list(pd.read_csv(missing_input_path, nrows=0).columns)
        except Exception:
            cols = []
        if "Process and Item Number" in cols and not all(c in cols for c in ("Date", "Process", "Item Number")):
            raise ValueError(
                "No matching rows found. The selected file is a step-6 output CSV (Process and Item Number only). "
                f"Ensure the GUI Date ({date_dd_mm_yyyy}) matches the dispatch date in All Orders, "
                "or use Missing/Missing Input.csv with Date, Process, and Item Number columns."
            )
        raise ValueError("No matching rows found for any query in Missing Input CSV.")
    return _run_step6_style_outputs(
        df=df_run,
        name=process_name,
        output_dir=output_dir,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        apparel_dir=apparel_dir,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
        logo_normal_dir=logo_normal_dir,
        shift=shift,
        pdf_copy_dir=pdf_copy_dir,
        excel_copy_dir=excel_copy_dir,
        show_process_item_count=False,
        nest_pdf_under_shift=False,
        nest_excel_under_shift=True,
        log=_coerce_pipeline_log(log),
    )
