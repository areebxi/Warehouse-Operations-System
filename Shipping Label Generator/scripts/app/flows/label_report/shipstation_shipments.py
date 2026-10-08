from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from scripts.app.providers.real.provider import RealProvider


@dataclass(frozen=True)
class ShipStationShipmentRow:
    order_number: str
    order_id: int
    shipment_id: int
    create_date: str
    tracking_number: str
    carrier_code: str
    service_code: str
    package_code: str
    voided: bool


def _get(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d:
            return d.get(k)
    return None


async def list_shipments_created_on_date(provider: RealProvider, *, date_ymd: str) -> list[ShipStationShipmentRow]:
    """
    Fetch non-voided shipments created on the given local calendar date (YYYY-MM-DD).
    """
    page = 1
    out: list[ShipStationShipmentRow] = []
    while True:
        data = await provider._request_json(
            method="GET",
            path="/shipments",
            params={
                "createDateStart": date_ymd,
                "createDateEnd": date_ymd,
                "pageSize": 500,
                "page": page,
            },
        )
        if not isinstance(data, dict):
            break
        items = data.get("shipments")
        if not isinstance(items, list):
            items = []
        for it in items:
            if not isinstance(it, dict):
                continue
            sid = _get(it, "shipmentId", "shipment_id", "id")
            oid = _get(it, "orderId", "order_id")
            on = _get(it, "orderNumber", "order_number")
            if sid is None or oid is None or on is None:
                continue
            voided = bool(_get(it, "voided", "isVoided", "is_voided") or False)
            if voided:
                continue
            create_date = str(_get(it, "createDate", "create_date") or "").strip()
            out.append(
                ShipStationShipmentRow(
                    order_number=str(on).strip(),
                    order_id=int(oid),
                    shipment_id=int(sid),
                    create_date=create_date,
                    tracking_number=str(_get(it, "trackingNumber", "tracking_number") or "").strip(),
                    carrier_code=str(_get(it, "carrierCode", "carrier_code") or "").strip(),
                    service_code=str(_get(it, "serviceCode", "service_code") or "").strip(),
                    package_code=str(_get(it, "packageCode", "package_code") or "").strip(),
                    voided=voided,
                )
            )
        pages = int(data.get("pages") or 1)
        if page >= pages:
            break
        page += 1
    return out


def utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
