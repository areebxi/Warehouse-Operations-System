from __future__ import annotations

from dataclasses import dataclass

from scripts.app.models.order import Order
from scripts.app.models.shipment import Shipment
from scripts.app.rules.order_status import is_order_cancelled


@dataclass(frozen=True)
class SelectedShipments:
    shipments: list[Shipment]
    used_voided: bool


def select_order_candidate(*, candidates: list[Order], has_active_shipments: dict[int, bool]) -> Order | None:
    if not candidates:
        return None

    awaiting = [
        o for o in candidates if not has_active_shipments.get(o.orderId, False) and not is_order_cancelled(o)
    ]
    if awaiting:
        return sorted(awaiting, key=lambda o: o.orderId, reverse=True)[0]

    return None


def select_shipments(shipments: list[Shipment]) -> SelectedShipments:
    shipments = sorted(shipments, key=lambda s: s.shipmentId, reverse=True)
    active = [s for s in shipments if not s.voided]
    voided = [s for s in shipments if s.voided]
    if active:
        return SelectedShipments(shipments=active, used_voided=False)
    return SelectedShipments(shipments=voided, used_voided=True)

