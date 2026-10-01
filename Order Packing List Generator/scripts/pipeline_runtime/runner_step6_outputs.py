from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from pipeline_generate_excel_outputs.config import REQUIRED as EXCEL_REQUIRED_COLUMNS
from pipeline_generate_excel_outputs.service import run as run_generate_excel_outputs
from pipeline_runtime.pipeline_log import PipelineLog, detail_callable
from pipeline_runtime.runner_step6_pdf import run_step6_pdf_phase
from pipeline_runtime.runner_utils import (
    _FILENAME_UNSAFE,
    _copy_outputs_to_shift_dirs,
    _ensure_dir,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

MISSING_LOGO_IMAGE_COLUMNS = [
    "Picture Name",
    "Apparel Image",
    "Logo/Design Image",
    "Customise",
    "Position Code",
]


def run_step6_style_outputs(
    df: pd.DataFrame,
    name: str,
    output_dir: str | Path,
    date_dd_mm_yyyy: str,
    apparel_dir: Optional[str | Path],
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    shift: Optional[str] = None,
    pdf_copy_dir: Optional[str | Path] = None,
    excel_copy_dir: Optional[str | Path] = None,
    show_process_item_count: bool = True,
    log: Optional[PipelineLog] = None,
    *,
    nest_pdf_under_shift: bool = True,
    nest_excel_under_shift: bool = True,
    use_demo_images: bool = False,
) -> Path:
    date_dd_mm_yyyy = date_dd_mm_yyyy.replace("/", "-")
    try:
        dispatch_date = datetime.strptime(date_dd_mm_yyyy, "%d-%m-%Y").date()
    except ValueError as exc:
        raise ValueError(f"Date must be in DD-MM-YYYY format, got '{date_dd_mm_yyyy}'.") from exc

    name = (name or "").strip()
    if not name:
        raise ValueError("Process name cannot be empty.")
    if _FILENAME_UNSAFE.search(name):
        raise ValueError("Process name cannot contain / \\ : * ? \" < > |")

    if df is None or df.empty:
        raise ValueError("Step-6 data is empty; nothing to export.")

    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for col in ("Apparel Image", "Logo/Design Image", "Picture Name"):
        if col in df.columns:
            df[col] = df[col].apply(lambda v: "" if pd.isna(v) else str(v).strip())

    missing_base = [c for c in EXCEL_REQUIRED_COLUMNS if c not in df.columns]
    if missing_base:
        raise ValueError(f"Step-6 data is missing required column(s): {', '.join(missing_base)}.")

    missing_image = [c for c in MISSING_LOGO_IMAGE_COLUMNS if c not in df.columns]
    if missing_image:
        raise ValueError(
            "Step-6 data is missing required column(s) for PDF images: " + ", ".join(missing_image)
        )

    base_output_dir = Path(output_dir)
    shift_label = (shift or "").strip()
    output_root = (
        base_output_dir / date_dd_mm_yyyy / f"{shift_label} Shift" / name
        if shift_label
        else base_output_dir / date_dd_mm_yyyy / name
    )
    _ensure_dir(output_root)

    lc = detail_callable(log)
    csv_path = output_root / f"{name}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8")
    if log:
        log.detail(f"Wrote {len(df)} rows to {csv_path.name}")

    _wh = PROJECT_ROOT.parent
    if str(_wh) not in sys.path:
        sys.path.insert(0, str(_wh))
    from shared.demo_images import demo_image_lookup, effective_image_dirs  # noqa: E402

    use_demo = bool(use_demo_images)
    apparel_dir_path, logo_normal_path, logo_custom_single_path, logo_custom_double_path = (
        effective_image_dirs(
            use_demo,
            apparel_dir,
            logo_normal_dir,
            logo_custom_single_dir,
            logo_custom_double_dir,
        )
    )

    if log:
        log.step(
            "Step 7 (missing pipeline): Generating Excel outputs (Picking, Orders Details, DTF Des)..."
        )
    run_generate_excel_outputs(
        csv_path,
        output_root,
        dispatch_date,
        use_fixed_process_number=True,
        use_fixed_numeric_process=False,
        log=lc,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        shift_label=shift_label or None,
    )
    if log:
        xlsx_here = sorted(output_root.glob("*.xlsx"))
        log.detail(
            f"Step 7 (missing pipeline): Done — {len(xlsx_here)} workbook(s): "
            + ", ".join(x.name for x in xlsx_here)
        )

    run_step6_pdf_phase(
        name=name,
        output_root=output_root,
        csv_path=csv_path,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        apparel_dir_path=apparel_dir_path,
        logo_normal_path=logo_normal_path,
        logo_custom_single_path=logo_custom_single_path,
        logo_custom_double_path=logo_custom_double_path,
        use_demo=use_demo,
        demo_image_lookup=demo_image_lookup,
        show_process_item_count=show_process_item_count,
        pdf_copy_dir=pdf_copy_dir,
        excel_copy_dir=excel_copy_dir,
        nest_pdf_under_shift=nest_pdf_under_shift,
        nest_excel_under_shift=nest_excel_under_shift,
        shift_label=shift_label,
        _copy_outputs_to_shift_dirs=_copy_outputs_to_shift_dirs,
        log=log,
        lc=lc,
    )
    return output_root
