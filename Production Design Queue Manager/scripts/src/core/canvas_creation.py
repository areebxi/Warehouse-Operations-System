"""
Canvas creation utilities for creating and saving canvas images with arranged designs.

This module:
- creates a transparent RGBA canvas sized to content + text
- draws optional DES/ PART labels
- pastes arranged design images
- optionally adds the Color Bar on the right
"""
from PIL import Image, ImageDraw, ImageFont
from tkinter import messagebox
from typing import Optional, Dict, List, Any, Callable

from src.system.logging.utils import get_run_logger


def _calculate_canvas_height(
    arranged_designs: List[Dict[str, Any]],
    text_height: int
) -> int:
    bottom_padding = 100
    max_bottom = 0

    for design in arranged_designs:
        design_bottom = design['y'] + design['height']
        if design_bottom > max_bottom:
            max_bottom = design_bottom

    y_offset = text_height if text_height > 0 else 0
    required_height = int(y_offset + max_bottom + bottom_padding)

    # Safety check: ensure height is reasonable (max 100000 pixels)
    if required_height > 100000:
        messagebox.showwarning(
            "Warning",
            "Canvas height limited to 100000 pixels. Some designs may be cut off.",
        )
        return 100000

    return required_height


def _load_font(font_size: int = 160) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
    except (OSError, IOError):
        try:
            return ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
        except (OSError, IOError):
            try:
                return ImageFont.truetype("C:/Windows/Fonts/calibrib.ttf", font_size)
            except (OSError, IOError):
                try:
                    return ImageFont.truetype("arial.ttf", font_size)
                except (OSError, IOError):
                    return ImageFont.load_default()


def _draw_canvas_text(
    draw: ImageDraw.ImageDraw,
    des_text: Optional[str],
    part_text: Optional[str],
    font: ImageFont.FreeTypeFont
) -> None:
    text_y = 20
    text_color = (0, 0, 0)  # Black

    text_parts = []
    if des_text:
        text_parts.append(str(des_text).strip().upper())
    if part_text:
        text_parts.append(str(part_text).strip().upper())

    if text_parts:
        combined_text = "  ".join(text_parts)
        draw.text((20, text_y), combined_text, fill=text_color, font=font)


def _paste_designs(
    canvas_image: Image.Image,
    arranged_designs: List[Dict[str, Any]],
    y_offset: int
) -> None:
    for design in arranged_designs:
        x = design['x']
        y = y_offset + design['y']
        img = design['image']

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Alpha-aware paste
        canvas_image.paste(img, (x, y), img)


def _add_color_bar(
    canvas_image: Image.Image,
    color_bar_image: Image.Image,
    text_y: int
) -> None:
    try:
        color_bar = color_bar_image.copy()
        if color_bar.mode != 'RGBA':
            color_bar = color_bar.convert('RGBA')

        actual_canvas_width = canvas_image.width
        color_bar_width = color_bar.width
        color_bar_x = actual_canvas_width - color_bar_width
        color_bar_y = text_y

        if color_bar_x < 0:
            color_bar_x = 0

        canvas_image.paste(color_bar, (int(color_bar_x), int(color_bar_y)), color_bar)
    except Exception as e:
        print(f"Error adding Color Bar to canvas: {e}")


def create_canvas_image(
    arranged_designs: List[Dict[str, Any]],
    canvas_width_mm: float,
    canvas_height_mm: float,
    mm_to_pixel_factor: float,
    dpi: int,
    color_bar_image: Optional[Image.Image] = None,
    des_text: Optional[str] = None,
    part_text: Optional[str] = None,
    extract_text_func: Optional[Callable[[str], str]] = None
) -> Image.Image:
    if not arranged_designs:
        raise ValueError("No designs to save!")

    logger = get_run_logger()
    logger.debug(
        "create_canvas_image: designs_count=%s, canvas_width_mm=%.2f, "
        "canvas_height_mm=%.2f, dpi=%s, has_color_bar=%s, des_text=%s, part_text=%s",
        len(arranged_designs),
        canvas_width_mm,
        canvas_height_mm,
        dpi,
        bool(color_bar_image),
        des_text,
        part_text,
    )

    canvas_width_px = int(canvas_width_mm * mm_to_pixel_factor)
    text_height = 200 if (des_text or part_text) else 0
    actual_height = _calculate_canvas_height(arranged_designs, text_height)

    canvas_image = Image.new('RGBA', (canvas_width_px, actual_height), (255, 255, 255, 0))

    if text_height > 0:
        draw = ImageDraw.Draw(canvas_image)
        font = _load_font()
        _draw_canvas_text(draw, des_text, part_text, font)

    y_offset = text_height if text_height > 0 else 0
    _paste_designs(canvas_image, arranged_designs, y_offset)

    if color_bar_image:
        _add_color_bar(canvas_image, color_bar_image, 20)

    canvas_image = canvas_image.crop((0, 0, canvas_width_px, actual_height))

    logger.debug(
        "create_canvas_image: final canvas size -> %dx%d px, designs_count=%s",
        canvas_width_px,
        actual_height,
        len(arranged_designs),
    )

    return canvas_image


def save_canvas_image(canvas_image: Image.Image, save_path: str, dpi: int) -> None:
    # compress_level=1: lossless PNG, much faster than default (6) on huge canvases
    canvas_image.save(
        save_path,
        'PNG',
        dpi=(dpi, dpi),
        compress_level=1,
        optimize=False,
    )

