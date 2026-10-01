"""Print-labels entrypoints — stable façade."""

from __future__ import annotations

from app.flows.print_labels.combined_sanity import (
    _SUMMARY_PROCESS_HINT_RE,
    _SUMMARY_PROCESS_MARKER_RE,
    _extract_process_number_from_summary_page,
    _sanity_check_combined_pdf,
)
from app.flows.print_labels.manual_job import (
    _archive_existing_manual_job,
    _manual_job_has_outputs,
    _manual_job_id_from_groups,
    _manual_job_paths,
    _manual_logs_job_dir,
    _manual_orders_csv_path,
    _manual_output_root,
    _write_manual_input_log,
)
from app.flows.print_labels.paths import (
    _PROCESS_PDF_RE,
    _combined_pdf_name_for_run,
    _combined_pdf_name_from_orders_dir,
    _orders_csv_path,
    _path_from_repo,
    _process_number_key_from_pdf_path,
    _repo_root,
)
from app.flows.print_labels.process_group import (
    _run_process_group,
    _write_summary_bucket_pdf,
)
from app.flows.print_labels.run_manual import run_manual_print
from app.flows.print_labels.run_print_flow import run_print

__all__ = [
    "run_print",
    "run_manual_print",
]
