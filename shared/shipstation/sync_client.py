"""ShipStation Classic V1 sync HTTP client (read helpers)."""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

import requests

from .credentials import ShipStationCredentials, load_shipstation_credentials

LogFn = Callable[[str], None]


class ShipStationError(RuntimeError):
    """Raised when a ShipStation API call fails."""


def parse_listtags_payload(data: Any) -> list[dict[str, Any]]:
    """Normalize accounts/listtags JSON into [{tagId, name}, ...] sorted by name."""
    tags: Any
    if isinstance(data, list):
        tags = data
    elif isinstance(data, dict):
        tags = data.get("tags")
        if tags is None and isinstance(data.get("tagId"), (int, str)):
            tags = [data]
        if not isinstance(tags, list):
            for key in ("Tags", "results", "list"):
                if isinstance(data.get(key), list):
                    tags = data[key]
                    break
    else:
        tags = None
    if not isinstance(tags, list):
        raise ShipStationError("ShipStation listtags response missing tags list.")

    out: list[dict[str, Any]] = []
    for t in tags:
        if not isinstance(t, dict):
            continue
        tag_id = t.get("tagId", t.get("TagId", t.get("tag_id", t.get("id"))))
        name = t.get("name", t.get("Name", t.get("tagName", t.get("tag_name", ""))))
        if tag_id is None:
            continue
        try:
            tid = int(tag_id)
        except (TypeError, ValueError):
            continue
        out.append({"tagId": tid, "name": str(name or "").strip()})
    out.sort(key=lambda x: (x["name"].casefold(), x["tagId"]))
    return out


class ShipStationClient:
    def __init__(
        self,
        credentials: ShipStationCredentials | None = None,
        *,
        timeout: float = 60.0,
        log: LogFn | None = None,
    ) -> None:
        self.credentials = credentials or load_shipstation_credentials()
        self.timeout = timeout
        self._log = log or (lambda _msg: None)
        self._session = requests.Session()
        self._session.auth = (self.credentials.api_key, self.credentials.api_secret)
        self._session.headers.update({"Accept": "application/json"})

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.credentials.base_url.rstrip('/')}/{path.lstrip('/')}"
        last_err: Exception | None = None
        for attempt in range(8):
            try:
                resp = self._session.get(url, params=params or {}, timeout=self.timeout)
            except requests.RequestException as exc:
                raise ShipStationError(f"ShipStation request failed: {exc}") from exc
            if resp.status_code == 401:
                raise ShipStationError(
                    "ShipStation authentication failed (check config/ShipStation/.env)."
                )
            if resp.status_code == 429:
                wait_s = 20.0 * (attempt + 1)
                raw = (resp.headers.get("Retry-After") or "").strip()
                if raw:
                    try:
                        wait_s = max(wait_s, float(raw))
                    except ValueError:
                        pass
                self._log(f"ShipStation: HTTP 429, sleeping {wait_s:.0f}s (attempt {attempt + 1}/8)…")
                time.sleep(wait_s)
                last_err = ShipStationError("ShipStation HTTP 429 for orders: Too Many Request")
                continue
            if not resp.ok:
                body = (resp.text or "")[:300]
                raise ShipStationError(
                    f"ShipStation HTTP {resp.status_code} for {path}: {body}"
                )
            try:
                return resp.json()
            except ValueError as exc:
                raise ShipStationError(f"ShipStation returned invalid JSON for {path}") from exc
        raise last_err or ShipStationError(f"ShipStation HTTP 429 for {path}")

    def list_tags(self) -> list[dict[str, Any]]:
        data = self._get("accounts/listtags")
        out = parse_listtags_payload(data)
        self._log(f"ShipStation: loaded {len(out)} tag(s).")
        return out

    def list_orders_by_tag(
        self,
        tag_id: int,
        *,
        order_status: str = "awaiting_shipment",
        page_size: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of orders for tagId + orderStatus (orders/listbytag)."""
        page_size = max(1, min(int(page_size), 500))
        page = 1
        all_orders: list[dict[str, Any]] = []
        total_pages: int | None = None
        while True:
            self._log(
                f"ShipStation: fetching orders tagId={tag_id} "
                f"status={order_status} page={page}"
                + (f"/{total_pages}" if total_pages else "")
                + "…"
            )
            data = self._get(
                "orders/listbytag",
                params={
                    "tagId": int(tag_id),
                    "orderStatus": order_status,
                    "page": page,
                    "pageSize": page_size,
                },
            )
            if not isinstance(data, dict):
                raise ShipStationError("Unexpected ShipStation listbytag response.")
            orders = data.get("orders")
            if not isinstance(orders, list):
                raise ShipStationError(
                    "ShipStation listbytag response missing orders list."
                )
            all_orders.extend(o for o in orders if isinstance(o, dict))
            try:
                total_pages = int(data.get("pages") or 1)
            except (TypeError, ValueError):
                total_pages = 1
            if page >= total_pages:
                break
            page += 1
        self._log(f"ShipStation: fetched {len(all_orders)} order(s) for tagId={tag_id}.")
        return all_orders

    def list_orders(
        self,
        *,
        order_status: str = "awaiting_shipment",
        page_size: int = 500,
        order_date: Optional[str] = None,
        order_date_start: Optional[str] = None,
        order_date_end: Optional[str] = None,
        sort_by: str = "OrderDate",
        sort_dir: str = "DESC",
        page_pause_s: float = 0.0,
        start_page: int = 1,
        collect: bool = True,
        on_page: Optional[Callable[[int, int, list[dict[str, Any]]], None]] = None,
    ) -> list[dict[str, Any]]:
        """Paginated GET /orders (prefer list_orders_by_tag when filtering by tag)."""
        page_size = max(1, min(int(page_size), 500))
        page = max(1, int(start_page))
        all_orders: list[dict[str, Any]] = []
        total_pages: int | None = None
        while True:
            self._log(
                f"ShipStation: fetching orders status={order_status} page={page}"
                + (f"/{total_pages}" if total_pages else "")
                + "…"
            )
            params: dict[str, Any] = {
                "orderStatus": order_status,
                "page": page,
                "pageSize": page_size,
                "sortBy": sort_by,
                "sortDir": sort_dir,
            }
            if order_date:
                params["orderDate"] = order_date
            if order_date_start:
                params["orderDateStart"] = order_date_start
            if order_date_end:
                params["orderDateEnd"] = order_date_end
            data = self._get("orders", params=params)
            if not isinstance(data, dict):
                raise ShipStationError("Unexpected ShipStation orders response.")
            orders = data.get("orders")
            if not isinstance(orders, list):
                raise ShipStationError("ShipStation orders response missing orders list.")
            batch = [o for o in orders if isinstance(o, dict)]
            if collect:
                all_orders.extend(batch)
            try:
                total_pages = int(data.get("pages") or 1)
            except (TypeError, ValueError):
                total_pages = 1
            if on_page:
                on_page(page, total_pages, batch)
            if page >= total_pages:
                break
            if page_pause_s > 0:
                time.sleep(page_pause_s)
            page += 1
        self._log(f"ShipStation: fetched {len(all_orders)} order(s) status={order_status}.")
        return all_orders

    def get_order(self, order_id: int) -> dict[str, Any]:
        data = self._get(f"orders/{int(order_id)}")
        if not isinstance(data, dict):
            raise ShipStationError(f"Unexpected ShipStation order response for {order_id}.")
        return data
