from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple, Union
from PIL import Image
from src.system.logging.utils import get_run_logger

def apply_a3_landscape_transform(
    img: Image.Image, size_info: Dict[str, Any]
) -> Tuple[Image.Image, Dict[str, Any]]:
    """Rotate image 90° and swap size box so A3 pastes in landscape."""
    rotated = img.rotate(90, expand=True)
    swapped = swap_size_info_landscape(size_info)
    swapped["a3_landscape_applied"] = True
    logger = get_run_logger()
    logger.debug(
        "a3_landscape=forced rotate=90 size_box_swapped "
        "original_box=%sx%s swapped_box=%sx%s",
        size_info["width_px"],
        size_info["height_px"],
        swapped["width_px"],
        swapped["height_px"],
    )
    return rotated, swapped
def swap_size_info_landscape(size_info: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of size_info with width/height dimensions swapped."""
    return {
        **size_info,
        "width_mm": size_info["height_mm"],
        "height_mm": size_info["width_mm"],
        "width_px": size_info["height_px"],
        "height_px": size_info["width_px"],
    }
def is_iron_on_order(*labels: Optional[Union[str, int]]) -> bool:
    """True if any label contains 'IronOn' (case-insensitive)."""
    for label in labels:
        if label is None:
            continue
        if IRON_ON_MARKER in str(label).casefold():
            return True
    return False
def is_a3_size(size_info: Optional[Dict[str, Any]]) -> bool:
    """True when size_info refers to A3 paper size."""
    if not size_info:
        return False
    code = str(size_info.get("size_code", "")).strip().upper()
    return code == A3_SIZE_CODE
