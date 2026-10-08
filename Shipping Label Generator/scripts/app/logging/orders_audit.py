from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from scripts.app.logging.jsonl import JsonlLogger


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_fields(fields: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in fields.items():
        if v is None:
            continue
        if isinstance(v, str) and not v.strip():
            continue
        out[k] = v
    return out


@dataclass
class OrderAuditLogger:
    """
    Per-order trace lines written into the existing run log (shipping.log / combined.log).
    """

    log: JsonlLogger
    command: str
    run_key: str

    @classmethod
    def for_log(cls, *, log: JsonlLogger, command: str, run_key: str) -> OrderAuditLogger:
        return cls(log=log, command=str(command), run_key=str(run_key))

    # Keep older call sites working.
    beside_log = for_log

    def record(self, *, outcome: str, order_number: str, **fields: Any) -> None:
        entry = _clean_fields(
            {
                "ts": _utc_iso(),
                "command": self.command,
                "run_key": self.run_key,
                "outcome": str(outcome),
                "order_number": str(order_number),
                **fields,
            }
        )
        self.log.info("order_audit", extra=entry)

    def summary(self, **fields: Any) -> None:
        entry = _clean_fields(
            {
                "ts": _utc_iso(),
                "command": self.command,
                "run_key": self.run_key,
                "outcome": "run_summary",
                **fields,
            }
        )
        self.log.info("order_audit_summary", extra=entry)
