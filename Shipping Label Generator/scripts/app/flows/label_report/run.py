"""Label report entrypoints — stable façade."""

from __future__ import annotations

from app.flows.label_report.report_batch import (
    _batch_orders,
    _orders_csv_path,
    _repo_root,
    _reports_dir,
)
from app.flows.label_report.report_build import _build_report_rows
from app.flows.label_report.report_models import REPORT_HEADER, ReportRow, _yes_no
from app.flows.label_report.report_origin import _app_command_for_order, _label_origin
from app.flows.label_report.report_run_async import _run_async, run_label_report
from app.flows.label_report.report_write import (
    _print_console_summary,
    _write_csv,
    _write_summary_txt,
)

__all__ = [
    "REPORT_HEADER",
    "ReportRow",
    "_app_command_for_order",
    "_batch_orders",
    "_build_report_rows",
    "_label_origin",
    "_orders_csv_path",
    "_print_console_summary",
    "_repo_root",
    "_reports_dir",
    "_run_async",
    "_write_csv",
    "_write_summary_txt",
    "_yes_no",
    "run_label_report",
]
