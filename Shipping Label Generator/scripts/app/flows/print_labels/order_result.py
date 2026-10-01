from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.flows.print_labels.failures import FailureRow


@dataclass(frozen=True)
class OrderResult:
    order_number: str
    process_number: str
    label_pdf_path: Path
    failure: FailureRow | None
    ship_from: str | None = None


@dataclass(frozen=True)
class ServiceCodeResolutionError(ValueError):
    """
    Raised when we cannot determine a ShipStation serviceCode for an order.

    This is intentionally a ValueError so existing failure handling keeps working.
    """

    order_number: str
    process_number: str
    carrier_code: str | None
    requested_shipping_service: str | None
    carrier_key: str | None
    order_service_code: str | None
    shipment_service_code: str | None
    message: str

    def __str__(self) -> str:
        # Keep a single-line reason that is safe for CSV + PDFs.
        return (
            "serviceCode could not be resolved"
            f" (order_number={self.order_number!r}, process_number={self.process_number!r},"
            f" carrierCode={self.carrier_code!r}, carrier_key={self.carrier_key!r},"
            f" requestedShippingService={self.requested_shipping_service!r},"
            f" order.serviceCode={self.order_service_code!r}, shipment.serviceCode={self.shipment_service_code!r};"
            f" {self.message})"
        )
