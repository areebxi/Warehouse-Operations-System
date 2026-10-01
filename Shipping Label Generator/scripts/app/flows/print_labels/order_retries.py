from __future__ import annotations

from time import monotonic
from typing import Any, Awaitable, Callable, TypeVar

from app.config.load import AppConfig
from app.logging.jsonl import JsonlLogger
from app.util.retries import call_with_retries

T = TypeVar("T")


async def _timed_call_with_retries(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    op: str,
    op_kind: str,
    fn: Callable[[], Awaitable[T]],
    extra: dict[str, Any],
) -> T:
    """Wraps call_with_retries and logs elapsed_ms per op (includes retries)."""
    t0 = monotonic()
    try:
        out = await call_with_retries(cfg=cfg, log=log, op=op, op_kind=op_kind, fn=fn, extra=extra)
        log.info(
            "provider_op_timing",
            extra={**extra, "op": op, "elapsed_ms": round((monotonic() - t0) * 1000.0, 2), "ok": True},
        )
        return out
    except Exception:
        log.info(
            "provider_op_timing",
            extra={**extra, "op": op, "elapsed_ms": round((monotonic() - t0) * 1000.0, 2), "ok": False},
        )
        raise

