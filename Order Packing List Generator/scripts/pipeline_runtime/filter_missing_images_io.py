"""Helpers for missing-logo / missing-apparel Step 5→6 filter sideline CSVs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import pandas as pd


def write_sideline_csv(
    frames: list[pd.DataFrame],
    output_root: Path,
    filename: str,
    *,
    label: str,
    sibling_pullins: int = 0,
    log: Optional[Callable[[str], None]] = None,
) -> Optional[Path]:
    if not frames:
        if log:
            log(f"  {label}: none.")
        return None
    combined = pd.concat(frames, ignore_index=True, sort=False)
    path = output_root / filename
    combined.to_csv(path, index=False, encoding="utf-8")
    if log:
        extra = (
            f" ({sibling_pullins} merge-sibling pull-in(s))" if sibling_pullins else ""
        )
        log(f"  {label}: wrote {len(combined)} row(s) -> {path.name}{extra}.")
    return path
