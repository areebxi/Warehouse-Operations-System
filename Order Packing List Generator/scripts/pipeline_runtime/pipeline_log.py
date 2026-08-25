"""Dual-channel pipeline logging: detail (file / stdout) vs step (GUI progress)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional


class PipelineLog:
    """Every message goes to ``detail``; ``step`` also forwards to ``on_step`` (e.g. GUI queue)."""

    __slots__ = ("_detail", "_on_step")

    def __init__(
        self,
        detail_fn: Callable[[str], None],
        on_step: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._detail = detail_fn
        self._on_step = on_step

    def detail(self, msg: str) -> None:
        self._detail(msg)

    def step(self, msg: str) -> None:
        self._detail(msg)
        if self._on_step is not None:
            self._on_step(msg)


def detail_callable(log: Optional[PipelineLog]) -> Optional[Callable[[str], None]]:
    """Adapt legacy APIs that expect ``Optional[Callable[[str], None]]``."""
    return log.detail if log is not None else None
