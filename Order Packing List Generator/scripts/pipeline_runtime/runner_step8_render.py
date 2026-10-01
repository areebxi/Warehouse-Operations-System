from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from pipeline_runtime.pipeline_log import PipelineLog


def render_step8_pdfs(
    *,
    step6_csvs: list[Path],
    indexed: dict[str, Any],
    render_one_pdf,
    csv_to_pdf,
    format_missing_report,
    date_dd_mm_yyyy: Optional[str],
    log: Optional[PipelineLog],
    lc,
) -> Optional[str]:
    apparel_stem_map = indexed["apparel_stem_map"]
    logo_custom_stem_map = indexed["logo_custom_stem_map"]
    logo_normal_stem_map = indexed["logo_normal_stem_map"]
    apparel_dir_path = indexed["apparel_dir_path"]
    logo_normal_path = indexed["logo_normal_path"]
    position_code_to_draw = indexed["position_code_to_draw"]
    all_missing_logo_actual_dfs: list[pd.DataFrame] = []
    all_missing_apparel_actual_dfs: list[pd.DataFrame] = []
    step8_missing_logos_report: Optional[str] = None

    if len(step6_csvs) > 1:
        max_workers = min(2, os.cpu_count() or 2)
        if log:
            log.detail(
                f"  Step 8: {len(step6_csvs)} process CSV(s) — rendering PDFs via ProcessPoolExecutor "
                f"(max_workers={max_workers})."
            )
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    render_one_pdf,
                    str(csv_path),
                    str(csv_path.with_suffix(".pdf")),
                    apparel_stem_map,
                    logo_custom_stem_map,
                    logo_normal_stem_map,
                    position_code_to_draw,
                    date_dd_mm_yyyy,
                ): csv_path
                for csv_path in step6_csvs
            }
            for future in as_completed(futures):
                csv_name, pdf_name, n_pages, missing_logo_actual_df, missing_apparel_actual_df = future.result()
                if missing_logo_actual_df is not None and not missing_logo_actual_df.empty:
                    all_missing_logo_actual_dfs.append(missing_logo_actual_df)
                if missing_apparel_actual_df is not None and not missing_apparel_actual_df.empty:
                    all_missing_apparel_actual_dfs.append(missing_apparel_actual_df)
                if log:
                    log.detail(f"  Step 8: {csv_name} -> {pdf_name} ({n_pages} page(s))")
                    try:
                        pp = Path(pdf_name)
                        if pp.is_file():
                            log.detail(f"  Step 8: PDF file {pp.resolve()} size={pp.stat().st_size} bytes")
                    except OSError:
                        pass
    else:
        for csv_path in step6_csvs:
            pdf_path = csv_path.with_suffix(".pdf")
            n_rows = len(pd.read_csv(csv_path, encoding="utf-8"))
            if log:
                log.detail(
                    f"  Step 8: csv_to_pdf start — csv={csv_path.resolve()} "
                    f"out_pdf={pdf_path.resolve()} rows={n_rows}"
                )
            t_pdf = time.perf_counter()
            n_pages, paths, missing_logo_actual_df, missing_apparel_actual_df = csv_to_pdf(
                csv_path,
                pdf_path,
                apparel_image_dir=apparel_dir_path,
                logo_customise_dir=None,
                logo_normal_dir=logo_normal_path,
                apparel_stem_map=apparel_stem_map,
                logo_custom_stem_map=logo_custom_stem_map or None,
                logo_normal_stem_map=logo_normal_stem_map,
                position_code_to_draw=position_code_to_draw,
                pdf_asset_log=lc,
                date_dd_mm_yyyy=date_dd_mm_yyyy,
            )
            if missing_logo_actual_df is not None and not missing_logo_actual_df.empty:
                all_missing_logo_actual_dfs.append(missing_logo_actual_df)
            if missing_apparel_actual_df is not None and not missing_apparel_actual_df.empty:
                all_missing_apparel_actual_dfs.append(missing_apparel_actual_df)
            if log:
                dt = time.perf_counter() - t_pdf
                display = ", ".join(p.name for p in paths) if paths and len(paths) > 1 else (paths[0].name if paths else pdf_path.name)
                sz = pdf_path.stat().st_size if pdf_path.is_file() else 0
                log.detail(
                    f"  Step 8: csv_to_pdf done in {dt:.2f}s — {csv_path.name} -> {display} "
                    f"({n_pages} page(s), {sz} bytes on disk)"
                )

    missing_logo_combined = pd.concat(all_missing_logo_actual_dfs, ignore_index=True) if all_missing_logo_actual_dfs else None
    missing_apparel_combined = pd.concat(all_missing_apparel_actual_dfs, ignore_index=True) if all_missing_apparel_actual_dfs else None
    if missing_logo_combined is not None or missing_apparel_combined is not None:
        report = format_missing_report(missing_logo_combined, missing_apparel_combined)
        if report:
            step8_missing_logos_report = report
            if log:
                log.detail(report)
    return step8_missing_logos_report

