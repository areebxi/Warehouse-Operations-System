from __future__ import annotations

from app.flows.label_report.app_prints import AppFailedRecord, AppPrintRecord
from app.flows.label_report.report_models import ReportRow
from app.flows.label_report.report_origin import _app_command_for_order, _label_origin
from app.flows.label_report.shipstation_shipments import ShipStationShipmentRow


def _build_report_rows(
    *,
    batch_orders: dict[str, tuple[str, str]],
    app_success: dict[str, AppPrintRecord],
    app_failed: dict[str, AppFailedRecord],
    ss_by_order: dict[str, ShipStationShipmentRow],
) -> list[ReportRow]:
    all_orders = set(batch_orders.keys()) | set(app_success.keys()) | set(app_failed.keys()) | set(ss_by_order.keys())
    rows: list[ReportRow] = []

    for on in sorted(all_orders):
        proc, cust = batch_orders.get(on, ("", ""))
        app_ok = app_success.get(on)
        app_bad = app_failed.get(on)
        ss = ss_by_order.get(on)
        in_batch = on in batch_orders
        app_command = _app_command_for_order(app_ok=app_ok, app_bad=app_bad)

        if app_ok is not None:
            proc = proc or app_ok.process_number
            cust = cust or app_ok.customer_name
            status = "printed_by_app"
            shipment_id = app_ok.shipment_id or (str(ss.shipment_id) if ss else "")
            tracking = app_ok.tracking_number or (ss.tracking_number if ss else "")
            carrier = app_ok.carrier_code or (ss.carrier_code if ss else "")
            service = app_ok.service_code or (ss.service_code if ss else "")
            package = app_ok.package_code or (ss.package_code if ss else "")
            label_source = app_ok.label_source
            fail_reason = ""
            create_date = ss.create_date if ss else ""
        elif ss is not None:
            status = "printed_outside_app"
            shipment_id = str(ss.shipment_id)
            tracking = ss.tracking_number
            carrier = ss.carrier_code
            service = ss.service_code
            package = ss.package_code
            label_source = ""
            fail_reason = ""
            create_date = ss.create_date
        elif app_bad is not None:
            proc = proc or app_bad.process_number
            cust = cust or app_bad.customer_name
            status = "app_failed"
            shipment_id = ""
            tracking = ""
            carrier = ""
            service = ""
            package = ""
            label_source = ""
            fail_reason = app_bad.reason
            create_date = ""
        else:
            status = "not_shipped"
            shipment_id = ""
            tracking = ""
            carrier = ""
            service = ""
            package = ""
            label_source = ""
            fail_reason = ""
            fail_reason = ""
            create_date = ""

        shipstation_only = ss is not None and app_ok is None and not in_batch
        label_origin = _label_origin(
            status=status,
            in_batch=in_batch,
            app_command=app_command,
            shipstation_only=shipstation_only,
        )

        rows.append(
            ReportRow(
                order_number=on,
                process_number=proc,
                customer_name=cust,
                status=status,
                label_origin=label_origin,
                in_todays_dtf_batch=in_batch,
                app_command=app_command,
                shipstation_only=shipstation_only,
                shipment_id=shipment_id,
                tracking_number=tracking,
                carrier_code=carrier,
                service_code=service,
                package_code=package,
                app_label_source=label_source,
                app_failure_reason=fail_reason,
                shipment_create_date=create_date,
            )
        )
    return rows
