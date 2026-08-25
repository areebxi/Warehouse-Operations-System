from __future__ import annotations

from typing import Any, Iterable


def redact(value: Any, *, redact_keys: Iterable[str]) -> Any:
    keys = {k for k in redact_keys}

    def _walk(v: Any) -> Any:
        if isinstance(v, dict):
            out: dict[Any, Any] = {}
            for k, vv in v.items():
                if isinstance(k, str) and k in keys:
                    out[k] = "[REDACTED]"
                else:
                    out[k] = _walk(vv)
            return out
        if isinstance(v, list):
            return [_walk(x) for x in v]
        if isinstance(v, tuple):
            return tuple(_walk(x) for x in v)
        return v

    return _walk(value)
