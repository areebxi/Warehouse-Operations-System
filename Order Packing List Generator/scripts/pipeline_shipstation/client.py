"""ShipStation V1 API client (list tags, list orders by tag)."""

from __future__ import annotations

from typing import Any, Callable

import requests

from .credentials import ShipStationCredentials, load_shipstation_credentials

LogFn = Callable[[str], None]


class ShipStationError(RuntimeError):
    """Raised when a ShipStation API call fails."""


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
        try:
            resp = self._session.get(url, params=params or {}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ShipStationError(f"ShipStation request failed: {exc}") from exc
        if resp.status_code == 401:
            raise ShipStationError("ShipStation authentication failed (check API KEY.txt).")
        if not resp.ok:
            body = (resp.text or "")[:300]
            raise ShipStationError(
                f"ShipStation HTTP {resp.status_code} for {path}: {body}"
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise ShipStationError(f"ShipStation returned invalid JSON for {path}") from exc

    def list_tags(self) -> list[dict[str, Any]]:
        """Return tags as list of dicts with tagId and name (sorted by name)."""
        data = self._get("accounts/listtags")
        tags: Any
        if isinstance(data, list):
            tags = data
        elif isinstance(data, dict):
            tags = data.get("tags")
            if tags is None and isinstance(data.get("tagId"), (int, str)):
                tags = [data]
            if not isinstance(tags, list):
                for key in ("Tags", "results"):
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
            tag_id = t.get("tagId", t.get("TagId"))
            name = t.get("name", t.get("Name", ""))
            if tag_id is None:
                continue
            out.append({"tagId": int(tag_id), "name": str(name or "").strip()})
        out.sort(key=lambda x: (x["name"].casefold(), x["tagId"]))
        self._log(f"ShipStation: loaded {len(out)} tag(s).")
        return out

    def list_orders_by_tag(
        self,
        tag_id: int,
        *,
        order_status: str = "awaiting_shipment",
        page_size: int = 500,
    ) -> list[dict[str, Any]]:
        """Fetch all pages of orders for tagId + orderStatus."""
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
                raise ShipStationError("ShipStation listbytag response missing orders list.")
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
