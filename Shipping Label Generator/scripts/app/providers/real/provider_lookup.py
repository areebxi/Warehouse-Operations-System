"""Order lookup that also finds shipped orders by order number."""
from __future__ import annotations

from typing import Any

from scripts.app.models.order import Order
from scripts.app.providers.real.provider import ProviderParseError


def _orders_from_payload(provider: Any, data: Any) -> list[Order]:
    if not isinstance(data, dict):
        raise ProviderParseError(
            method="GET",
            url=f"{provider._base_url}/orders",
            status=200,
            message="Unexpected orders response shape: expected object with key 'orders'",
            body_snippet=str(data)[:2000],
            expected="object with 'orders' list",
        )
    items = data.get("orders")
    if items is None:
        items = []
    if not isinstance(items, list):
        raise ProviderParseError(
            method="GET",
            url=f"{provider._base_url}/orders",
            status=200,
            message="Unexpected orders response shape: expected list at 'orders'",
            body_snippet=str({k: type(v).__name__ for k, v in list(data.items())[:50]})[:2000],
            expected="orders: list",
        )

    out: list[Order] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        oid = provider._get(it, "orderId", "order_id", "id")
        on = provider._get(it, "orderNumber", "order_number", "number")
        if oid is None or on is None:
            continue
        ship_to = it.get("shipTo") if isinstance(it.get("shipTo"), dict) else {}
        customer_name = provider._get(it, "customerName", "customer_name")
        if not customer_name and isinstance(ship_to, dict):
            customer_name = ship_to.get("name")
        ship_from = it.get("shipFrom") if isinstance(it.get("shipFrom"), dict) else {}
        ship_from_name = ship_from.get("name") if isinstance(ship_from, dict) else None
        items_list = it.get("items")
        status = provider._get(it, "orderStatus", "order_status")
        out.append(
            Order(
                orderId=provider._as_int(oid, field="orderId"),
                orderNumber=provider._as_str(on),
                carrierCode=provider._get(it, "carrierCode", "carrier_code"),
                serviceCode=provider._get(it, "serviceCode", "service_code"),
                packageCode=provider._get(it, "packageCode", "package_code"),
                requestedShippingService=provider._get(it, "requestedShippingService", "requested_shipping_service"),
                customerName=str(customer_name).strip() if customer_name else None,
                shipFromName=str(ship_from_name).strip() if ship_from_name else None,
                orderStatus=str(status).strip() if status is not None else None,
                items=list(items_list) if isinstance(items_list, list) else [],
            )
        )
    return out


async def lookup_orders(provider: Any, order_number: str) -> list[Order]:
    """Default order list, then orderStatus=shipped when that list is empty."""
    order_number = str(order_number).strip()
    if not order_number:
        return []

    data = await provider._request_json(
        method="GET",
        path="/orders",
        params={"orderNumber": order_number, "pageSize": 100},
    )
    found = _orders_from_payload(provider, data)
    if found:
        return found
    shipped = await provider._request_json(
        method="GET",
        path="/orders",
        params={"orderNumber": order_number, "pageSize": 100, "orderStatus": "shipped"},
    )
    return _orders_from_payload(provider, shipped)
