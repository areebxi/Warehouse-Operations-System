from __future__ import annotations

from app.flows.label_report.app_prints import AppFailedRecord, AppPrintRecord


def _app_command_for_order(
    *,
    app_ok: AppPrintRecord | None,
    app_bad: AppFailedRecord | None,
) -> str:
    if app_ok is not None and app_ok.app_command:
        return app_ok.app_command
    if app_bad is not None and app_bad.app_command:
        return app_bad.app_command
    return ""


def _label_origin(
    *,
    status: str,
    in_batch: bool,
    app_command: str,
    shipstation_only: bool,
) -> str:
    if status == "printed_by_app":
        if app_command == "manual-print":
            return "app_manual_print"
        return "app_dtf_print"
    if status == "printed_outside_app":
        if in_batch:
            return "dtf_batch_shipped_in_shipstation"
        if shipstation_only:
            return "shipstation_only_no_dtf"
        return "printed_outside_app"
    if status == "app_failed":
        if app_command == "manual-print":
            return "app_manual_print_failed"
        return "app_dtf_print_failed"
    if status == "not_shipped" and in_batch:
        return "dtf_batch_not_shipped"
    return status
