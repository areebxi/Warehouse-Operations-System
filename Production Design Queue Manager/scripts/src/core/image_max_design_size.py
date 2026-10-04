"""Global max design size clamp (300×500 mm)."""

from __future__ import annotations

from typing import List, Tuple

MAX_DESIGN_WIDTH_MM = 300.0
MAX_DESIGN_HEIGHT_MM = 500.0


def apply_max_design_size_mm(
    width_px: int,
    height_px: int,
    width_mm: float,
    height_mm: float,
    mm_to_pixel_factor: float,
    *,
    apply_max_design_size: bool,
    log_lines: List[str],
) -> Tuple[int, int, float, float]:
    """Shrink to 300×500 mm when enabled; otherwise log a skip."""
    if width_mm <= MAX_DESIGN_WIDTH_MM and height_mm <= MAX_DESIGN_HEIGHT_MM:
        return width_px, height_px, width_mm, height_mm
    if not apply_max_design_size:
        log_lines.append(
            f"  max design size constraint skipped "
            f"(would be {MAX_DESIGN_WIDTH_MM:.0f}x{MAX_DESIGN_HEIGHT_MM:.0f}mm)"
        )
        return width_px, height_px, width_mm, height_mm
    scale_factor = min(
        MAX_DESIGN_WIDTH_MM / width_mm,
        MAX_DESIGN_HEIGHT_MM / height_mm,
    )
    log_lines.append(
        f"  max design size constraint: {MAX_DESIGN_WIDTH_MM:.0f}x{MAX_DESIGN_HEIGHT_MM:.0f}mm "
        f"-> scale_factor={scale_factor:.4f}"
    )
    width_px = int(width_px * scale_factor)
    height_px = int(height_px * scale_factor)
    width_mm = width_px / mm_to_pixel_factor
    height_mm = height_px / mm_to_pixel_factor
    return width_px, height_px, width_mm, height_mm
