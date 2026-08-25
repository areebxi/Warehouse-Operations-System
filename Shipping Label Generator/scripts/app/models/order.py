from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Order:
    orderId: int
    orderNumber: str

    carrierCode: str | None = None
    serviceCode: str | None = None
    packageCode: str | None = None

    requestedShippingService: str | None = None
    customerName: str | None = None
    shipFromName: str | None = None
    orderStatus: str | None = None
    items: list[dict[str, Any]] = field(default_factory=list)
