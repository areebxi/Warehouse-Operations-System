from __future__ import annotations
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from shared.shipstation import (  # noqa: E402
    ShipStationClient,
    ShipStationCredentials,
    ShipStationError,
    load_shipstation_credentials,
)

class ShipStationAPIMixin2:
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

    def export_orders_to_json(self, orders: List[Dict], filename: str = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"awaiting_dispatch_orders_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as jsonfile:
            json.dump(orders, jsonfile, indent=2, ensure_ascii=False, default=str)

        print(f"Orders exported to {filename}")
        return filename

    def get_order_details(self, order_id: int) -> Optional[Dict]:
        try:
            return self._client.get_order(int(order_id))
        except ShipStationError as e:
            print(f"Error fetching order {order_id}: {e}")
            return None

