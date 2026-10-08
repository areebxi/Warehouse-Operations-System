from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, Any, Awaitable, Callable, TypeVar

from scripts.app.config.load import AppConfig
from scripts.app.flows.print_labels.failures import FailureRow
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.models.label import Label
from scripts.app.models.order import Order
from scripts.app.providers.base import Provider
from scripts.app.rules.service_map import carrier_key, map_service_code
from scripts.app.rules.order_status import cancelled_order_reason, is_order_cancelled
from scripts.app.rules.selection import select_order_candidate, select_shipments
from scripts.app.rules.weights import normalize_weight
from scripts.app.util.retries import call_with_retries

if TYPE_CHECKING:
    from scripts.app.logging.orders_audit import OrderAuditLogger

T = TypeVar("T")


async def _timed_call_with_retries(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    op: str,
    op_kind: str,
    fn: Callable[[], Awaitable[T]],
    extra: dict[str, Any],
) -> T:
    """Wraps call_with_retries and logs elapsed_ms per op (includes retries)."""
    t0 = monotonic()
    try:
        out = await call_with_retries(cfg=cfg, log=log, op=op, op_kind=op_kind, fn=fn, extra=extra)
        log.info(
            "provider_op_timing",
            extra={**extra, "op": op, "elapsed_ms": round((monotonic() - t0) * 1000.0, 2), "ok": True},
        )
        return out
    except Exception:
        log.info(
            "provider_op_timing",
            extra={**extra, "op": op, "elapsed_ms": round((monotonic() - t0) * 1000.0, 2), "ok": False},
        )
        raise


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


def _is_test_mode() -> bool:
    """
    Guardrail to prevent mock/test data leaking into production runs.

    Enable by setting SHIPPING_TEST_MODE=1 (or true/yes/on).
    """
    v = (os.getenv("SHIPPING_TEST_MODE") or "").strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _extract_total_weight_lb(order: Order) -> float | None:
    total_lb = 0.0
    seen = False
    for it in order.items or []:
        if not isinstance(it, dict):
            continue
        w = it.get("weight")
        u = it.get("weightUnit")
        q = it.get("quantity", 1) or 1
        if w is None or u is None:
            continue
        try:
            wf = float(w)
            qf = float(q)
        except Exception:
            continue
        unit = str(u).strip().lower()
        if unit in ("lb", "lbs", "pound", "pounds"):
            total_lb += wf * qf
            seen = True
        elif unit in ("oz", "ounce", "ounces"):
            total_lb += (wf / 16.0) * qf
            seen = True
    return total_lb if seen else None


def _pick_order_candidate_fast(*, candidates: list[Order], has_active_shipments: dict[int, bool]) -> Order | None:
    """
    Candidate selection optimization:
    - If ShipStation returns exactly one candidate order, skip the extra per-candidate
      /shipments(active, pageSize=1) call and just use it.
    - If there are multiple candidates, preserve the existing "awaiting shipment" selection rules.
    - Cancelled channel orders are never selected.
    """
    if not candidates:
        return None
    shippable = [o for o in candidates if not is_order_cancelled(o)]
    if not shippable:
        return None
    if len(shippable) == 1:
        return shippable[0]
    return select_order_candidate(candidates=shippable, has_active_shipments=has_active_shipments)


def _resolve_fields(
    *,
    cfg: AppConfig,
    order: Order,
    shipment_fields: dict[str, str | None],
    process_number: str = "",
) -> tuple[str, str, str]:
    provider_cfg = cfg.raw.get("provider") or {}
    provider_cfg = provider_cfg if isinstance(provider_cfg, dict) else {}
    default_carrier = str(provider_cfg.get("default_carrier") or "").strip()
    default_package = str(provider_cfg.get("default_package") or "").strip()

    carrier = shipment_fields.get("carrierCode") or order.carrierCode or (default_carrier or None)
    package = shipment_fields.get("packageCode") or order.packageCode or (default_package or None) or "package"
    service = shipment_fields.get("serviceCode") or order.serviceCode

    if not _is_test_mode():
        if carrier and str(carrier).strip().lower().startswith("mock_"):
            raise ServiceCodeResolutionError(
                order_number=str(order.orderNumber),
                process_number=str(process_number or ""),
                carrier_code=str(carrier),
                requested_shipping_service=order.requestedShippingService,
                carrier_key=carrier_key(str(carrier)),
                order_service_code=order.serviceCode,
                shipment_service_code=shipment_fields.get("serviceCode"),
                message="mock carrierCode detected in non-test mode (set SHIPPING_TEST_MODE=1 to allow)",
            )
        if order.requestedShippingService and str(order.requestedShippingService).strip().lower().startswith("mock_"):
            ckey = carrier_key(str(carrier)) if carrier else None
            raise ServiceCodeResolutionError(
                order_number=str(order.orderNumber),
                process_number=str(process_number or ""),
                carrier_code=str(carrier) if carrier else None,
                requested_shipping_service=order.requestedShippingService,
                carrier_key=ckey,
                order_service_code=order.serviceCode,
                shipment_service_code=shipment_fields.get("serviceCode"),
                message="mock requestedShippingService detected in non-test mode (set SHIPPING_TEST_MODE=1 to allow)",
            )

    if not carrier:
        raise ServiceCodeResolutionError(
            order_number=str(order.orderNumber),
            process_number=str(process_number or ""),
            carrier_code=None,
            requested_shipping_service=order.requestedShippingService,
            carrier_key=None,
            order_service_code=order.serviceCode,
            shipment_service_code=shipment_fields.get("serviceCode"),
            message=(
                "missing carrierCode; "
                f"order.carrierCode={order.carrierCode!r}, shipment.carrierCode={shipment_fields.get('carrierCode')!r}, "
                f"provider.default_carrier={default_carrier!r}"
            ),
        )

    if not service:
        service = map_service_code(
            cfg_raw=cfg.raw,
            carrier=str(carrier),
            requested_shipping_service=order.requestedShippingService,
        )

    if not service:
        ckey = carrier_key(str(carrier))
        raise ServiceCodeResolutionError(
            order_number=str(order.orderNumber),
            process_number=str(process_number or ""),
            carrier_code=str(carrier),
            requested_shipping_service=order.requestedShippingService,
            carrier_key=ckey,
            order_service_code=order.serviceCode,
            shipment_service_code=shipment_fields.get("serviceCode"),
            message="no matching service_map entry and no serviceCode on order/shipment",
        )

    return str(carrier), str(service), str(package)


def _audit_step(
    audit: OrderAuditLogger | None,
    *,
    outcome: str,
    order_number: str,
    process_number: str,
    customer_name: str = "",
    **fields: Any,
) -> None:
    if audit is None:
        return
    audit.record(
        outcome=outcome,
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        **fields,
    )


def _audit_fail(
    audit: OrderAuditLogger | None,
    *,
    order_number: str,
    process_number: str,
    customer_name: str,
    reason: str,
    shipstation_order_id: str = "",
    **fields: Any,
) -> None:
    if audit is None:
        return
    audit.record(
        outcome="print_failed",
        order_number=order_number,
        process_number=process_number,
        customer_name=customer_name,
        reason=reason,
        shipstation_order_id=shipstation_order_id,
        **fields,
    )


async def process_one_order(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    provider: Provider,
    process_number: str,
    order_number: str,
    customer_name_from_input: str = "",
    labels_dir: Path,
    audit: OrderAuditLogger | None = None,
) -> OrderResult:
    customer_name_from_input = str(customer_name_from_input or "")
    customer_name: str = customer_name_from_input
    from scripts.app.pdf.report_pages import make_label_error_page_pdf

    def _write_error_pdf(*, reason: str, customer: str) -> Path:
        labels_dir.mkdir(parents=True, exist_ok=True)
        out_path = labels_dir / f"{order_number}__ERROR.pdf"
        out_path.write_bytes(
            make_label_error_page_pdf(
                process_number=process_number,
                order_number=order_number,
                customer_name=customer,
                error_reason=reason,
            )
        )
        return out_path

    if audit is not None:
        audit.record(
            outcome="print_start",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name_from_input,
        )

    try:
        candidates = await _timed_call_with_retries(
            cfg=cfg,
            log=log,
            op="lookup_orders",
            op_kind="request",
            fn=lambda: provider.lookup_orders(order_number),
            extra={"order_number": order_number, "process_number": process_number},
        )
        _audit_step(
            audit,
            outcome="print_lookup",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            candidate_count=int(len(candidates)),
        )
        if not candidates:
            reason = "order not found"
            _audit_fail(
                audit,
                order_number=order_number,
                process_number=process_number,
                customer_name=customer_name,
                reason=reason,
            )
            return OrderResult(
                order_number=order_number,
                process_number=process_number,
                label_pdf_path=_write_error_pdf(reason=reason, customer=customer_name),
                failure=FailureRow(customer_name, process_number, order_number, "", reason),
                ship_from=None,
            )

        if all(is_order_cancelled(o) for o in candidates):
            reason = cancelled_order_reason(orders=candidates)
            cust = customer_name_from_input or (candidates[0].customerName or "")
            _audit_fail(
                audit,
                order_number=order_number,
                process_number=process_number,
                customer_name=cust,
                reason=reason,
                shipstation_order_id=str(candidates[0].orderId),
            )
            return OrderResult(
                order_number=order_number,
                process_number=process_number,
                label_pdf_path=_write_error_pdf(reason=reason, customer=cust),
                failure=FailureRow(
                    cust,
                    process_number,
                    order_number,
                    str(candidates[0].orderId),
                    reason,
                ),
                ship_from=None,
            )

        shippable_candidates = [o for o in candidates if not is_order_cancelled(o)]

        has_active: dict[int, bool] = {}
        if len(shippable_candidates) > 1:
            for o in shippable_candidates:
                sh = await _timed_call_with_retries(
                    cfg=cfg,
                    log=log,
                    op="list_shipments",
                    op_kind="request",
                    fn=lambda o=o: provider.list_shipments(o.orderId, include_voided=False, page_size=1),
                    extra={"order_number": order_number, "process_number": process_number, "orderId": o.orderId, "include_voided": False},
                )
                has_active[o.orderId] = len(sh) > 0

        selected = _pick_order_candidate_fast(candidates=shippable_candidates, has_active_shipments=has_active)
        if selected is None:
            reason = "no processable order candidate (all have active shipments)"
            cust = customer_name_from_input or (candidates[0].customerName or "")
            _audit_fail(
                audit,
                order_number=order_number,
                process_number=process_number,
                customer_name=cust,
                reason=reason,
                shipstation_order_id=str(candidates[0].orderId),
            )
            return OrderResult(
                order_number=order_number,
                process_number=process_number,
                label_pdf_path=_write_error_pdf(reason=reason, customer=cust),
                failure=FailureRow(
                    cust,
                    process_number,
                    order_number,
                    str(candidates[0].orderId),
                    reason,
                ),
                ship_from=None,
            )

        customer_name = selected.customerName or customer_name or ""
        _audit_step(
            audit,
            outcome="print_order_selected",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            shipstation_order_id=str(selected.orderId),
            requested_shipping_service=selected.requestedShippingService or "",
            candidate_count=int(len(candidates)),
            shippable_candidate_count=int(len(shippable_candidates)),
        )

        # Amendments: if ShipStation order has Amendments tag, do not create/reuse a label.
        from scripts.app.flows.amendments.shipstation_tags import selected_order_has_amendments
        from scripts.app.flows.amendments.tags import amendments_skip_reason

        try:
            blocked, tag_info = await selected_order_has_amendments(
                provider,
                order_id=int(selected.orderId),
                order_number=order_number,
            )
        except Exception as e:
            log.warning(
                "print_amendments_check_failed",
                extra={
                    "order_number": order_number,
                    "process_number": process_number,
                    "orderId": selected.orderId,
                },
                exc=e,
            )
            blocked, tag_info = False, None

        if blocked:
            reason = amendments_skip_reason()
            cust = customer_name_from_input or customer_name or (tag_info.customer_name if tag_info else "")
            log.info(
                "print_skipped_amendments_tag",
                extra={
                    "order_number": order_number,
                    "process_number": process_number,
                    "orderId": selected.orderId,
                    "tag_names": list(tag_info.tag_names) if tag_info else [],
                    "tag_count": int(tag_info.tag_count) if tag_info else 0,
                },
            )
            _audit_fail(
                audit,
                order_number=order_number,
                process_number=process_number,
                customer_name=cust,
                reason=reason,
                shipstation_order_id=str(selected.orderId),
                tag_names=list(tag_info.tag_names) if tag_info else [],
            )
            return OrderResult(
                order_number=order_number,
                process_number=process_number,
                label_pdf_path=_write_error_pdf(reason=reason, customer=cust),
                failure=FailureRow(cust, process_number, order_number, str(selected.orderId), reason),
                ship_from=None,
            )

        all_shipments = await _timed_call_with_retries(
            cfg=cfg,
            log=log,
            op="list_shipments",
            op_kind="request",
            fn=lambda: provider.list_shipments(selected.orderId, include_voided=True, page_size=100),
            extra={"order_number": order_number, "process_number": process_number, "orderId": selected.orderId, "include_voided": True},
        )
        sel_ship = select_shipments(all_shipments)
        _audit_step(
            audit,
            outcome="print_shipments_loaded",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            shipstation_order_id=str(selected.orderId),
            shipment_count=int(len(sel_ship.shipments)),
            used_voided=bool(sel_ship.used_voided),
        )
        if sel_ship.used_voided and sel_ship.shipments:
            log.warning(
                "print_using_voided_shipments",
                extra={"order_number": order_number, "process_number": process_number, "orderId": selected.orderId},
            )
            _audit_step(
                audit,
                outcome="print_using_voided_shipments",
                order_number=order_number,
                process_number=process_number,
                customer_name=customer_name,
                shipstation_order_id=str(selected.orderId),
                shipment_id=str(sel_ship.shipments[0].shipmentId),
            )

        label: Label | None = None
        shipment_fields: dict[str, str | None] = {"carrierCode": None, "serviceCode": None, "packageCode": None}

        if sel_ship.shipments:
            s0 = sel_ship.shipments[0]
            shipment_fields = {"carrierCode": s0.carrierCode, "serviceCode": s0.serviceCode, "packageCode": s0.packageCode}

        if sel_ship.shipments and not sel_ship.used_voided:
            try:
                fetched = await _timed_call_with_retries(
                    cfg=cfg,
                    log=log,
                    op="fetch_label",
                    op_kind="label",
                    fn=lambda: provider.fetch_label(sel_ship.shipments[0].shipmentId),
                    extra={
                        "order_number": order_number,
                        "process_number": process_number,
                        "orderId": selected.orderId,
                        "shipmentId": sel_ship.shipments[0].shipmentId,
                    },
                )
                if fetched and fetched.labelData:
                    label = fetched
                    _audit_step(
                        audit,
                        outcome="print_label_reused",
                        order_number=order_number,
                        process_number=process_number,
                        customer_name=customer_name,
                        shipstation_order_id=str(selected.orderId),
                        shipment_id=str(sel_ship.shipments[0].shipmentId),
                        carrier_code=shipment_fields.get("carrierCode") or "",
                        service_code=shipment_fields.get("serviceCode") or "",
                        package_code=shipment_fields.get("packageCode") or "",
                    )
            except Exception:
                log.warning(
                    "print_fetch_label_failed",
                    extra={"order_number": order_number, "process_number": process_number},
                )
                _audit_step(
                    audit,
                    outcome="print_label_fetch_failed",
                    order_number=order_number,
                    process_number=process_number,
                    customer_name=customer_name,
                    shipstation_order_id=str(selected.orderId),
                    shipment_id=str(sel_ship.shipments[0].shipmentId),
                )

        reused_label = label is not None

        carrier, service, package = _resolve_fields(
            cfg=cfg, order=selected, shipment_fields=shipment_fields, process_number=process_number
        )
        _audit_step(
            audit,
            outcome="print_service_resolved",
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            shipstation_order_id=str(selected.orderId),
            carrier_code=carrier,
            service_code=service,
            package_code=package,
            requested_shipping_service=selected.requestedShippingService or "",
        )
        log.info(
            "service_mapping_resolved",
            extra={
                "order_number": order_number,
                "process_number": process_number,
                "carrierCode": carrier,
                "requestedShippingService": selected.requestedShippingService,
                "serviceCode": service,
                "packageCode": package,
            },
        )

        if label is None:
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
            label = await _timed_call_with_retries(
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

        from scripts.app.pdf.label_decode import write_label_pdf

        out_path = labels_dir / f"{order_number}.pdf"
        write_label_pdf(out_path, label_data_b64=label.labelData)
        shipment_id = ""
        tracking_number = ""
        if sel_ship.shipments:
            shipment_id = str(sel_ship.shipments[0].shipmentId)
        if label.trackingNumber:
            tracking_number = str(label.trackingNumber)
        if audit is not None:
            audit.record(
                outcome="print_success",
                order_number=order_number,
                process_number=process_number,
                customer_name=customer_name,
                shipstation_order_id=str(selected.orderId),
                carrier_code=carrier,
                service_code=service,
                package_code=package,
                requested_shipping_service=selected.requestedShippingService or "",
                label_source="reused" if reused_label else "created",
                shipment_id=shipment_id,
                tracking_number=tracking_number,
                label_pdf=str(out_path),
            )
        return OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=out_path,
            failure=None,
            ship_from=selected.shipFromName,
        )

    except ServiceCodeResolutionError as e:
        log.error(
            "print_order_failed",
            extra={"order_number": order_number, "process_number": process_number},
            exc=e,
        )
        reason = str(e)
        if customer_name_from_input:
            customer_name = customer_name_from_input
        order_id = ""
        package_code = ""
        try:
            if "selected" in locals() and selected is not None:
                order_id = str(getattr(selected, "orderId", "") or "")
                customer_name = customer_name or str(getattr(selected, "customerName", "") or "")
            if "shipment_fields" in locals() and isinstance(shipment_fields, dict):
                package_code = str(shipment_fields.get("packageCode") or "")
        except Exception:
            pass
        _audit_fail(
            audit,
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            reason=reason,
            shipstation_order_id=order_id,
            carrier_code=e.carrier_code or "",
            service_code=e.order_service_code or e.shipment_service_code or "",
            package_code=package_code,
            requested_shipping_service=e.requested_shipping_service or "",
            carrier_key=e.carrier_key or "",
        )
        return OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=_write_error_pdf(reason=reason, customer=customer_name),
            failure=FailureRow(customer_name, process_number, order_number, order_id, reason),
            ship_from=None,
        )
    except Exception as e:
        log.error(
            "print_order_failed",
            extra={"order_number": order_number, "process_number": process_number},
            exc=e,
        )
        reason = str(e)
        # Prefer the name from the converted input file (Excel) for error artifacts.
        if customer_name_from_input:
            customer_name = customer_name_from_input
        order_id = ""
        fail_fields: dict[str, Any] = {}
        try:
            if "selected" in locals() and selected is not None:
                order_id = str(getattr(selected, "orderId", "") or "")
            if "carrier" in locals():
                fail_fields["carrier_code"] = carrier
            if "service" in locals():
                fail_fields["service_code"] = service
            if "package" in locals():
                fail_fields["package_code"] = package
            if "selected" in locals() and selected is not None:
                fail_fields["requested_shipping_service"] = selected.requestedShippingService or ""
        except Exception:
            order_id = ""
        _audit_fail(
            audit,
            order_number=order_number,
            process_number=process_number,
            customer_name=customer_name,
            reason=reason,
            shipstation_order_id=order_id,
            **fail_fields,
        )
        return OrderResult(
            order_number=order_number,
            process_number=process_number,
            label_pdf_path=_write_error_pdf(reason=reason, customer=customer_name),
            failure=FailureRow(customer_name, process_number, order_number, order_id, reason),
            ship_from=None,
        )

