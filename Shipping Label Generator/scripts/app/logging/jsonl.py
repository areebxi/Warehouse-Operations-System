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

from scripts.app.logging.redact import redact
from scripts.app.util.time import local_date_ymd, utc_compact_timestamp


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


@dataclass
class JsonlLogger:
    logs_dir: Path
    level: str
    redact_keys: list[str]
    logger_name: str
    log_path: Path
    rotate: bool = True
    also_console: bool = True
    _logger: logging.Logger | None = None

    @classmethod
    def from_config(cls, cfg: Any) -> "JsonlLogger":
        raw = cfg.raw if hasattr(cfg, "raw") else cfg
        logs_dir = Path(str(raw["paths"]["logs_dir"]))
        logs_dir.mkdir(parents=True, exist_ok=True)

        level = str(raw["logging"].get("level", "INFO")).upper()
        redact_keys = list(raw["logging"].get("redact_keys", []))

        # Default: rolling whole-history log.
        return cls(
            logs_dir=logs_dir,
            level=level,
            redact_keys=redact_keys,
            logger_name="app.shipping",
            log_path=logs_dir / "shipping.log",
            rotate=True,
            also_console=True,
        )

    @staticmethod
    def _safe_key(key: str) -> str:
        s = str(key or "").strip()
        s = re.sub(r"[^\w\-\.]+", "_", s)
        s = s.strip("._")
        return s or "run"

    @classmethod
    def for_input_run(cls, cfg: Any, *, input_key: str, command: str) -> "JsonlLogger":
        """
        Creates a single log file under:
          logs/<YYYY-MM-DD>/<input_key>/shipping.log

        This behaves like the original rolling `logs/shipping.log` (single file that accumulates
        events, with rotation), but separated per input key.
        """
        base = cls.from_config(cfg)
        key = cls._safe_key(input_key)
        cmd = cls._safe_key(command)
        run_dir = base.logs_dir / local_date_ymd() / key
        run_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            logs_dir=base.logs_dir,
            level=base.level,
            redact_keys=base.redact_keys,
            # Stable name so multiple runs append to the same file.
            logger_name=f"app.{cmd}.{key}",
            log_path=run_dir / "shipping.log",
            rotate=True,
            also_console=True,
        )

    @classmethod
    def for_combined_pdf_run(
        cls,
        cfg: Any,
        *,
        combined_pdf_stem: str,
        date_dir: str | None = None,
    ) -> "JsonlLogger":
        """
        Create a per-combined-PDF log file under:

          logs/Combined_PDFs Logs/<YYYY-MM-DD>/<combined_pdf_stem>.log

        This is intended to make troubleshooting combined-PDF issues easier by keeping
        each combined output's logs separated per file.
        """
        base = cls.from_config(cfg)
        dd = cls._safe_key(date_dir or local_date_ymd())
        stem = cls._safe_key(combined_pdf_stem)

        run_dir = base.logs_dir / "Combined_PDFs Logs" / dd
        run_dir.mkdir(parents=True, exist_ok=True)

        # Unique logger name per combined PDF so handlers don't collide across runs.
        logger_name = f"app.print.combined.{dd}.{stem}"

        return cls(
            logs_dir=base.logs_dir,
            level=base.level,
            redact_keys=base.redact_keys,
            logger_name=logger_name,
            log_path=run_dir / f"{stem}.log",
            rotate=True,
            also_console=True,
        )

    @classmethod
    def for_manual_print_run(
        cls,
        cfg: Any,
        *,
        job_id: str,
        date_dir: str | None = None,
    ) -> "JsonlLogger":
        """
        Create a per-manual-job combined log under:

          logs/Manual Print Logs/<YYYY-MM-DD>/<job_id>/combined.log
        """
        base = cls.from_config(cfg)
        dd = cls._safe_key(date_dir or local_date_ymd())
        key = cls._safe_key(job_id)

        run_dir = base.logs_dir / "Manual Print Logs" / dd / key
        run_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            logs_dir=base.logs_dir,
            level=base.level,
            redact_keys=base.redact_keys,
            logger_name=f"app.manual_print.{dd}.{key}",
            log_path=run_dir / "combined.log",
            rotate=True,
            also_console=True,
        )

    def _ensure_configured(self) -> logging.Logger:
        if self._logger is not None:
            return self._logger

        logger = logging.getLogger(self.logger_name)
        logger.setLevel(getattr(logging, self.level, logging.INFO))
        logger.propagate = False

        # Avoid duplicating handlers if called multiple times for same instance logger_name.
        if not getattr(logger, "_shipping_configured", False):
            if self.rotate:
                file_handler: logging.Handler = RotatingFileHandler(
                    filename=str(self.log_path),
                    maxBytes=5 * 1024 * 1024,
                    backupCount=5,
                    encoding="utf-8",
                )
            else:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(filename=str(self.log_path), encoding="utf-8")
            file_handler.setLevel(getattr(logging, self.level, logging.INFO))
            file_handler.setFormatter(_JsonlFormatter())
            logger.addHandler(file_handler)

            if self.also_console:
                console_handler = _console_queue_handler()
                console_handler.setLevel(logging.WARNING)
                logger.addHandler(console_handler)

            setattr(logger, "_shipping_configured", True)

        self._logger = logger
        return logger

    def _emit(self, level: str, msg: str, *, extra: dict[str, Any] | None = None, exc: BaseException | None = None) -> None:
        logger = self._ensure_configured()
        lvl = getattr(logging, level, logging.INFO)
        payload = redact(extra, redact_keys=self.redact_keys) if extra is not None else None
        exc_info = None
        if exc is not None:
            exc_info = (type(exc), exc, exc.__traceback__)
        logger.log(lvl, msg, extra={"extra_payload": payload}, exc_info=exc_info)

    def info(self, msg: str, *, extra: dict[str, Any] | None = None) -> None:
        self._emit("INFO", msg, extra=extra)

    def warning(self, msg: str, *, extra: dict[str, Any] | None = None, exc: BaseException | None = None) -> None:
        self._emit("WARNING", msg, extra=extra, exc=exc)

    def error(self, msg: str, *, extra: dict[str, Any] | None = None, exc: BaseException | None = None) -> None:
        self._emit("ERROR", msg, extra=extra, exc=exc)
