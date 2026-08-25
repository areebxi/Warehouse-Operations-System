from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Shipment:
    shipmentId: int
    voided: bool
    orderId: int

    carrierCode: str | None = None
    serviceCode: str | None = None
    packageCode: str | None = None
