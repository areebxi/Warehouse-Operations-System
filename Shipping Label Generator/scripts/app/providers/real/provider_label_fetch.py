"""Download an existing label. Tries the current path, then ShipStation getlabel."""
from __future__ import annotations

from typing import Any

from scripts.app.models.label import Label
from scripts.app.providers.real.provider import ProviderHttpError, ProviderParseError


async def _get_json(provider: Any, *, path: str, params: dict[str, Any] | None) -> Any | None:
    try:
        return await provider._request_json(method="GET", path=path, params=params)
    except ProviderHttpError as e:
        if e.status == 404:
            return None
        raise


def _label_from_payload(provider: Any, data: Any, *, url: str) -> Label | None:
    if data is None:
        return None
    if not isinstance(data, dict):
        raise ProviderParseError(
            method="GET",
            url=url,
            status=200,
            message="Unexpected label response shape: expected object",
            body_snippet=str(data)[:2000],
            expected="object with labelData or labelDownload",
        )
    label_data = provider._get(data, "labelData", "label_data")
    tracking = provider._get(data, "trackingNumber", "tracking_number")
    if label_data:
        return Label(labelData=str(label_data), trackingNumber=str(tracking) if tracking else None)
    return None


async def fetch_label(provider: Any, shipment_id: int) -> Label | None:
    sid = int(shipment_id)
    primary = f"/shipments/{sid}/label"
    data = await _get_json(provider, path=primary, params=None)
    label = _label_from_payload(provider, data, url=f"{provider._base_url}{primary}")
    if label is None and isinstance(data, dict):
        href = None
        ld = data.get("labelDownload")
        if isinstance(ld, dict):
            href = ld.get("href") or ld.get("url")
        if href and isinstance(href, str) and href.strip():
            b64 = await provider._download_label_as_base64(href.strip())
            tracking = provider._get(data, "trackingNumber", "tracking_number")
            return Label(labelData=b64, trackingNumber=str(tracking) if tracking else None)
    if label is not None:
        return label

    getlabel = "/shipments/getlabel"
    data2 = await _get_json(provider, path=getlabel, params={"shipmentId": sid})
    label2 = _label_from_payload(provider, data2, url=f"{provider._base_url}{getlabel}")
    if label2 is None and isinstance(data2, dict):
        href = None
        ld = data2.get("labelDownload")
        if isinstance(ld, dict):
            href = ld.get("href") or ld.get("url")
        if href and isinstance(href, str) and href.strip():
            b64 = await provider._download_label_as_base64(href.strip())
            tracking = provider._get(data2, "trackingNumber", "tracking_number")
            return Label(labelData=b64, trackingNumber=str(tracking) if tracking else None)
    return label2
