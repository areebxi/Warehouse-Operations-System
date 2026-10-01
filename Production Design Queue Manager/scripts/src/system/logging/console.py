"""Console log capture setup/teardown — stable façade."""

from __future__ import annotations

from .console_close import close_console_logging
from .console_setup import setup_console_logging
from .console_state import get_console_log_stats, get_console_logs_dir

__all__ = [
    "close_console_logging",
    "get_console_log_stats",
    "get_console_logs_dir",
    "setup_console_logging",
]
