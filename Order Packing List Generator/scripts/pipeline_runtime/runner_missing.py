from __future__ import annotations

from pathlib import Path
from typing import Optional
from zipfile import BadZipFile

import pandas as pd
from pandas.errors import ParserError

from scripts.pipeline_fill_prime_images.service import fill_apparel_and_logo_from_df
from scripts.pipeline_runtime.order_number_csv import (
    read_csv_with_order_numbers,
    read_excel_with_order_numbers,
)
from scripts.pipeline_runtime.pipeline_log import PipelineLog
from scripts.pipeline_runtime.runner_step6_outputs import (
    MISSING_LOGO_IMAGE_COLUMNS,
    run_step6_style_outputs,
)


def run_missing_logos_pipeline(
    missing_logos_excel_path: str | Path,
    fixed_process_name: str,
    output_dir: str | Path,
    date_dd_mm_yyyy: str,
    apparel_dir: Optional[str | Path],
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    shift: Optional[str] = None,
    pdf_copy_dir: Optional[str | Path] = None,
    excel_copy_dir: Optional[str | Path] = None,
    log: Optional[PipelineLog] = None,
) -> Path:
    path = Path(missing_logos_excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing file not found: {path}")
    if log:
        log.step("Reading missing assets file...")
    suffix = path.suffix.lower()
    try:
        if suffix in {".xlsx", ".xlsm"}:
            df = read_excel_with_order_numbers(path)
        elif suffix == ".csv":
            df = read_csv_with_order_numbers(path)
        else:
            raise ValueError(
                "Missing file must be an Excel (.xlsx, .xlsm) or CSV (.csv) file."
            )
    except BadZipFile as exc:
        raise ValueError(
            "Selected missing file is not a valid Excel .xlsx workbook. "
            "Use an existing 'Missing Logos (date).xlsx' file or a CSV with the same columns."
        ) from exc
    except (UnicodeDecodeError, ParserError) as exc:
        raise ValueError(
            "Selected missing file is not a valid CSV. "
            "Please export a text CSV or use the original 'Missing Logos (date).xlsx' workbook."
        ) from exc

    for col in ("Apparel Image", "Logo/Design Image", "Picture Name"):
        if col in df.columns:
            df[col] = df[col].apply(lambda v: "" if pd.isna(v) else str(v).strip())
    if df.empty:
        raise ValueError(f"Missing file is empty: {path}")
    df.columns = [str(c).strip() for c in df.columns]

    missing_image = [c for c in MISSING_LOGO_IMAGE_COLUMNS if c not in df.columns]
    if missing_image:
        derive_needed = ["Apparel Image", "Logo/Design Image"]
        can_derive = all(c in df.columns for c in ["Picture Name", "Item SKU", "Customise", "Order Number"])
        if set(missing_image) <= set(derive_needed) and can_derive:
            if log:
                log.detail("Re-deriving Apparel Image and Logo/Design Image from Picture Name, Item SKU, Customise...")
            df = fill_apparel_and_logo_from_df(df)
        else:
            raise ValueError(
                f"Missing file is missing required column(s) for PDF images: {', '.join(missing_image)}. "
                "Required: Picture Name, Apparel Image, Logo/Design Image, Customise, Position Code. "
                "Do not rename or delete column headers when editing 'Missing Logos (date).xlsx'."
            )

    output_root = run_step6_style_outputs(
        df=df,
        name=fixed_process_name,
        output_dir=output_dir,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        apparel_dir=apparel_dir,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
        logo_normal_dir=logo_normal_dir,
        shift=shift,
        pdf_copy_dir=pdf_copy_dir,
        excel_copy_dir=excel_copy_dir,
        log=log,
    )
    if log:
        log.step("Done.")
    return output_root
