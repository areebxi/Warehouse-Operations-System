"""Stable façade for Missing Logo watcher helpers (impl2)."""

from __future__ import annotations

from auto_missing_logo_inbox import (
    _inbox_root,
    _iter_inbox_files,
    _move_to,
    _rel_date_shift,
    _setup_logging,
    _wait_stable,
)
from auto_missing_logo_loop import process_one, run_once
from auto_missing_logo_process import _save_batches

__all__ = [
    "_inbox_root",
    "_iter_inbox_files",
    "_move_to",
    "_rel_date_shift",
    "_save_batches",
    "_setup_logging",
    "_wait_stable",
    "process_one",
    "run_once",
]
