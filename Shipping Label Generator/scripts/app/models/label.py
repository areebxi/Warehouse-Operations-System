from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Label:
    labelData: str
    trackingNumber: str | None = None
