from __future__ import annotations

import json

from app.models.order import Order
from app.models.shipment import Shipment
from app.providers.real.errors import ProviderParseError


class ProviderOrdersMixin:
    async def lookup_orders(self, order_number: str) -> list[Order]:
        order_number = str(order_number).strip()
        if not order_number:
            return []

        data = await self._request_json(
            method="GET",
            path="/orders",
            params={"orderNumber": order_number, "pageSize": 100},
        )

        if not isinstance(data, dict):
            raise ProviderParseError(
                method="GET",
                url=f"{self._base_url}/orders",
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
                url=f"{self._base_url}/orders",
                status=200,
                message="Unexpected orders response shape: expected list at 'orders'",
                body_snippet=json.dumps(
                    {k: type(v).__name__ for k, v in list(data.items())[:50]}, ensure_ascii=False
                )[:2000],
                expected="orders: list",
            )

        out: list[Order] = []
        for it in items:
            if not isinstance(it, dict):
                continue

            oid = self._get(it, "orderId", "order_id", "id")
            on = self._get(it, "orderNumber", "order_number", "number")
            if oid is None or on is None:
                continue

            ship_to = it.get("shipTo") if isinstance(it.get("shipTo"), dict) else {}
            customer_name = self._get(it, "customerName", "customer_name")
            if not customer_name and isinstance(ship_to, dict):
                customer_name = ship_to.get("name")

            ship_from = it.get("shipFrom") if isinstance(it.get("shipFrom"), dict) else {}
            ship_from_name = None
            if isinstance(ship_from, dict):
                ship_from_name = ship_from.get("name")

            items_list = it.get("items")
            out.append(
                Order(
                    orderId=self._as_int(oid, field="orderId"),
                    orderNumber=self._as_str(on),
                    carrierCode=self._get(it, "carrierCode", "carrier_code"),
                    serviceCode=self._get(it, "serviceCode", "service_code"),
                    packageCode=self._get(it, "packageCode", "package_code"),
                    requestedShippingService=self._get(
                        it, "requestedShippingService", "requested_shipping_service"
                    ),
                    customerName=str(customer_name).strip() if customer_name else None,
                    shipFromName=str(ship_from_name).strip() if ship_from_name else None,
                    orderStatus=(
                        str(self._get(it, "orderStatus", "order_status")).strip()
                        if self._get(it, "orderStatus", "order_status") is not None
                        else None
                    ),
                    items=list(items_list) if isinstance(items_list, list) else [],
                )
            )
        return out

    async def list_shipments(
        self,
        order_id: int,
        *,
        include_voided: bool,
        page_size: int | None = None,
    ) -> list[Shipment]:
        ps = int(page_size) if page_size is not None else 100
        data = await self._request_json(
            method="GET",
            path="/shipments",
            params={"orderId": int(order_id), "pageSize": ps},
        )

        if not isinstance(data, dict):
            raise ProviderParseError(
                method="GET",
                url=f"{self._base_url}/shipments",
                status=200,
                message="Unexpected shipments response shape: expected object with key 'shipments'",
                body_snippet=str(data)[:2000],
                expected="object with 'shipments' list",
            )
        items = data.get("shipments")
        if items is None:
            items = []
        if not isinstance(items, list):
            raise ProviderParseError(
                method="GET",
                url=f"{self._base_url}/shipments",
                status=200,
                message="Unexpected shipments response shape: expected list at 'shipments'",
                body_snippet=json.dumps(
                    {k: type(v).__name__ for k, v in list(data.items())[:50]}, ensure_ascii=False
                )[:2000],
                expected="shipments: list",
            )

        out: list[Shipment] = []
        for it in items:
            if not isinstance(it, dict):
                continue

            sid = self._get(it, "shipmentId", "shipment_id", "id")
            oid = self._get(it, "orderId", "order_id")
            voided = bool(self._get(it, "voided", "isVoided", "is_voided") or False)
            if sid is None or oid is None:
                continue

            out.append(
                Shipment(
                    shipmentId=self._as_int(sid, field="shipmentId"),
                    orderId=self._as_int(oid, field="orderId"),
                    voided=voided,
                    carrierCode=self._get(it, "carrierCode", "carrier_code"),
                    serviceCode=self._get(it, "serviceCode", "service_code"),
                    packageCode=self._get(it, "packageCode", "package_code"),
                )
            )

        if not include_voided:
            out = [s for s in out if not s.voided]

        out.sort(key=lambda s: s.shipmentId, reverse=True)
        return out
