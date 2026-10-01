from __future__ import annotations

from dataclasses import dataclass

REPORT_HEADER = [
    "Order Number",
    "Process Number",
    "Customer Name",
    "Status",
    "Label Origin",
    "In Today's DTF Batch",
    "App Command",
    "ShipStation Only",
    "ShipStation Shipment ID",
    "Tracking Number",
    "Carrier",
    "Service",
    "Package",
    "App Label Source",
    "App Failure Reason",
    "Shipment Create Date",
]


@dataclass(frozen=True)
class ReportRow:
    order_number: str
    process_number: str
    customer_name: str
    status: str
    label_origin: str
    in_todays_dtf_batch: bool
    app_command: str
    shipstation_only: bool
    shipment_id: str
    tracking_number: str
    carrier_code: str
    service_code: str
    package_code: str
    app_label_source: str
    app_failure_reason: str
    shipment_create_date: str


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"
