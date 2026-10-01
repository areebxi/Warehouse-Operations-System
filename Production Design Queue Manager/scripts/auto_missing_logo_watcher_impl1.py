"""Stable façade for Missing Logo watcher helpers (impl1)."""

from __future__ import annotations

from auto_missing_logo_inbox import _is_inbox_candidate
from auto_missing_logo_loop import watch_loop
from auto_missing_logo_process import (
    _build_ctx,
    _output_stem,
    process_missing_logo_file_headless,
)

__all__ = [
    "_build_ctx",
    "_is_inbox_candidate",
    "_output_stem",
    "process_missing_logo_file_headless",
    "watch_loop",
]
