from __future__ import annotations

import re
import time
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional, Tuple

import pandas as pd  # type: ignore[import]

from scripts.pipeline_cl_lookup.enrich_cl_lookup import NEW_COLUMNS, enrich_packing_data
from scripts.pipeline_cl_lookup.fetch_input_csv import (
    OUTPUT_COLUMNS,
    fetch_input_csv,
    write_fetched_csv,
)
from scripts.pipeline_assign_process_number.service import run as run_assign_process_number
from scripts.pipeline_fill_prime_images.service import fill_packing_columns
from scripts.pipeline_packing_rules.service import apply_packing_rules_to_csv
from scripts.pipeline_generate_excel_outputs.service import run as run_generate_excel_outputs
from scripts.pipeline_generate_packing_list_pdf.runtime_api import (
    build_image_stem_map,
    collect_image_match_details,
    csv_to_pdf,
    format_image_match_log,
    format_missing_report,
    load_position_code_to_draw,
    render_one_pdf,
)
from scripts.pipeline_runtime.filter_missing_logos import filter_step6_csvs_for_missing_logos
from scripts.pipeline_runtime.pipeline_log import PipelineLog, detail_callable
from scripts.pipeline_runtime.runner_missing import run_missing_logos_pipeline
from scripts.pipeline_runtime.runner_step6_outputs import run_step6_style_outputs
from scripts.pipeline_runtime.runner_step8_pdf import run_step8_pdf_generation_impl
from scripts.pipeline_runtime.runner_utils import (
    ALL_ORDERS_PATH,
    _copy_outputs_to_shift_dirs,
    _ensure_dir,
    _move_missing_logo_to_root,
    _move_unmatched_to_root,
    _sanitize_process_for_filename,
    _update_all_orders_log,
    log_csv_preview,
)
from scripts.pipeline_split_by_process_item.service import run as run_split_by_process_and_item_number
from scripts.pipeline_split_position.service import run as run_split_and_assign_position_codes

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

_run_step6_style_outputs = run_step6_style_outputs

PipelinePhase = Literal["all", "excel", "pdf"]


def discover_step6_csvs(output_root: Path, token: str) -> list[Path]:
    """Process CSVs left after Step 6 / missing-logo filter (excludes intermediate pipeline files)."""
    exclude_names = {
        f"1_fetch_input_csv_{token}.csv",
        f"1b_apply_rules_{token}.csv",
        f"2_enrich_cl_lookup_{token}.csv",
        f"3_fill_prime_and_images_{token}.csv",
        f"4_matched_split_and_assign_position_codes_{token}.csv",
        f"5_assign_process_number_{token}.csv",
        f"unmatched_orders_{token}.csv",
        f"missing_logo_orders_{token}.csv",
    }
    return sorted(
        p
        for p in output_root.glob("*.csv")
        if p.name not in exclude_names and not p.name.startswith("_")
    )


def _log_path(label: str, p: str | Path | None, log: PipelineLog) -> None:
    if not p:
        log.detail(f"  {label}: (not set)")
        return
    try:
        log.detail(f"  {label}: {Path(p).resolve()}")
    except OSError:
        log.detail(f"  {label}: {p}")


def run_pipeline(
    input_csv: str | Path,
    date_dd_mm_yyyy: str,
    shift: str,
    output_dir: str | Path,
    workbook_path: str | Path,
    apparel_dir: Optional[str | Path],
    logo_custom_single_dir: Optional[str | Path],
    logo_custom_double_dir: Optional[str | Path],
    logo_normal_dir: Optional[str | Path],
    separate_by_logo_id: bool = False,
    logo_id_threshold: int = 5,
    use_fixed_process_number: bool = False,
    fixed_process_number: Optional[str] = None,
    pdf_copy_dir: Optional[str | Path] = None,
    excel_copy_dir: Optional[str | Path] = None,
    log: Optional[PipelineLog] = None,
    phases: PipelinePhase = "all",
) -> Tuple[Path, Optional[Path], Optional[Path], Optional[str]]:
    """
    Run the packing pipeline for a single input CSV.

    phases:
      - ``all``: steps 1–8 (default)
      - ``excel``: steps 1–7 only (Excel); skip PDF
      - ``pdf``: Step 8 only (rediscover process CSVs in the token output folder)

    Returns:
        (output_root_for_token, unmatched_path_or_none, missing_logo_path_or_none,
         missing_logos_report_or_none)
    """
    if phases not in ("all", "excel", "pdf"):
        raise ValueError(f"phases must be 'all', 'excel', or 'pdf', got {phases!r}")

    input_csv_path = Path(input_csv)
    base_output_dir = Path(output_dir)
    workbook_path = Path(workbook_path)

    if not input_csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv_path}")

    date_dd_mm_yyyy = date_dd_mm_yyyy.replace("/", "-")
    try:
        dispatch_date = datetime.strptime(date_dd_mm_yyyy, "%d-%m-%Y").date()
    except ValueError as exc:
        raise ValueError(f"Date must be in DD-MM-YYYY format, got '{date_dd_mm_yyyy}'.") from exc

    token = input_csv_path.stem
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
        phase_label = {"all": "full (Excel+PDF)", "excel": "Excel only (steps 1–7)", "pdf": "PDF only (step 8)"}[
            phases
        ]
        log.detail(f"Pipeline run ({phase_label})")
        log.detail(f"  Input CSV:     {input_csv_path.resolve()}")
        log.detail(f"  Output folder: {output_root.resolve()}")
        log.detail(f"  Dispatch date: {date_dd_mm_yyyy}   Shift: {shift_label}")
        log.detail(f"  Workbook:      {workbook_path.resolve()}")
        log.detail(f"  Options:       use_fixed_process_number={use_fixed_process_number}   fixed={fixed_process_number!r}")
        log.detail(f"                 separate_by_logo_id={separate_by_logo_id}   logo_id_threshold={logo_id_threshold}")
        log.detail("  Image dirs:")
        _log_path("Apparel", apparel_dir, log)
        _log_path("Logo custom (single)", logo_custom_single_dir, log)
        _log_path("Logo custom (double)", logo_custom_double_dir, log)
        _log_path("Logo normal", logo_normal_dir, log)
        _log_path("PDF copy", pdf_copy_dir, log)
        _log_path("Excel copy", excel_copy_dir, log)
        log.detail(f"  All Orders log file: {ALL_ORDERS_PATH.resolve()}")
        log.detail("----------")

    if phases == "pdf":
        step6_csvs = discover_step6_csvs(output_root, token)
        if log:
            log.step(
                "Step 8/8: starting PDF phase (Excel files are complete). "
                "The next log block may pause briefly while image folders are indexed."
            )
            log.detail(f"  PDF phase: rediscovered {len(step6_csvs)} process CSV(s) in {output_root}")
        step8_missing_logos_report = run_step8_pdf_generation_impl(
            step6_csvs=step6_csvs,
            workbook_path=workbook_path,
            apparel_dir=apparel_dir,
            logo_custom_single_dir=logo_custom_single_dir,
            logo_custom_double_dir=logo_custom_double_dir,
            logo_normal_dir=logo_normal_dir,
            build_image_stem_map=build_image_stem_map,
            render_one_pdf=render_one_pdf,
            csv_to_pdf=csv_to_pdf,
            load_position_code_to_draw=load_position_code_to_draw,
            format_missing_report=format_missing_report,
            collect_image_match_details=collect_image_match_details,
            format_image_match_log=format_image_match_log,
            sanitize_process_for_filename=_sanitize_process_for_filename,
            date_dd_mm_yyyy=date_dd_mm_yyyy,
            log=log,
        )
        copy_warnings: list[str] = []
        if pdf_copy_dir:
            copy_warnings = _copy_outputs_to_shift_dirs(
                output_root, shift_label, pdf_copy_dir, None, lc
            )
            if copy_warnings:
                extra = "\n".join(copy_warnings)
                if step8_missing_logos_report:
                    step8_missing_logos_report = f"{step8_missing_logos_report}\n\n{extra}"
                else:
                    step8_missing_logos_report = extra
        if log:
            log.detail("----------")
            log.detail(f"PDF phase finished. Primary output: {output_root.resolve()}")
            if step8_missing_logos_report and not (
                copy_warnings and step8_missing_logos_report == "\n".join(copy_warnings)
            ):
                log.detail("Missing-logos report was produced (see Step 8 messages above).")
            if copy_warnings:
                log.detail("PDF copy had failures (also included in Finished report):")
                for w in copy_warnings:
                    log.detail(f"  {w}")
            log.detail("----------")
        return output_root, None, None, step8_missing_logos_report

    if log:
        log.step("Step 1/8: Fetching input CSV...")
    t_step = time.perf_counter()
    step1_path = output_root / f"1_fetch_input_csv_{token}.csv"
    rows = fetch_input_csv(input_csv_path)
    write_fetched_csv(rows, step1_path)
    if log:
        log.detail(
            f"Step 1/8: Done ({len(rows)} rows) -> {step1_path.name}  [{time.perf_counter() - t_step:.2f}s]"
        )
        log.detail(
            f"Step 1/8: output column order ({len(OUTPUT_COLUMNS)}): {', '.join(OUTPUT_COLUMNS)}"
        )
        if rows:
            r0 = rows[0]
            head_cols = OUTPUT_COLUMNS[:12]
            pairs = [
                f"{k}={(str(r0.get(k, '')).replace(chr(10), ' ').strip()[:72])}"
                for k in head_cols
                if k in r0
            ]
            if pairs:
                log.detail("Step 1/8: first input row (first columns, truncated): " + " | ".join(pairs))
        log_csv_preview(lc, step1_path, "Step 1 CSV preview (on disk)")

    apply_packing_rules_to_csv(step1_path, token=token, log=lc)

    if log:
        log.step("Step 2/8: Enriching CL lookup...")
    t_step = time.perf_counter()
    step2_path = output_root / f"2_enrich_cl_lookup_{token}.csv"
    df_step2 = enrich_packing_data(step1_path, workbook_path, log=lc)
    df_step2.to_csv(step2_path, index=False, encoding="utf-8")
    if log:
        log.detail(f"Step 2/8: Done ({len(df_step2)} rows) -> {step2_path.name}  [{time.perf_counter() - t_step:.2f}s]")
        present_new = [c for c in NEW_COLUMNS if c in df_step2.columns]
        log.detail(
            f"Step 2/8: total columns {len(df_step2.columns)}; CL-filled targets present: "
            f"{', '.join(present_new)}"
        )
        log_csv_preview(lc, step2_path, "Step 2 CSV preview (CL-enriched)")

    if log:
        log.step("Step 3/8: Filling Prime and images...")
    t_step = time.perf_counter()
    step3_path = output_root / f"3_fill_prime_and_images_{token}.csv"
    df_step3 = fill_packing_columns(step2_path, log=lc)
    df_step3.to_csv(step3_path, index=False, encoding="utf-8")
    if log:
        log.detail(f"Step 3/8: Done ({len(df_step3)} rows) -> {step3_path.name}  [{time.perf_counter() - t_step:.2f}s]")
        log_csv_preview(lc, step3_path, "Step 3 CSV preview (Prime / images filled)")

    if log:
        log.step("Step 4/8: Splitting and assigning position codes...")
    t_step = time.perf_counter()
    run_split_and_assign_position_codes(step3_path, workbook_path, output_root, log=lc)
    unmatched_csv_path = output_root / f"unmatched_orders_{token}.csv"
    unmatched_path: Optional[Path]
    unmatched_count = 0
    if unmatched_csv_path.exists():
        df_unmatched = pd.read_csv(unmatched_csv_path)
        unmatched_count = len(df_unmatched)
        if unmatched_count == 0:
            try:
                unmatched_csv_path.unlink()
            except OSError:
                pass
            unmatched_path = None
        else:
            unmatched_path = unmatched_csv_path
            moved = _move_unmatched_to_root(unmatched_path, date_dd_mm_yyyy, shift_label)
            if moved is not None:
                unmatched_path = moved
    else:
        unmatched_path = None
    matched_step4_path = output_root / f"4_matched_split_and_assign_position_codes_{token}.csv"
    if log:
        matched_count = len(pd.read_csv(matched_step4_path)) if matched_step4_path.exists() else 0
        log.detail(
            f"Step 4/8: Done (matched: {matched_count}, unmatched: {unmatched_count}) "
            f"-> {matched_step4_path.name}"
            + (f"; unmatched moved to {unmatched_path}" if unmatched_path else "")
            + f"  [{time.perf_counter() - t_step:.2f}s]"
        )
        log_csv_preview(lc, matched_step4_path, "Step 4 matched CSV preview (positions)")

    if log:
        log.step("Step 5/8: Assigning process numbers...")
    t_step = time.perf_counter()
    if not matched_step4_path.exists():
        raise FileNotFoundError(f"Step-4 matched CSV not found: {matched_step4_path}")
    fixed = (fixed_process_number or "").strip() if use_fixed_process_number else None
    run_assign_process_number(
        matched_step4_path,
        shift,
        workbook_path,
        output_root,
        dispatch_date=dispatch_date,
        separate_by_logo_id=separate_by_logo_id,
        logo_id_threshold=logo_id_threshold,
        fixed_process_number=fixed,
        log=lc,
    )
    step5_path = output_root / f"5_assign_process_number_{token}.csv"

    if not step5_path.exists():
        raise FileNotFoundError(f"Step-5 CSV not found after assign_process_number: {step5_path}")
    if log:
        n5 = len(pd.read_csv(step5_path))
        log.detail(f"Step 5/8: Done ({n5} rows) -> {step5_path.name}  [{time.perf_counter() - t_step:.2f}s]")
        log_csv_preview(lc, step5_path, "Step 5 CSV preview (process numbers)")

    if log:
        log.step("Step 6/8: Splitting by process and item number...")
    t_step = time.perf_counter()
    fixed_numeric = bool(fixed and re.fullmatch(r"\d+", fixed))
    run_split_by_process_and_item_number(
        step5_path,
        output_root,
        workbook_path,
        run_date=dispatch_date,
        use_simple_process_format=False,
        use_fixed_numeric_process=fixed_numeric,
        fixed_process_number=fixed if fixed_numeric else None,
        log=lc,
    )
    step6_csvs = discover_step6_csvs(output_root, token)
    if log:
        log.step("Filtering missing logos (merge groups)...")
    t_miss = time.perf_counter()
    step6_csvs, missing_logo_path, missing_logo_count = filter_step6_csvs_for_missing_logos(
        step6_csvs,
        output_root=output_root,
        token=token,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
        logo_normal_dir=logo_normal_dir,
        log=lc,
    )
    if missing_logo_path is not None:
        moved_missing = _move_missing_logo_to_root(missing_logo_path, date_dd_mm_yyyy, shift_label)
        if moved_missing is not None:
            missing_logo_path = moved_missing
    if log:
        log.detail(
            f"  Missing-logo filter done — excluded {missing_logo_count} row(s)"
            + (f"; file: {missing_logo_path}" if missing_logo_path else "")
            + f"  [{time.perf_counter() - t_miss:.2f}s]"
        )

    for csv_path in step6_csvs:
        _update_all_orders_log(csv_path, date_dd_mm_yyyy, log=lc)
    if log:
        total_s6 = 0
        for p in sorted(step6_csvs, key=lambda x: x.name):
            try:
                nrows = len(pd.read_csv(p, encoding="utf-8"))
            except Exception as exc:
                log.detail(f"  Step 6: could not count rows in {p.name}: {exc}")
                continue
            total_s6 += nrows
            log.detail(f"  Step 6: {p.name} — {nrows} row(s)")
        log.detail(
            f"Step 6/8: Done — {len(step6_csvs)} process CSV file(s), "
            f"{total_s6} total row(s) across files  [{time.perf_counter() - t_step:.2f}s]"
        )
        if step6_csvs:
            first_proc = sorted(step6_csvs, key=lambda x: x.name)[0]
            log_csv_preview(lc, first_proc, "Step 6 CSV preview (first process file by name)")

    if log:
        log.step("Step 7/8: Generating Excel outputs...")
    t_step = time.perf_counter()
    for csv_path in step6_csvs:
        if log:
            log.detail(f"  Step 7/8: generating Excel from {csv_path.name} ...")
        run_generate_excel_outputs(
            csv_path,
            output_root,
            dispatch_date,
            use_fixed_process_number=use_fixed_process_number,
            use_fixed_numeric_process=fixed_numeric,
            log=lc,
            date_dd_mm_yyyy=date_dd_mm_yyyy,
            shift_label=shift_label,
        )
        if log:
            log.detail(f"  Step 7/8: completed Excel trio for {csv_path.name}")
    if log:
        xlsx_files = sorted(output_root.glob("*.xlsx"))
        log.detail(
            f"  Step 7/8: {len(xlsx_files)} Excel file(s) in output folder "
            f"{output_root.resolve()}"
        )
        for xf in xlsx_files[:80]:
            log.detail(f"    {xf.name}")
        if len(xlsx_files) > 80:
            log.detail(f"    ... and {len(xlsx_files) - 80} more .xlsx in this folder")
        log.detail(
            "  Step 7: each process CSV generates three Excel workbooks (Picking, Orders Details, DTF Des) "
            "in the same output folder as the CSV."
        )
        log.detail(f"Step 7/8: Done  [{time.perf_counter() - t_step:.2f}s]")

    step8_missing_logos_report: Optional[str] = None
    if phases == "excel":
        if log:
            log.detail("Excel phase complete — skipping PDF (Step 8) for this pass.")
        copy_warnings = []
        if excel_copy_dir:
            copy_warnings = _copy_outputs_to_shift_dirs(
                output_root, shift_label, None, excel_copy_dir, lc
            )
            if copy_warnings:
                step8_missing_logos_report = "\n".join(copy_warnings)
        if log:
            log.detail("----------")
            log.detail(f"Excel phase finished. Primary output: {output_root.resolve()}")
            if unmatched_path:
                try:
                    log.detail(f"Unmatched orders file: {unmatched_path.resolve()}")
                except OSError:
                    log.detail(f"Unmatched orders file: {unmatched_path}")
            if missing_logo_path:
                try:
                    log.detail(f"Missing logo orders file: {missing_logo_path.resolve()}")
                except OSError:
                    log.detail(f"Missing logo orders file: {missing_logo_path}")
            if copy_warnings:
                log.detail("Excel copy had failures (also included in Finished report):")
                for w in copy_warnings:
                    log.detail(f"  {w}")
            log.detail("----------")
        return output_root, unmatched_path, missing_logo_path, step8_missing_logos_report

    if log:
        log.step(
            "Step 8/8: starting PDF phase (Excel files are complete). "
            "The next log block may pause briefly while image folders are indexed."
        )

    step8_missing_logos_report = run_step8_pdf_generation_impl(
        step6_csvs=step6_csvs,
        workbook_path=workbook_path,
        apparel_dir=apparel_dir,
        logo_custom_single_dir=logo_custom_single_dir,
        logo_custom_double_dir=logo_custom_double_dir,
        logo_normal_dir=logo_normal_dir,
        build_image_stem_map=build_image_stem_map,
        render_one_pdf=render_one_pdf,
        csv_to_pdf=csv_to_pdf,
        load_position_code_to_draw=load_position_code_to_draw,
        format_missing_report=format_missing_report,
        collect_image_match_details=collect_image_match_details,
        format_image_match_log=format_image_match_log,
        sanitize_process_for_filename=_sanitize_process_for_filename,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        log=log,
    )

    if pdf_copy_dir or excel_copy_dir:
        copy_warnings = _copy_outputs_to_shift_dirs(
            output_root, shift_label, pdf_copy_dir, excel_copy_dir, lc
        )
        if copy_warnings:
            extra = "\n".join(copy_warnings)
            if step8_missing_logos_report:
                step8_missing_logos_report = f"{step8_missing_logos_report}\n\n{extra}"
            else:
                step8_missing_logos_report = extra
    else:
        copy_warnings = []
    if log:
        log.detail("----------")
        log.detail(f"Pipeline finished. Primary output: {output_root.resolve()}")
        if unmatched_path:
            try:
                log.detail(f"Unmatched orders file: {unmatched_path.resolve()}")
            except OSError:
                log.detail(f"Unmatched orders file: {unmatched_path}")
        if missing_logo_path:
            try:
                log.detail(f"Missing logo orders file: {missing_logo_path.resolve()}")
            except OSError:
                log.detail(f"Missing logo orders file: {missing_logo_path}")
        if step8_missing_logos_report and not (
            copy_warnings and step8_missing_logos_report == "\n".join(copy_warnings)
        ):
            log.detail("Missing-logos report was produced (see Step 8 messages above).")
        if copy_warnings:
            log.detail("PDF/Excel copy had failures (also included in Finished report):")
            for w in copy_warnings:
                log.detail(f"  {w}")
        log.detail("----------")
    return output_root, unmatched_path, missing_logo_path, step8_missing_logos_report
