from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
import pandas as pd
from pipeline_generate_packing_list_pdf.core_helpers import (
    PROCESS_ITEM_RE as _PROCESS_ITEM_RE,
    parse_process_and_item_impl,
    safe_str_impl,
)
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from pipeline_runtime.runner import ALL_ORDERS_PATH, PROJECT_ROOT, _run_step6_style_outputs
import sys
from shared import paths as wh  # noqa: E402

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
    use_demo_images: bool = False,
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
        use_demo_images=use_demo_images,
    )
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
