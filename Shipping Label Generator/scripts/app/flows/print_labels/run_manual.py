from __future__ import annotations

from app.config.load import AppConfig
from app.flows.print_labels.manual_job import (
    _archive_existing_manual_job,
    _manual_job_has_outputs,
    _manual_job_id_from_groups,
    _manual_logs_job_dir,
    _manual_orders_csv_path,
    _manual_output_root,
    _write_manual_input_log,
)
from app.flows.print_labels.read_group import read_and_group_orders
from app.flows.print_labels.run_print_flow import run_print
from app.logging.jsonl import JsonlLogger
from app.util.process_numbers import process_number_sort_key
from app.util.time import local_date_ymd

def run_manual_print(cfg: AppConfig, log: JsonlLogger, *, replace_job_id: str | None = None) -> int:
    """
    Print from the fixed manual CSV under Manual Outputs/.

    Job id is derived from process numbers in the CSV (e.g. "2000-2400-2450").
    Replace runs archive existing outputs for that job id before reprinting.
    """
    date_dir = local_date_ymd()
    manual_csv = _manual_orders_csv_path(cfg)
    if not manual_csv.exists():
        log.error("manual_print_missing_orders_csv", extra={"orders_csv": str(manual_csv)})
        print(f"Manual print input not found: {manual_csv}")
        print("Create it with columns: Process Number, Order Number, Customer Name")
        return 2

    try:
        groups = read_and_group_orders(manual_csv)
    except Exception as e:
        log.error("manual_print_read_failed", extra={"orders_csv": str(manual_csv)}, exc=e)
        print(f"Manual print input could not be read: {manual_csv}")
        return 2

    if not groups:
        log.error("manual_print_no_orders", extra={"orders_csv": str(manual_csv)})
        print(f"Manual print input has no orders: {manual_csv}")
        return 2

    process_numbers = {str(g.process_number).strip() for g in groups if str(g.process_number).strip()}
    try:
        expected_job_id = _manual_job_id_from_groups(groups)
    except ValueError as e:
        log.error("manual_print_invalid_job_id", exc=e)
        print("Manual print input has no valid process numbers.")
        return 2

    if replace_job_id is not None:
        job_id = str(replace_job_id).strip()
        if not job_id:
            log.error("manual_print_invalid_replace_job_id", extra={"job_id": job_id})
            print("Replace job id is required, for example: 2000-2400-2450")
            return 2
        if job_id != expected_job_id:
            log.error(
                "manual_print_replace_job_id_mismatch",
                extra={"entered_job_id": job_id, "expected_job_id": expected_job_id},
            )
            print(f"Replace job id must match current CSV processes: {expected_job_id}")
            return 2
        _archive_existing_manual_job(
            cfg=cfg,
            date_dir=date_dir,
            job_id=job_id,
            process_numbers=process_numbers,
            log=log,
        )
        allow_existing_outputs = True
    else:
        job_id = expected_job_id
        if _manual_job_has_outputs(cfg=cfg, date_dir=date_dir, job_id=job_id):
            log.error("manual_print_job_already_exists", extra={"job_id": job_id, "date_dir": date_dir})
            print(f"Manual print outputs already exist for job: {job_id}")
            print("Use option 2 (Replace existing job) to archive and reprint.")
            return 2
        allow_existing_outputs = False

    log.info(
        "manual_print_selected_job",
        extra={
            "job_id": job_id,
            "orders_csv": str(manual_csv),
            "replace": bool(replace_job_id),
            "process_numbers": sorted(process_numbers, key=process_number_sort_key),
        },
    )
    print(f"Manual Print job id: {job_id}")
    _write_manual_input_log(
        cfg=cfg,
        date_dir=date_dir,
        job_id=job_id,
        manual_csv=manual_csv,
        groups=groups,
        replace=bool(replace_job_id),
    )

    manual_output_root = _manual_output_root(cfg)
    manual_log = JsonlLogger.for_manual_print_run(cfg, job_id=job_id, date_dir=date_dir)
    manual_job_log_dir = _manual_logs_job_dir(cfg=cfg, date_dir=date_dir, job_id=job_id)

    return run_print(
        cfg,
        log,
        orders_csv_override=manual_csv,
        combined_name_override=job_id,
        labels_base_dir_override=manual_output_root / "Labels" / date_dir,
        combined_pdfs_dir_override=manual_output_root / "Combined_PDFs" / date_dir,
        process_pdfs_base_dir_override=manual_output_root / "Process_PDFs" / date_dir / "Manual",
        failures_dir_override=manual_job_log_dir,
        run_log_override=manual_log,
        command_name="manual-print",
        allow_existing_outputs=allow_existing_outputs,
    )

