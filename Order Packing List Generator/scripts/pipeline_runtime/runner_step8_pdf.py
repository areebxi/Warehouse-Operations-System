from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from scripts.pipeline_generate_packing_list_pdf.runtime_api import count_image_lookup_stats
from scripts.pipeline_runtime.order_number_csv import read_csv_with_order_numbers
from scripts.pipeline_runtime.pipeline_log import PipelineLog, detail_callable
from scripts.pipeline_runtime.runner_utils import (
    build_image_trace_log_file_body,
    log_image_trace_block,
)


def _log_stem_sample_keys(
    log: Optional[PipelineLog],
    label: str,
    stem_map: Optional[Dict[str, Path]],
    limit: int = 40,
) -> None:
    if not log or not stem_map:
        return
    keys = sorted(stem_map.keys())[:limit]
    log.detail(
        f"  Step 8 stem sample ({label}): {len(keys)} of {len(stem_map)} key(s) (alphabetically first): {', '.join(keys)}"
    )
    if len(stem_map) > limit:
        log.detail(f"  Step 8 stem sample ({label}): ... {len(stem_map) - limit} more key(s) not listed")


def _log_overlay_sample(
    log: Optional[PipelineLog],
    position_code_to_draw: dict[str, str],
    limit: int = 50,
) -> None:
    if not log or not position_code_to_draw:
        return
    n = len(position_code_to_draw)
    take = min(limit, n)
    log.detail(f"  Step 8 workbook overlay (Position Code -> asset): {n} entr(y/ies); listing first {take}:")
    for k, v in sorted(position_code_to_draw.items(), key=lambda kv: str(kv[0]))[:take]:
        log.detail(f"    {k!r} -> {v}")
    if n > take:
        log.detail(f"  Step 8 workbook overlay: ... {n - take} more entr(y/ies) omitted")


def run_step8_pdf_generation_impl(
    *,
    step6_csvs: list[Path],
    workbook_path: Path,
    apparel_dir: Optional[str | Path],
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    build_image_stem_map,
    render_one_pdf,
    csv_to_pdf,
    load_position_code_to_draw,
    format_missing_report,
    collect_image_match_details,
    format_image_match_log,
    sanitize_process_for_filename,
    date_dd_mm_yyyy: Optional[str] = None,
    log: Optional[PipelineLog] = None,
) -> Optional[str]:
    apparel_dir_path = Path(apparel_dir) if apparel_dir else None
    logo_custom_single_path = Path(logo_custom_single_dir) if logo_custom_single_dir else None
    logo_custom_double_path = Path(logo_custom_double_dir) if logo_custom_double_dir else None
    logo_normal_path = Path(logo_normal_dir) if logo_normal_dir else None

    lc = detail_callable(log)
    if log:
        log.step(
            "Step 8/8: PDF — indexing image folders (parallel scan of apparel + logo directories). "
            "Very large folders can take 30–120s on first scan; later runs in this session reuse "
            "an in-memory (and on-disk) stem-map cache. Stem counts appear in the next block."
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
    index_elapsed = time.perf_counter() - t_index

    logo_custom_stem_map: Dict[str, Path] = {}
    for src in (logo_custom_single_stem_map, logo_custom_double_stem_map):
        if src:
            for stem, path in src.items():
                if stem not in logo_custom_stem_map:
                    logo_custom_stem_map[stem] = path

    run_timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    position_code_to_draw = load_position_code_to_draw(workbook_path) if workbook_path.exists() else {}

    if log:
        log.detail(
            f"Step 8/8: image folder index complete in {index_elapsed:.2f}s — stem counts and paths:"
        )
        log.detail(
            "  Stem maps: scan each configured folder (top-level only, not recursive) for "
            ".png / .jpg / .jpeg; file stem -> path. PDF code resolves Apparel Image / Picture Name "
            "and Logo/Design Image tokens against these maps (custom vs normal rules in generator)."
        )
        la = len(apparel_stem_map) if apparel_stem_map else 0
        lcs = len(logo_custom_single_stem_map) if logo_custom_single_stem_map else 0
        lcd = len(logo_custom_double_stem_map) if logo_custom_double_stem_map else 0
        ln = len(logo_normal_stem_map) if logo_normal_stem_map else 0
        lc_merged = len(logo_custom_stem_map) if logo_custom_stem_map else 0
        log.detail(f"  Apparel dir: {apparel_dir_path or '(not set)'} -> {la} unique stem(s) indexed.")
        log.detail(f"  Logo custom single: {logo_custom_single_path or '(not set)'} -> {lcs} stem(s).")
        log.detail(
            f"  Logo custom double: {logo_custom_double_path or '(not set)'} -> {lcd} stem(s) "
            f"(merged with single -> {lc_merged} combined)."
        )
        log.detail(f"  Logo normal: {logo_normal_path or '(not set)'} -> {ln} stem(s).")
        log.detail(f"  Workbook overlay map (Position Code -> drawing): {len(position_code_to_draw)} entr(y/ies).")
        _log_overlay_sample(log, position_code_to_draw)
        _log_stem_sample_keys(log, "apparel", apparel_stem_map)
        _log_stem_sample_keys(log, "logo custom (merged single+double)", logo_custom_stem_map)
        _log_stem_sample_keys(log, "logo normal", logo_normal_stem_map)
        log.detail(
            "  Step 8: full image trace (context + every row + summary) is written into this same "
            "pipeline transcript below — no second file under logs/."
        )

    has_image_lookup_main = (
        apparel_stem_map is not None
        or logo_custom_stem_map is not None
        or logo_normal_stem_map is not None
        or (apparel_dir_path and apparel_dir_path.is_dir())
        or (logo_custom_single_path and logo_custom_single_path.is_dir())
        or (logo_custom_double_path and logo_custom_double_path.is_dir())
        or (logo_normal_path and logo_normal_path.is_dir())
    )

    if log:
        log.step("Step 8/8: Generating PDFs...")
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
    if has_image_lookup_main:
        for csv_path in step6_csvs:
            process_name = sanitize_process_for_filename(csv_path.stem)
            df_csv = read_csv_with_order_numbers(csv_path)
            details = collect_image_match_details(
                df_csv,
                apparel_stem_map,
                logo_normal_stem_map,
                logo_custom_stem_map,
                apparel_image_dir=apparel_dir_path,
                logo_customise_dir=None,
                logo_normal_dir=logo_normal_path,
            )
            detail_text = format_image_match_log(details)
            stats = count_image_lookup_stats(
                df_csv,
                apparel_stem_map,
                logo_normal_stem_map,
                logo_custom_stem_map,
                apparel_image_dir=apparel_dir_path,
                logo_customise_dir=None,
                logo_normal_dir=logo_normal_path,
            )
            file_body = build_image_trace_log_file_body(
                step_label="Step 8/8 — image resolution after PDF generation",
                run_timestamp=run_timestamp,
                source_csv=csv_path,
                row_count=len(df_csv),
                workbook_path=workbook_path,
                output_pdf=csv_path.with_suffix(".pdf"),
                output_folder=csv_path.parent,
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
                log.detail(
                    f"  Step 8: image trace for {csv_path.name} (process {process_name}) — "
                    f"apparel {stats['apparel_found']}/{stats['apparel_total']}, "
                    f"logo {stats['logo_found']}/{stats['logo_total']} (full block follows)"
                )
            log_image_trace_block(lc, file_body)
    elif log:
        log.detail(
            "  Step 8: no image-lookup trace block (no stem maps and no configured image directories)."
        )

    if log:
        log.step("Step 8/8: Done.")

    return step8_missing_logos_report
