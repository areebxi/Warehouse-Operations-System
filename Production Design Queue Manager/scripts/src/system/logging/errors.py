"""Error/warning helpers (no separate error files — console log only)."""

from pathlib import Path
from typing import Optional

_logs_dir: Optional[Path] = None


def _get_project_root() -> Path:
    """Resolve repository root from scripts/src/system/logging module path."""
    return Path(__file__).resolve().parents[4]


def save_error_to_file(content: str, error_type: str = "error") -> None:
    """No-op: errors/warnings are captured in the console log only."""
    return None


from .errors_setup import setup_error_logging
