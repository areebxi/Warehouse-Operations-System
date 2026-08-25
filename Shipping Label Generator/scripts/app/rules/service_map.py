from __future__ import annotations

from typing import Any


def carrier_key(carrier: str) -> str:
    return str(carrier).lower().replace(" ", "_").replace("-", "_")


def map_service_code(*, cfg_raw: dict[str, Any], carrier: str, requested_shipping_service: str | None) -> str | None:
    if not requested_shipping_service:
        return None
    ckey = carrier_key(carrier)
    entries = (cfg_raw.get("service_map") or {}).get(ckey) or []
    hay = str(requested_shipping_service).lower()
    for e in entries:
        match = str((e or {}).get("match") or "").lower()
        code = (e or {}).get("code")
        if match and match in hay and code:
            return str(code)
    return None

