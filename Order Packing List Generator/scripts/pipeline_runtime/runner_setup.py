from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from pipeline_runtime.pipeline_log import PipelineLog, detail_callable
from pipeline_runtime.runner_utils import ALL_ORDERS_PATH, _ensure_dir
from pipeline_split_by_process_item.common import pin_batch_shift
from shared.demo_images import effective_image_dirs


def _log_path(label: str, p: str | Path | None, log: PipelineLog) -> None:
    if not p:
        log.detail(f"  {label}: (not set)")
        return
    try:
        log.detail(f"  {label}: {Path(p).resolve()}")
    except OSError:
        log.detail(f"  {label}: {p}")


def prepare_pipeline_run(
    *,
    input_csv: str | Path,
    date_dd_mm_yyyy: str,
    shift: str,
    output_dir: str | Path,
    workbook_path: str | Path,
    apparel_dir,
    logo_custom_single_dir,
    logo_custom_double_dir,
    logo_normal_dir,
    use_demo_images: bool,
    phases: str,
    cl_csv_path: Optional[str | Path],
    use_fixed_process_number: bool,
    fixed_process_number: Optional[str],
    separate_by_logo_id: bool,
    logo_id_threshold: int,
    pdf_copy_dir,
    excel_copy_dir,
    log: Optional[PipelineLog],
) -> dict:
    """Validate inputs, resolve dirs, and log the run banner. Returns context dict."""
    input_csv_path = Path(input_csv)
    base_output_dir = Path(output_dir)
    workbook_path = Path(workbook_path)
    cl_csv = Path(cl_csv_path) if cl_csv_path is not None else None

    if not input_csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv_path}")

    use_demo = bool(use_demo_images)
    apparel_dir, logo_normal_dir, logo_custom_single_dir, logo_custom_double_dir = effective_image_dirs(
        use_demo,
        apparel_dir,
        logo_normal_dir,
        logo_custom_single_dir,
        logo_custom_double_dir,
    )

    date_dd_mm_yyyy = date_dd_mm_yyyy.replace("/", "-")
    try:
        dispatch_date = datetime.strptime(date_dd_mm_yyyy, "%d-%m-%Y").date()
    except ValueError as exc:
        raise ValueError(f"Date must be in DD-MM-YYYY format, got '{date_dd_mm_yyyy}'.") from exc

    token = pin_batch_shift(input_csv_path.stem)
    shift_label = (shift or "").strip()
    if not shift_label:
        raise ValueError("Shift must be a non-empty string.")
    output_root = base_output_dir / date_dd_mm_yyyy / f"{shift_label} Shift" / token
    if phases != "pdf":
        _ensure_dir(output_root)
    elif not output_root.is_dir():
        raise FileNotFoundError(
            f"PDF phase requires existing output folder from Excel phase: {output_root}"
        )

    lc = detail_callable(log)
    if log:
        log.detail("----------")
        phase_label = {
            "all": "full (Excel+PDF)",
            "excel": "Excel only (steps 1–7)",
            "pdf": "PDF only (step 8)",
        }[phases]
        log.detail(f"Pipeline run ({phase_label})")
        log.detail(f"  Input CSV:     {input_csv_path.resolve()}")
        log.detail(f"  Output folder: {output_root.resolve()}")
        log.detail(f"  Dispatch date: {date_dd_mm_yyyy}   Shift: {shift_label}")
        log.detail(f"  Workbook:      {workbook_path.resolve()}")
        if cl_csv is not None:
            log.detail(f"  CL CSV:        {cl_csv.resolve()}")
        else:
            log.detail("  CL CSV:        (default live Custom_Label_Database.csv)")
        log.detail(
            f"  Options:       use_fixed_process_number={use_fixed_process_number}   "
            f"fixed={fixed_process_number!r}"
        )
        log.detail(
            f"                 separate_by_logo_id={separate_by_logo_id}   "
            f"logo_id_threshold={logo_id_threshold}"
        )
        log.detail("  Image dirs:")
        _log_path("Apparel", apparel_dir, log)
        _log_path("Logo custom (single)", logo_custom_single_dir, log)
        _log_path("Logo custom (double)", logo_custom_double_dir, log)
        _log_path("Logo normal", logo_normal_dir, log)
        _log_path("PDF copy", pdf_copy_dir, log)
        _log_path("Excel copy", excel_copy_dir, log)
        if use_demo:
            log.detail("  Demo images: enabled (Demo Images Database/)")
        log.detail(f"  All Orders log file: {ALL_ORDERS_PATH.resolve()}")
        log.detail("----------")

    return {
        "input_csv_path": input_csv_path,
        "workbook_path": workbook_path,
        "cl_csv": cl_csv,
        "use_demo": use_demo,
        "apparel_dir": apparel_dir,
        "logo_normal_dir": logo_normal_dir,
        "logo_custom_single_dir": logo_custom_single_dir,
        "logo_custom_double_dir": logo_custom_double_dir,
        "date_dd_mm_yyyy": date_dd_mm_yyyy,
        "dispatch_date": dispatch_date,
        "token": token,
        "shift_label": shift_label,
        "output_root": output_root,
        "lc": lc,
    }
