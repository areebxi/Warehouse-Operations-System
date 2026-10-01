from __future__ import annotations
import base64
import os
import asyncio
import json
from dataclasses import dataclass
from time import monotonic
from typing import Any
import aiohttp
from app.config.load import AppConfig
from app.logging.jsonl import JsonlLogger
from app.models.label import Label
from app.models.order import Order
from app.models.shipment import Shipment
from app.providers.base import Provider

class RealProviderMixin2:
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

    def _client_timeout(self) -> aiohttp.ClientTimeout:
        http = self._http_cfg()
        # call_with_retries enforces total request/label timeouts via asyncio.wait_for.
        # These are socket-level bounds to avoid hanging connections.
        sock_connect = float(http.get("sock_connect_timeout_sec", 30))
        sock_read = float(http.get("sock_read_timeout_sec", 60))
        return aiohttp.ClientTimeout(total=None, sock_connect=sock_connect, sock_read=sock_read)

