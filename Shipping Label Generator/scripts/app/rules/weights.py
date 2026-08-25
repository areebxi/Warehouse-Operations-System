from __future__ import annotations

from typing import Any


def _contains_any(haystack: str, needles: list[str]) -> bool:
    h = str(haystack).lower()
    for n in needles:
        if str(n).lower() in h:
            return True
    return False


def normalize_weight(*, cfg_raw: dict[str, Any], carrier_code: str, weight: float) -> tuple[float, str]:
    ounce_carriers = list(((cfg_raw.get("weight") or {}).get("ounce_carriers") or []))
    if _contains_any(carrier_code, ounce_carriers):
        return float(weight) * 16.0, "oz"
    return float(weight), "lb"

