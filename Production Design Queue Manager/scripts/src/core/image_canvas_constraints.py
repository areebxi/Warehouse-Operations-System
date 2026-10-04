"""Canvas + padding width/height clamps used by image resizing."""

from __future__ import annotations

from typing import List, Optional, Tuple

from src.core.size_reference import COLOR_BAR_WIDTH, COLOR_BAR_SPACING


def apply_canvas_constraints_mm(
    width_px: int,
    height_px: int,
    width_mm: float,
    height_mm: float,
    mm_to_pixel_factor: float,
    *,
    canvas_width_mm: Optional[float],
    canvas_height_mm: Optional[float],
    design_padding: int,
    log_lines: List[str],
) -> Tuple[int, int, float, float]:
    if canvas_width_mm is not None:
        canvas_width_px = int(canvas_width_mm * mm_to_pixel_factor)
        effective_canvas_width_px = canvas_width_px - COLOR_BAR_WIDTH - COLOR_BAR_SPACING
        max_width_px = effective_canvas_width_px - (2 * design_padding)
        if width_px > max_width_px:
            scale_factor = max_width_px / width_px
            log_lines.append(
                f"  canvas width constraint: effective_canvas_width_px={effective_canvas_width_px}px "
                f"(including color bar reservation), max_width_px={max_width_px}px -> "
                f"scale_factor={scale_factor:.4f}"
            )
            width_px = int(width_px * scale_factor)
            height_px = int(height_px * scale_factor)
            width_mm = width_px / mm_to_pixel_factor
            height_mm = height_px / mm_to_pixel_factor

    if canvas_height_mm is not None:
        canvas_height_px = int(canvas_height_mm * mm_to_pixel_factor)
        if height_px > canvas_height_px:
            scale_factor = canvas_height_px / height_px
            log_lines.append(
                f"  canvas height constraint: max_height_px={canvas_height_px}px -> "
                f"scale_factor={scale_factor:.4f}"
            )
            width_px = int(width_px * scale_factor)
            height_px = int(height_px * scale_factor)
            width_mm = width_px / mm_to_pixel_factor
            height_mm = height_px / mm_to_pixel_factor

    return width_px, height_px, width_mm, height_mm
