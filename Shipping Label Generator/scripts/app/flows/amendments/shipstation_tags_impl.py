from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from typing import Any
from app.flows.amendments.tags import OrderTagInfo
from app.providers.real.provider import RealProvider

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
async def get_cached_account_tags(provider: RealProvider) -> dict[int, str]:
    key = id(provider)
    cached = _account_tags_cache.get(key)
    if cached is not None:
        return cached
    loaded = await list_account_tags(provider)
    _account_tags_cache[key] = loaded
    return loaded
def clear_account_tags_cache() -> None:
    _account_tags_cache.clear()
