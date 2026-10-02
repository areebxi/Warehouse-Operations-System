"""Normalize ShipStation listtags / stores JSON payloads."""

from __future__ import annotations

from typing import Any


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


def parse_stores_payload(data: Any) -> list[dict[str, Any]]:
    """Normalize /stores JSON into [{storeId, storeName}, ...]."""
    stores: Any
    if isinstance(data, list):
        stores = data
    elif isinstance(data, dict):
        stores = data.get("stores")
        if stores is None and data.get("storeId") is not None:
            stores = [data]
        if not isinstance(stores, list):
            stores = None
    else:
        stores = None
    if not isinstance(stores, list):
        raise ShipStationError("ShipStation stores response missing stores list.")
    out: list[dict[str, Any]] = []
    for s in stores:
        if not isinstance(s, dict):
            continue
        sid = s.get("storeId", s.get("StoreId", s.get("store_id", s.get("id"))))
        name = s.get("storeName", s.get("StoreName", s.get("store_name", s.get("name", ""))))
        if sid is None:
            continue
        try:
            store_id = int(sid)
        except (TypeError, ValueError):
            continue
        out.append({"storeId": store_id, "storeName": str(name or "").strip()})
    return out
