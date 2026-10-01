"""Shared mutable state and stream helpers for console logging."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

_console_logs_dir: Optional[Path] = None
_console_log_file: Optional[Any] = None
_original_stdout = None
_original_stderr = None
_console_log_stats: Dict[str, Any] = {
    "errors": 0,
    "warnings": 0,
    "exceptions": 0,
    "error_dialogs": 0,
    "warning_dialogs": 0,
    "tracebacks": 0,
    "start_time": None,
    "end_time": None,
}


def get_console_logs_dir() -> Optional[Path]:
    return _console_logs_dir


def get_console_log_stats() -> Dict[str, Any]:
    return _console_log_stats


def _get_project_root() -> Path:
    """Resolve repository root from scripts/src/system/logging module path."""
    return Path(__file__).resolve().parents[4]


def _safe_stream_write(stream, message: str) -> None:
    """Write to a stream if it exists; ignore missing/broken consoles (e.g. pythonw)."""
    if stream is None or not hasattr(stream, "write"):
        return
    try:
        stream.write(message)
        if hasattr(stream, "flush"):
            stream.flush()
    except Exception:
        pass


def _safe_stream_flush(stream) -> None:
    """Flush a stream if it exists; ignore missing/broken consoles."""
    if stream is None or not hasattr(stream, "flush"):
        return
    try:
        stream.flush()
    except Exception:
        pass
