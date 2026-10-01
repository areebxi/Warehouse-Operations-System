"""Shared constants + low-level draw helpers for apparel/logo PDF cells."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Callable, Optional

_LOGO_FIELDS = (
    "Logo/Design Image (1st)",
    "Logo/Design Image (2nd)",
    "Logo/Design Image (3rd)",
    "Logo/Design Image (4th)",
    "Logo/Design Image (5th)",
)

_SLOT_LABELS = (
    "logo slot 1 (1st)",
    "logo slot 2 (2nd)",
    "logo slot 3 (3rd)",
    "logo slot 4 (4th)",
    "logo slot 5 (5th)",
)


def _pdf_asset_log_line(log: Optional[Callable[[str], None]], line: str) -> None:
    if not log:
        return
    try:
        log(line)
    except Exception:
        pass


def _draw_prepared_image(
    c,
    prepared: object,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    image_reader_cls,
) -> None:
    if isinstance(prepared, io.BytesIO):
        c.drawImage(
            image_reader_cls(prepared),
            lx,
            ly,
            width=lw,
            height=lh,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )
    else:
        c.drawImage(
            str(prepared),
            lx,
            ly,
            width=lw,
            height=lh,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )


def _draw_red_margin(c, lx: float, ly: float, lw: float, lh: float) -> None:
    line_w = max(1.5, min(lw, lh) * 0.02)
    c.setStrokeColorRGB(1, 0, 0)
    c.setLineWidth(line_w)
    c.rect(lx, ly, lw, lh, fill=0, stroke=1)


def _draw_back_print_reference(
    c,
    ref_path: Path,
    lx: float,
    ly: float,
    lw: float,
    lh: float,
    *,
    prepare_image: Callable[..., object],
    image_reader_cls,
) -> None:
    prepared_ref = prepare_image(ref_path, lw, lh)
    _draw_prepared_image(c, prepared_ref, lx, ly, lw, lh, image_reader_cls)
    _draw_red_margin(c, lx, ly, lw, lh)
