"""
System-level services (logging, settings, DI).

This package re-exports legacy flat modules from `src/` so imports can move
to `src.system.*` without breaking existing behavior.
"""

from .logging.utils import (
    setup_error_logging,
    get_run_logger,
    set_detailed_logging,
    setup_console_logging,
    close_console_logging,
)

from .settings_manager import SettingsManager
from .service_factory import create_settings_manager

__all__ = [
    "setup_error_logging",
    "get_run_logger",
    "set_detailed_logging",
    "setup_console_logging",
    "close_console_logging",
    "SettingsManager",
    "create_settings_manager",
]

