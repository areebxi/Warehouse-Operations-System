from __future__ import annotations

import base64
import os
import asyncio
import json
from dataclasses import dataclass
from time import monotonic
from typing import Any

import aiohttp

from scripts.app.config.load import AppConfig
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.models.label import Label
from scripts.app.models.order import Order
from scripts.app.models.shipment import Shipment
from scripts.app.providers.base import Provider


def _parse_retry_after_header(raw: str | None) -> float | None:
    """
    Parse Retry-After per RFC 7231: delay in seconds, or an HTTP-date after which to retry.
    Returns seconds to wait (>= 0), or None if the header is missing or unparsable.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        sec = float(s)
        if sec >= 0.0:
            return sec
    except ValueError:
        pass
    try:
        from datetime import datetime, timezone

        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(s)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0.0, (dt - now).total_seconds())
    except Exception:
        return None


@dataclass(frozen=True)
class ProviderHttpError(RuntimeError):
    method: str
    url: str
    status: int
    message: str
    retry_after: float | None = None

    def __str__(self) -> str:
        return f"ProviderHttpError(method={self.method}, url={self.url}, status={self.status}, message={self.message})"


@dataclass(frozen=True)
class ProviderParseError(RuntimeError):
    method: str
    url: str
    status: int
    message: str
    body_snippet: str = ""
    expected: str = ""
    non_retryable: bool = True

    def __str__(self) -> str:
        bits = [f"ProviderParseError(method={self.method}, url={self.url}, status={self.status}"]
        if self.expected:
            bits.append(f"expected={self.expected}")
        bits.append(f"message={self.message})")
        return ", ".join(bits)


@dataclass(frozen=True)
class ProviderNonRetryableError(RuntimeError):
    message: str
    non_retryable: bool = True

    def __str__(self) -> str:
        return self.message


class _SpacingRateLimiter:
    """
    Very small async rate limiter.

    This enforces an average request rate by spacing requests (no bursts).
    It is intentionally simple and dependency-free.
    """

    def __init__(self, requests_per_sec: float | None) -> None:
        rps = float(requests_per_sec) if requests_per_sec else 0.0
        self._interval = (1.0 / rps) if rps > 0.0 else 0.0
        self._lock = asyncio.Lock()
        self._next_at = 0.0

    async def acquire(self) -> None:
        if self._interval <= 0.0:
            return
        while True:
            delay = 0.0
            async with self._lock:
                now = monotonic()
                at = self._next_at
                if now >= at:
                    self._next_at = now + self._interval
                    return
                delay = at - now
            await asyncio.sleep(delay)


def _local_rate_limiter_from_cfg(*, rl: dict[str, Any], log: JsonlLogger) -> _SpacingRateLimiter:
    """
    Optional fixed spacing between requests (requests_per_sec).
    If unset, null, or <= 0: no in-process pacing — rely on max_workers semaphore + ShipStation 429 handling.
    """
    requests_per_sec = rl.get("requests_per_sec")
    rps_f: float | None = float(requests_per_sec) if requests_per_sec is not None else None
    if rps_f is not None and rps_f <= 0.0:
        rps_f = None

    lim = _SpacingRateLimiter(float(rps_f) if rps_f is not None else None)
    log.info(
        "provider_rate_limit_mode",
        extra={
            "mode": "spacing" if (rps_f is not None and rps_f > 0.0) else "none",
            "requests_per_sec": rps_f,
        },
    )
    return lim


class RealProvider(Provider):
    def __init__(self, cfg: AppConfig, log: JsonlLogger) -> None:
        self._cfg = cfg
        self._log = log
        self._base_url = (os.getenv("REAL_API_BASE_URL") or "").strip().rstrip("/")
        self._api_key = (os.getenv("REAL_API_KEY") or "").strip()
        self._api_secret = (os.getenv("REAL_API_SECRET") or "").strip()
        self._session: aiohttp.ClientSession | None = None

        if not self._base_url:
            raise ValueError("REAL_API_BASE_URL is required (e.g. https://ssapi.shipstation.com)")
        if not self._api_key or not self._api_secret:
            raise ValueError("REAL_API_KEY and REAL_API_SECRET are required")

        conc = cfg.raw.get("concurrency") or {}
        self._req_sem = asyncio.Semaphore(int(conc.get("max_workers", 25)))

        rl = cfg.raw.get("rate_limit") or {}
        rl_dict = rl if isinstance(rl, dict) else {}
        self._rate_limiter = _local_rate_limiter_from_cfg(rl=rl_dict, log=log)

    def _auth(self) -> aiohttp.BasicAuth:
        return aiohttp.BasicAuth(self._api_key, self._api_secret)

    def _provider_cfg(self) -> dict[str, Any]:
        raw = self._cfg.raw.get("provider") or {}
        return raw if isinstance(raw, dict) else {}

    def _http_cfg(self) -> dict[str, Any]:
        raw = self._provider_cfg().get("http") or {}
        return raw if isinstance(raw, dict) else {}

    def _connector(self) -> aiohttp.TCPConnector:
        http = self._http_cfg()
        conc = self._cfg.raw.get("concurrency") or {}
        max_workers = int(conc.get("max_workers", 25))
        limit = int(http.get("pool_limit", min(max_workers, 50)))
        limit_per_host = int(http.get("pool_limit_per_host", min(max_workers, 25)))
        return aiohttp.TCPConnector(limit=limit, limit_per_host=limit_per_host, enable_cleanup_closed=True)

    def _client_timeout(self) -> aiohttp.ClientTimeout:
        http = self._http_cfg()
        # call_with_retries enforces total request/label timeouts via asyncio.wait_for.
        # These are socket-level bounds to avoid hanging connections.
        sock_connect = float(http.get("sock_connect_timeout_sec", 30))
        sock_read = float(http.get("sock_read_timeout_sec", 60))
        return aiohttp.ClientTimeout(total=None, sock_connect=sock_connect, sock_read=sock_read)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is not None and not self._session.closed:
            return self._session
        headers = {"Accept": "application/json"}
        self._session = aiohttp.ClientSession(
            auth=self._auth(),
            timeout=self._client_timeout(),
            headers=headers,
            connector=self._connector(),
        )
        return self._session

    async def aclose(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _request_json(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        session = await self._get_session()
        await self._rate_limiter.acquire()
        async with self._req_sem:
            async with session.request(method.upper(), url, params=params, json=json_body) as resp:
                retry_after = None
                if resp.status == 429:
                    retry_after = _parse_retry_after_header(resp.headers.get("Retry-After"))

                text = ""
                try:
                    text = await resp.text()
                except Exception:
                    text = ""

                if resp.status >= 400:
                    msg = (text or f"HTTP {resp.status}")[:2000]
                    raise ProviderHttpError(
                        method=str(method).upper(),
                        url=url,
                        status=int(resp.status),
                        message=msg,
                        retry_after=retry_after,
                    )

                if resp.status == 204:
                    return None
                try:
                    return json.loads(text or "null")
                except Exception as e:
                    snippet = (text or "")[:2000]
                    raise ProviderParseError(
                        method=str(method).upper(),
                        url=url,
                        status=int(resp.status),
                        message="Invalid JSON response",
                        body_snippet=snippet,
                        expected="JSON object",
                    ) from e

    @staticmethod
    def _as_int(v: Any, *, field: str) -> int:
        try:
            return int(v)
        except Exception as e:
            raise ValueError(f"Invalid int for {field}: {v!r}") from e

    @staticmethod
    def _as_str(v: Any) -> str:
        return str(v).strip()

    @staticmethod
    def _get(d: dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d:
                return d.get(k)
        return None

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
                body_snippet=json.dumps({k: type(v).__name__ for k, v in list(data.items())[:50]}, ensure_ascii=False)[:2000],
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
                    requestedShippingService=self._get(it, "requestedShippingService", "requested_shipping_service"),
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
                body_snippet=json.dumps({k: type(v).__name__ for k, v in list(data.items())[:50]}, ensure_ascii=False)[:2000],
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

    async def fetch_label(self, shipment_id: int) -> Label | None:
        try:
            data = await self._request_json(method="GET", path=f"/shipments/{int(shipment_id)}/label")
        except ProviderHttpError as e:
            if e.status == 404:
                return None
            raise

        if not isinstance(data, dict):
            raise ProviderParseError(
                method="GET",
                url=f"{self._base_url}/shipments/{int(shipment_id)}/label",
                status=200,
                message="Unexpected label response shape: expected object",
                body_snippet=str(data)[:2000],
                expected="object with labelData or labelDownload",
            )

        label_data = self._get(data, "labelData", "label_data")
        if not label_data:
            # URL-mode fallback: labelDownload.href
            href = None
            ld = data.get("labelDownload")
            if isinstance(ld, dict):
                href = ld.get("href") or ld.get("url")
            if href and isinstance(href, str) and href.strip():
                b64 = await self._download_label_as_base64(href.strip())
                tracking = self._get(data, "trackingNumber", "tracking_number")
                return Label(labelData=b64, trackingNumber=str(tracking) if tracking else None)
            return None
        tracking = self._get(data, "trackingNumber", "tracking_number")
        return Label(labelData=str(label_data), trackingNumber=str(tracking) if tracking else None)

    async def _download_label_as_base64(self, href: str) -> str:
        url = href if href.lower().startswith("http") else f"{self._base_url}{href}"
        session = await self._get_session()
        await self._rate_limiter.acquire()
        async with self._req_sem:
            async with session.get(url) as resp:
                if resp.status >= 400:
                    retry_after = None
                    if resp.status == 429:
                        retry_after = _parse_retry_after_header(resp.headers.get("Retry-After"))
                    text = ""
                    try:
                        text = (await resp.text())[:2000]
                    except Exception:
                        text = f"HTTP {resp.status}"
                    raise ProviderHttpError(method="GET", url=url, status=int(resp.status), message=text, retry_after=retry_after)
                data = await resp.read()
                return base64.b64encode(data).decode("ascii")

    async def create_label(
        self,
        *,
        order: Order,
        carrier_code: str,
        service_code: str,
        package_code: str,
        ship_date: str,
        weight: float | None,
        weight_unit: str | None,
        customer_reference: str | None,
    ) -> Label:
        provider_cfg = self._provider_cfg()

        payload: dict[str, Any] = {
            "orderId": int(order.orderId),
            "carrierCode": str(carrier_code),
            "serviceCode": str(service_code),
            "packageCode": str(package_code),
            "shipDate": str(ship_date),
            "labelFormat": str(provider_cfg.get("label_format", "PDF")),
            "labelLayout": str(provider_cfg.get("label_layout", "4x6")),
            # Force inline: pipeline expects base64 labelData
            "labelDownloadType": "inline",
        }

        if weight is not None and weight_unit:
            payload["weight"] = {"value": float(weight), "units": str(weight_unit)}
        if customer_reference:
            payload["customerReference"] = str(customer_reference)

        data = await self._request_json(method="POST", path="/orders/createlabelfororder", json_body=payload)
        if not isinstance(data, dict):
            raise ProviderParseError(
                method="POST",
                url=f"{self._base_url}/orders/createlabelfororder",
                status=200,
                message="Unexpected create_label response shape: expected object",
                body_snippet=str(data)[:2000],
                expected="object with labelData",
            )

        label_data = self._get(data, "labelData", "label_data")
        if not label_data:
            # Enrich message with provider hints if present
            msg = data.get("message") or data.get("Message")
            errs = data.get("errors") or data.get("Errors")
            hint = ""
            if msg:
                hint = f" message={msg!r}"
            elif errs:
                hint = f" errors={str(errs)[:500]!r}"
            raise ProviderNonRetryableError(f"no labelData in response.{hint}".strip())

        # Basic sanity (write_label_pdf does deeper PDF validation)
        try:
            base64.b64decode(str(label_data).encode("ascii"), validate=False)
        except Exception:
            raise RuntimeError("labelData is not valid base64")

        tracking = self._get(data, "trackingNumber", "tracking_number")
        return Label(labelData=str(label_data), trackingNumber=str(tracking) if tracking else None)

    async def void_label(self, shipment_id: int) -> None:
        await self._request_json(method="POST", path="/shipments/voidlabel", json_body={"shipmentId": int(shipment_id)})
