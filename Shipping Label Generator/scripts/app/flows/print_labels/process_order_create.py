"""Create a label only when the order is not already shipped."""
from __future__ import annotations

import base64
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from scripts.app.config.load import AppConfig
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.models.label import Label
from scripts.app.models.order import Order
from scripts.app.providers.base import Provider
from scripts.app.rules.selection import may_create_label

if TYPE_CHECKING:
    from scripts.app.logging.orders_audit import OrderAuditLogger

SHIPPED_LABEL_MISSING = "shipped order has no downloadable label"


def local_saved_label(cfg: AppConfig, *, process_number: str, order_number: str) -> Label | None:
    """ShipStation V1 list-shipments returns labelData null and has no reprint route.

    Use the label PDF this app already saved for that order number.
    """
    root = Path(str(cfg.raw["paths"]["output_dir"])) / "Labels"
    name = f"{order_number}.pdf"
    if not root.is_dir():
        return None
    hits = [p for p in root.rglob(name) if p.is_file()]
    folder = f"process_{process_number}"
    found = next((p for p in hits if p.parent.name == folder), None) or (hits[0] if hits else None)
    if found is None:
        return None
    data = found.read_bytes()
    if not data.startswith(b"%PDF"):
        return None
    return Label(labelData=base64.b64encode(data).decode("ascii"), trackingNumber=None)


async def create_label_if_allowed(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    provider: Provider,
    process_number: str,
    order_number: str,
    customer_name: str,
    selected: Order,
    carrier: str,
    service: str,
    package: str,
    audit: OrderAuditLogger | None,
) -> Label | str:
    """Return a new label, or a failure reason when the order is already shipped."""
    if not may_create_label(selected):
        saved = local_saved_label(cfg, process_number=process_number, order_number=order_number)
        if saved is not None:
            return saved
        return SHIPPED_LABEL_MISSING

    from scripts.app.flows.print_labels.process_order import (
        _audit_step,
        _extract_total_weight_lb,
        _timed_call_with_retries,
    )
    from scripts.app.rules.weights import normalize_weight

    weight_lb = _extract_total_weight_lb(selected)
    weight_val: float | None = None
    weight_unit: str | None = None
    if weight_lb is not None:
        weight_val, weight_unit = normalize_weight(cfg_raw=cfg.raw, carrier_code=carrier, weight=weight_lb)

    _audit_step(
        audit,
        outcome="print_label_creating",
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        shipstation_order_id=str(selected.orderId),
        carrier_code=carrier,
        service_code=service,
        package_code=package,
        requested_shipping_service=selected.requestedShippingService or "",
        weight=weight_val,
        weight_unit=weight_unit,
    )
    label: Label = await _timed_call_with_retries(
        cfg=cfg,
        log=log,
        op="create_label",
        op_kind="label",
        fn=lambda: provider.create_label(
            order=selected,
            carrier_code=carrier,
            service_code=service,
            package_code=package,
            ship_date=date.today().isoformat(),
            weight=weight_val,
            weight_unit=weight_unit,
            customer_reference=None,
        ),
        extra={"order_number": order_number, "process_number": process_number, "orderId": selected.orderId},
    )
    return label
