"""Shared run logger utilities."""

import logging
import sys
from typing import Optional, Any

_run_logger: Optional[logging.Logger] = None
_detailed_logging_enabled: bool = True

_EVENT_TITLES = {
    "processing_started": "Processing started",
    "processing_completed": "Processing completed",
    "processing_cancelled": "Processing cancelled",
    "file_loaded": "File loaded",
    "save_completed": "Save completed",
    "save_started": "Save started",
}


def get_run_logger(name: str = "queue_app.run") -> logging.Logger:
    global _run_logger
    if _run_logger is not None:
        return _run_logger
    logger = logging.getLogger(name)
    logger.propagate = False
    logger.setLevel(logging.DEBUG if _detailed_logging_enabled else logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    _run_logger = logger
    return logger


def set_detailed_logging(enabled: bool) -> None:
    global _detailed_logging_enabled, _run_logger
    _detailed_logging_enabled = enabled
    if _run_logger is not None:
        _run_logger.setLevel(logging.DEBUG if enabled else logging.INFO)


def log_run_debug(message: str, *args, **kwargs) -> None:
    get_run_logger().debug(message, *args, **kwargs)


def log_run_info(message: str, *args, **kwargs) -> None:
    get_run_logger().info(message, *args, **kwargs)


def log_run_warning(message: str, *args, **kwargs) -> None:
    get_run_logger().warning(message, *args, **kwargs)


def log_run_error(message: str, *args, **kwargs) -> None:
    get_run_logger().error(message, *args, **kwargs)


def _format_field_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def log_run_event(event: str, level: str = "info", **fields: Any) -> None:
    """Write a human-readable runtime event line."""
    logger = get_run_logger()
    title = _EVENT_TITLES.get(event, event.replace("_", " ").title())
    details = [
        f"{key.replace('_', ' ')}: {_format_field_value(value)}"
        for key, value in fields.items()
        if value is not None
    ]
    message = title
    if details:
        message = f"{title} — {'; '.join(details)}"

    level_name = (level or "info").lower()
    if level_name == "debug":
        logger.debug(message)
    elif level_name == "warning":
        logger.warning(message)
    elif level_name == "error":
        logger.error(message)
    else:
        logger.info(message)
