from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from pipeline_generate_packing_list_pdf.runtime_api import (
    build_image_stem_map,
    collect_image_match_details,
    count_image_lookup_stats,
    csv_to_pdf,
    format_image_match_log,
    load_position_code_to_draw,
)
from pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_utils import (
    build_image_trace_log_file_body,
    log_image_trace_block,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_step6_pdf_phase(
    *,
    name: str,
    output_root: Path,
    csv_path: Path,
    date_dd_mm_yyyy: str,
    apparel_dir_path,
    logo_normal_path,
    logo_custom_single_path,
    logo_custom_double_path,
    use_demo: bool,
    demo_image_lookup,
    show_process_item_count: bool,
    pdf_copy_dir,
    excel_copy_dir,
    nest_pdf_under_shift: bool,
    nest_excel_under_shift: bool,
    shift_label: str,
    _copy_outputs_to_shift_dirs,
    log: Optional[PipelineLog],
    lc,
) -> None:
    if log:
        log.step(
            "Step 8 (missing pipeline): PDF — scanning image folders for stems "
            "(first scan may take 30–120s; later runs reuse stem-map cache)..."
        )

    t_index = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as executor:
        fut_apparel = executor.submit(build_image_stem_map, apparel_dir_path, recursive=False)
        fut_logo_custom_single = executor.submit(build_image_stem_map, logo_custom_single_path, recursive=False)
        fut_logo_custom_double = executor.submit(build_image_stem_map, logo_custom_double_path, recursive=False)
        fut_logo_normal = executor.submit(build_image_stem_map, logo_normal_path, recursive=False)
        apparel_stem_map = fut_apparel.result()
        logo_custom_single_stem_map = fut_logo_custom_single.result()
        logo_custom_double_stem_map = fut_logo_custom_double.result()
        logo_normal_stem_map = fut_logo_normal.result()
    if log:
        log.detail(
            f"Step 8 (missing pipeline): image folder index complete in "
            f"{time.perf_counter() - t_index:.2f}s"
        )

    logo_custom_stem_map: Dict[str, Path] = {}
    for src in (logo_custom_single_stem_map, logo_custom_double_stem_map):
        if src:
            for stem, path in src.items():
                if stem not in logo_custom_stem_map:
                    logo_custom_stem_map[stem] = path

    if log:
        log.step("Step 8 (missing pipeline): Generating PDF...")
    pdf_path = output_root / f"{name}.pdf"
    _wh = PROJECT_ROOT.parent
    if str(_wh) not in sys.path:
        sys.path.insert(0, str(_wh))
    from shared import paths as wh
    workbook_path = wh.packing_workbook_path()
    try:
        position_code_to_draw = load_position_code_to_draw(workbook_path) if workbook_path.exists() else {}
    except Exception:
        position_code_to_draw = {}
    with demo_image_lookup(use_demo):
        n_pages, _paths, _ml, _ma = csv_to_pdf(
            csv_path,
            pdf_path,
            apparel_image_dir=apparel_dir_path,
            logo_customise_dir=None,
            logo_normal_dir=logo_normal_path,
            apparel_stem_map=apparel_stem_map,
            logo_custom_stem_map=logo_custom_stem_map or None,
            logo_normal_stem_map=logo_normal_stem_map,
            position_code_to_draw=position_code_to_draw,
            show_process_item_count=show_process_item_count,
            pdf_asset_log=lc,
            date_dd_mm_yyyy=date_dd_mm_yyyy,
        )
    if log:
        log.detail(f"Step 8 (missing pipeline): PDF written — {pdf_path.name} ({n_pages} page(s))")

    df_for_stats = read_csv_with_order_numbers(csv_path, encoding="utf-8")
    has_image_lookup = (
        apparel_stem_map is not None
        or logo_custom_stem_map is not None
        or logo_normal_stem_map is not None
        or (apparel_dir_path and apparel_dir_path.is_dir())
        or (logo_custom_single_path and logo_custom_single_path.is_dir())
        or (logo_custom_double_path and logo_custom_double_path.is_dir())
        or (logo_normal_path and logo_normal_path.is_dir())
    )
    if has_image_lookup:
        details = collect_image_match_details(
            df_for_stats,
            apparel_stem_map,
            logo_normal_stem_map,
            logo_custom_stem_map,
            apparel_image_dir=apparel_dir_path,
            logo_customise_dir=None,
            logo_normal_dir=logo_normal_path,
        )
        run_ts = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        detail_text = format_image_match_log(details)
        stats = count_image_lookup_stats(
            df_for_stats,
            apparel_stem_map,
            logo_normal_stem_map,
            logo_custom_stem_map,
            apparel_image_dir=apparel_dir_path,
            logo_customise_dir=None,
            logo_normal_dir=logo_normal_path,
        )
        file_body = build_image_trace_log_file_body(
            step_label="Step-6-style outputs — image resolution after PDF",
            run_timestamp=run_ts,
            source_csv=csv_path,
            row_count=len(df_for_stats),
            workbook_path=workbook_path,
            output_pdf=pdf_path,
            output_folder=output_root,
            apparel_dir=apparel_dir_path,
            logo_custom_single_dir=logo_custom_single_path,
            logo_custom_double_dir=logo_custom_double_path,
            logo_normal_dir=logo_normal_path,
            unique_apparel_stems=len(apparel_stem_map or {}),
            unique_logo_custom_stems=len(logo_custom_stem_map or {}),
            unique_logo_normal_stems=len(logo_normal_stem_map or {}),
            detail_text=detail_text,
            apparel_found=stats["apparel_found"],
            apparel_total=stats["apparel_total"],
            logo_found=stats["logo_found"],
            logo_total=stats["logo_total"],
        )
        if log:
            if stats["apparel_total"] or stats["logo_total"]:
                log.detail(
                    f"Image lookup: apparel {stats['apparel_found']}/{stats['apparel_total']} found, "
                    f"logo {stats['logo_found']}/{stats['logo_total']} found"
                )
            log.detail("Missing pipeline: full image trace (same transcript, no separate logs/ file):")
        log_image_trace_block(lc, file_body)

    if pdf_copy_dir or excel_copy_dir:
        _copy_outputs_to_shift_dirs(
            output_root,
            shift_label or "",
            pdf_copy_dir,
            excel_copy_dir,
            lc,
            nest_pdf_under_shift=nest_pdf_under_shift,
            nest_excel_under_shift=nest_excel_under_shift,
        )
    if log:
        log.detail(f"Done. Outputs written to:\n  {output_root}")
