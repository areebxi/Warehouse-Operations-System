from __future__ import annotations

import base64
from typing import Any

from app.models.label import Label
from app.models.order import Order
from app.providers.real.errors import (
    ProviderHttpError,
    ProviderNonRetryableError,
    ProviderParseError,
    _parse_retry_after_header,
)


class ProviderLabelsMixin:
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
                    raise ProviderHttpError(
                        method="GET",
                        url=url,
                        status=int(resp.status),
                        message=text,
                        retry_after=retry_after,
                    )
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
        await self._request_json(
            method="POST",
            path="/shipments/voidlabel",
            json_body={"shipmentId": int(shipment_id)},
        )
