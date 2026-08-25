from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd
from reportlab.pdfgen import canvas

from scripts.pipeline_generate_packing_list_pdf.draw_page_date_header import (
    format_dispatch_date_header,
)
from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers


def csv_to_pdf_impl(
    csv_path: Path,
    output_path: Path,
    apparel_image_dir: Optional[Path],
    logo_customise_dir: Optional[Path],
    logo_normal_dir: Optional[Path],
    apparel_stem_map: Optional[Dict[str, Path]],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    position_code_to_draw: Optional[Dict[str, str]],
    show_process_item_count: bool,
    pdf_asset_log: Optional[Callable[[str], None]] = None,
    date_dd_mm_yyyy: Optional[str] = None,
    *,
    max_pages_per_pdf: int,
    page_width: float,
    page_height: float,
    build_image_stem_map: Callable[[Optional[Path], bool], Dict[str, Path]],
    build_order_counts: Callable[[pd.DataFrame], dict],
    build_process_totals: Callable[[pd.DataFrame], Dict[str, int]],
    draw_page: Callable[..., Tuple[bool, bool]],
) -> Tuple[int, List[Path], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    df = read_csv_with_order_numbers(csv_path)
    if df.empty:
        return 0, [], None, None

    if apparel_stem_map is None and apparel_image_dir is not None and apparel_image_dir.is_dir():
        apparel_stem_map = build_image_stem_map(apparel_image_dir, recursive=False)
    if logo_custom_stem_map is None and logo_customise_dir is not None and logo_customise_dir.is_dir():
        logo_custom_stem_map = build_image_stem_map(logo_customise_dir, recursive=True)
    if logo_normal_stem_map is None and logo_normal_dir is not None and logo_normal_dir.is_dir():
        logo_normal_stem_map = build_image_stem_map(logo_normal_dir, recursive=False)

    order_number_counts = build_order_counts(df)
    process_totals = build_process_totals(df) if show_process_item_count else None
    dispatch_date_label: Optional[str] = None
    dispatch_day_name: Optional[str] = None
    if date_dd_mm_yyyy:
        dispatch_date_label, dispatch_day_name = format_dispatch_date_header(date_dd_mm_yyyy)
    n = len(df)
    written_paths: List[Path] = []
    missing_logo_row_indices: List[int] = []
    missing_apparel_row_indices: List[int] = []

    if n <= max_pages_per_pdf:
        c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))
        c.setTitle(output_path.name)
        for i in range(n):
            row = df.iloc[i]
            had_missing_logo, had_missing_apparel = draw_page(
                c,
                row,
                order_number_counts,
                process_totals,
                apparel_image_dir=apparel_image_dir,
                logo_customise_dir=logo_customise_dir,
                logo_normal_dir=logo_normal_dir,
                apparel_stem_map=apparel_stem_map,
                logo_custom_stem_map=logo_custom_stem_map,
                logo_normal_stem_map=logo_normal_stem_map,
                position_code_to_draw=position_code_to_draw,
                pdf_asset_log=pdf_asset_log,
                pdf_page_index=i,
                dispatch_date_label=dispatch_date_label,
                dispatch_day_name=dispatch_day_name,
            )
            if had_missing_logo:
                missing_logo_row_indices.append(i)
            if had_missing_apparel:
                missing_apparel_row_indices.append(i)
            c.showPage()
        c.save()
        written_paths.append(output_path)
        missing_logo_actual_df = (
            df.iloc[sorted(missing_logo_row_indices)].copy() if missing_logo_row_indices else None
        )
        missing_apparel_actual_df = (
            df.iloc[sorted(missing_apparel_row_indices)].copy() if missing_apparel_row_indices else None
        )
        return n, written_paths, missing_logo_actual_df, missing_apparel_actual_df

    base_dir = output_path.parent
    base_stem = output_path.stem
    part = 1
    for start in range(0, n, max_pages_per_pdf):
        end = min(start + max_pages_per_pdf, n)
        part_path = base_dir / f"{base_stem}_Part {part}.pdf"
        c = canvas.Canvas(str(part_path), pagesize=(page_width, page_height))
        c.setTitle(part_path.name)
        for i in range(start, end):
            row = df.iloc[i]
            had_missing_logo, had_missing_apparel = draw_page(
                c,
                row,
                order_number_counts,
                process_totals,
                apparel_image_dir=apparel_image_dir,
                logo_customise_dir=logo_customise_dir,
                logo_normal_dir=logo_normal_dir,
                apparel_stem_map=apparel_stem_map,
                logo_custom_stem_map=logo_custom_stem_map,
                logo_normal_stem_map=logo_normal_stem_map,
                position_code_to_draw=position_code_to_draw,
                pdf_asset_log=pdf_asset_log,
                pdf_page_index=i,
                dispatch_date_label=dispatch_date_label,
                dispatch_day_name=dispatch_day_name,
            )
            if had_missing_logo:
                missing_logo_row_indices.append(i)
            if had_missing_apparel:
                missing_apparel_row_indices.append(i)
            c.showPage()
        c.save()
        written_paths.append(part_path)
        part += 1

    missing_logo_actual_df = (
        df.iloc[sorted(missing_logo_row_indices)].copy() if missing_logo_row_indices else None
    )
    missing_apparel_actual_df = (
        df.iloc[sorted(missing_apparel_row_indices)].copy() if missing_apparel_row_indices else None
    )
    return n, written_paths, missing_logo_actual_df, missing_apparel_actual_df


def render_one_pdf_impl(
    csv_path_str: str,
    pdf_path_str: str,
    apparel_stem_map: Optional[Dict[str, Path]],
    logo_custom_stem_map: Optional[Dict[str, Path]],
    logo_normal_stem_map: Optional[Dict[str, Path]],
    position_code_to_draw: Optional[Dict[str, str]] = None,
    date_dd_mm_yyyy: Optional[str] = None,
    *,
    csv_to_pdf: Callable[..., Tuple[int, List[Path], Optional[pd.DataFrame], Optional[pd.DataFrame]]],
) -> Tuple[str, str, int, Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    csv_path = Path(csv_path_str)
    pdf_path = Path(pdf_path_str)
    n_pages, paths, missing_logo_actual_df, missing_apparel_actual_df = csv_to_pdf(
        csv_path,
        pdf_path,
        apparel_image_dir=None,
        logo_customise_dir=None,
        logo_normal_dir=None,
        apparel_stem_map=apparel_stem_map,
        logo_custom_stem_map=logo_custom_stem_map,
        logo_normal_stem_map=logo_normal_stem_map,
        position_code_to_draw=position_code_to_draw,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
    )
    pdf_name = ", ".join(p.name for p in paths) if paths else pdf_path.name
    return (
        csv_path.name,
        pdf_name,
        n_pages,
        missing_logo_actual_df,
        missing_apparel_actual_df,
    )
