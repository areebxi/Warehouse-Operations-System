from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from scripts.app.flows.amendments.tags import OrderTagInfo
from scripts.app.providers.real.provider import RealProvider

# Cache listtags per RealProvider instance for the lifetime of a print run.
_account_tags_cache: dict[int, dict[int, str]] = {}


def clear_account_tags_cache() -> None:
    _account_tags_cache.clear()


async def get_cached_account_tags(provider: RealProvider) -> dict[int, str]:
    key = id(provider)
    cached = _account_tags_cache.get(key)
    if cached is not None:
        return cached
    loaded = await list_account_tags(provider)
    _account_tags_cache[key] = loaded
    return loaded


def _get(d: dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in d:
            return d.get(k)
    return None


def _as_int(v: Any) -> int | None:
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None


def _parse_tag_ids(raw: Any) -> list[int]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    out: list[int] = []
    for x in raw:
        n = _as_int(x)
        if n is not None:
            out.append(n)
    return out


def _list_account_tags_sync() -> dict[int, str]:
    """Shared sync client — one credentials path for the whole warehouse."""
    warehouse = Path(__file__).resolve().parents[5]
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared.shipstation import ShipStationClient

    tags = ShipStationClient().list_tags()
    return {int(t["tagId"]): str(t["name"]) for t in tags if t.get("name")}


async def list_account_tags(provider: RealProvider) -> dict[int, str]:
    """
    Map tagId -> name from ShipStation GET /accounts/listtags.

    Uses shared.shipstation sync client (same credentials as Packing/PO).
    ``provider`` is kept for call-site compatibility / cache keying.
    """
    _ = provider
    return await asyncio.to_thread(_list_account_tags_sync)

def _order_tag_info_from_raw(
    *,
    order_number: str,
    raw_order: dict[str, Any],
    tag_id_to_name: dict[int, str],
) -> OrderTagInfo:
    oid = _as_int(_get(raw_order, "orderId", "order_id", "id"))
    tag_ids = _parse_tag_ids(_get(raw_order, "tagIds", "tag_ids", "tags"))
    names: list[str] = []
    for tid in tag_ids:
        nm = tag_id_to_name.get(tid)
        if nm:
            names.append(nm)
        else:
            names.append(f"tagId:{tid}")

    ship_to = raw_order.get("shipTo") if isinstance(raw_order.get("shipTo"), dict) else {}
    customer_name = _get(raw_order, "customerName", "customer_name")
    if not customer_name and isinstance(ship_to, dict):
        customer_name = ship_to.get("name")

    status = _get(raw_order, "orderStatus", "order_status")
    return OrderTagInfo(
        order_number=str(order_number).strip(),
        order_id=oid,
        tag_ids=tag_ids,
        tag_names=names,
        order_status=str(status).strip() if status is not None else "",
        customer_name=str(customer_name).strip() if customer_name else "",
    )


async def inspect_order_tags(
    provider: RealProvider,
    order_number: str,
    *,
    tag_id_to_name: dict[int, str] | None = None,
) -> list[OrderTagInfo]:
    """
    Look up ShipStation order(s) by order number and resolve their tags.

    ShipStation returns tagIds on each order; names come from /accounts/listtags.
    Does not use or modify RealProvider.lookup_orders / Order model.
    """
    order_number = str(order_number).strip()
    if not order_number:
        return []

    id_to_name = tag_id_to_name if tag_id_to_name is not None else await get_cached_account_tags(provider)

    data = await provider._request_json(
        method="GET",
        path="/orders",
        params={"orderNumber": order_number, "pageSize": 100},
    )
    items: list[Any] = []
    if isinstance(data, dict):
        raw = data.get("orders")
        if isinstance(raw, list):
            items = raw

    out: list[OrderTagInfo] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        on = _get(it, "orderNumber", "order_number", "number")
        if on is None:
            continue
        # Exact order-number match (ShipStation may be loose).
        if str(on).strip() != order_number:
            continue
        out.append(
            _order_tag_info_from_raw(
                order_number=order_number,
                raw_order=it,
                tag_id_to_name=id_to_name,
            )
        )
    return out


async def inspect_order_tags_by_id(
    provider: RealProvider,
    order_id: int,
    *,
    order_number: str = "",
    tag_id_to_name: dict[int, str] | None = None,
) -> OrderTagInfo | None:
    """
    Fetch one ShipStation order by id and resolve its tags (GET /orders/{orderId}).
    """
    id_to_name = tag_id_to_name if tag_id_to_name is not None else await get_cached_account_tags(provider)
    data = await provider._request_json(method="GET", path=f"/orders/{int(order_id)}")
    if not isinstance(data, dict):
        return None
    on = str(_get(data, "orderNumber", "order_number", "number") or order_number or "").strip()
    return _order_tag_info_from_raw(
        order_number=on or str(order_number),
        raw_order=data,
        tag_id_to_name=id_to_name,
    )


async def selected_order_has_amendments(
    provider: object,
    *,
    order_id: int,
    order_number: str,
) -> tuple[bool, OrderTagInfo | None]:
    """
    Print-safe amendments check.

    Returns (True, info) when Amendments tag is present.
    Returns (False, None) when provider is not RealProvider.
    Returns (False, info_or_None) when tags loaded and Amendments is absent.
    Raises on ShipStation/API errors so the print caller can fail-open with a warning.
    """
    if not isinstance(provider, RealProvider):
        return False, None
    info = await inspect_order_tags_by_id(
        provider,
        int(order_id),
        order_number=str(order_number),
    )
    if info is None:
        return False, None
    return bool(info.has_amendments), info
