from __future__ import annotations
import atexit
import json
import logging
import queue
import re
import threading
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from app.logging.redact import redact
from app.util.time import local_date_ymd, utc_compact_timestamp
_console_queue: queue.Queue[logging.LogRecord] | None = None
_console_listener: QueueListener | None = None
_console_lock = threading.Lock()
def _shutdown_console_listener() -> None:
    global _console_listener
    with _console_lock:
        if _console_listener is not None:
            _console_listener.stop()
            _console_listener = None
def _console_queue_handler() -> QueueHandler:
    global _console_queue, _console_listener
    with _console_lock:
        if _console_queue is None:
            _console_queue = queue.Queue(-1)
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.WARNING)
            stream_handler.setFormatter(_JsonlFormatter())
            _console_listener = QueueListener(_console_queue, stream_handler, respect_handler_level=True)
            _console_listener.start()
            atexit.register(_shutdown_console_listener)
        return QueueHandler(_console_queue)
def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
class _JsonlFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event: dict[str, Any] = {
            "ts": _utc_iso(),
            "level": record.levelname,
            "msg": record.getMessage(),
            "logger": record.name,
        }

        extra_payload = getattr(record, "extra_payload", None)
        if extra_payload is not None:
            event["extra"] = extra_payload

        if record.exc_info:
            event["exc"] = self.formatException(record.exc_info)

        return json.dumps(event, ensure_ascii=False)
