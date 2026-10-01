"""ShipStationAPI fetch/export methods for Purchase Order Generator."""

from __future__ import annotations

from typing import Dict, List, Optional

from shared.shipstation import ShipStationError  # noqa: E402
from shipstation_orders_export import (  # noqa: E402
    export_orders_to_csv as _export_orders_to_csv,
    export_orders_to_json as _export_orders_to_json,
)


class ShipStationAPIFetch:
    def get_orders_by_tag(
        self,
        tag_id: int | str,
        *,
        order_status: str = "awaiting_shipment",
        page_size: int = 500,
    ) -> List[Dict]:
        """Server-side tag filter via orders/listbytag (preferred)."""
        return self._client.list_orders_by_tag(
            int(tag_id),
            order_status=order_status,
            page_size=page_size,
        )

    def get_awaiting_dispatch_orders(
        self,
        page: int = 1,
        page_size: int = 500,
        order_date: str = None,
    ) -> List[Dict]:
        """Bulk awaiting_shipment list (prefer get_orders_by_tag when you have a tag)."""
        _ = page  # pagination handled inside client
        return self._client.list_orders(
            order_status="awaiting_shipment",
            page_size=page_size,
            order_date=order_date,
        )

    def get_shipped_orders(
        self,
        page: int = 1,
        page_size: int = 500,
        order_date: str = None,
    ) -> List[Dict]:
        _ = page
        return self._client.list_orders(
            order_status="shipped",
            page_size=page_size,
            order_date=order_date,
        )

    def export_orders_to_csv(self, orders, filename=None):
        return _export_orders_to_csv(orders, filename)

    def export_orders_to_json(self, orders: List[Dict], filename: str = None) -> str:
        return _export_orders_to_json(orders, filename)

    def get_order_details(self, order_id: int) -> Optional[Dict]:
        try:
            return self._client.get_order(int(order_id))
        except ShipStationError as e:
            print(f"Error fetching order {order_id}: {e}")
            return None
