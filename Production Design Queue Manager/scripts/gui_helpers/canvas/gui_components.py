"""
GUI component utilities for preview drawing and UI helpers.

Implementation moved from the legacy flat/preview location so canvas-related
GUI code is grouped together under `gui_helpers/canvas/`.
"""

import tkinter as tk
from PIL import Image, ImageTk
from typing import List, Dict, Any, Optional, Tuple


def _prepare_batches_for_preview(
    arranged_designs: List[Dict[str, Any]],
    all_batches: List[List[Dict[str, Any]]],
    canvas: tk.Canvas,
) -> List[List[Dict[str, Any]]]:
    """Prepare batches for preview, limiting to 100 designs."""
    if all_batches:
        batches_to_draw = all_batches
    elif arranged_designs:
        batches_to_draw = [arranged_designs]
    else:
        return []

    total_designs = sum(len(batch) for batch in batches_to_draw)
    if total_designs > 100:
        limited_batches = []
        design_count = 0
        for batch in batches_to_draw:
            if design_count >= 100:
                break
            limited_batch = batch[: 100 - design_count]
            limited_batches.append(limited_batch)
            design_count += len(limited_batch)
        batches_to_draw = limited_batches

        canvas.create_text(
            400,
            20,
            text=f"Preview limited to 100 designs (total: {total_designs})",
            font=("Arial", 10),
            fill="orange",
        )

    return batches_to_draw


def _calculate_preview_scale(
    batches_to_draw: List[List[Dict[str, Any]]],
    canvas_width_mm: float,
    canvas_height_mm: float,
    mm_to_pixel_factor: float,
    preview_width: int,
    preview_height: int,
    zoom_level: float,
) -> Tuple[float, float, List[int]]:
    """Calculate scale factor for preview."""
    canvas_width_px = int(canvas_width_mm * mm_to_pixel_factor)
    canvas_height_px = int(canvas_height_mm * mm_to_pixel_factor)

    batch_heights: List[int] = []
    for batch in batches_to_draw:
        if batch:
            max_bottom = max(design["y"] + design["height"] for design in batch)
            batch_heights.append(max_bottom)
        else:
            batch_heights.append(canvas_height_px)

    max_height_px = max(batch_heights) if batch_heights else canvas_height_px

    batch_spacing_px = 200
    border_width = 2
    batch_spacing_px += border_width * 2
    total_width_px = len(batches_to_draw) * canvas_width_px + (len(batches_to_draw) - 1) * batch_spacing_px

    scale_x = preview_width / total_width_px if total_width_px > 0 else preview_width / canvas_width_px
    scale_y = preview_height / max_height_px if max_height_px > 0 else preview_height / canvas_height_px
    base_scale = min(scale_x, scale_y * 0.95)

    scale = base_scale * zoom_level
    return scale, max_height_px, batch_heights


def _draw_batch_header(
    canvas: tk.Canvas,
    batch_num: int,
    total_batches: int,
    current_x_offset_px: float,
    canvas_width_px: int,
    scale: float,
    max_height_px: int,
    left_padding: float = 0,
) -> None:
    """Draw batch label and separator line."""
    if total_batches > 1:
        label_x_scaled = left_padding + current_x_offset_px * scale + (canvas_width_px * scale) / 2
        label_y_scaled = -25
        canvas.create_text(
            label_x_scaled,
            label_y_scaled,
            text=f"Batch {batch_num} / {total_batches}",
            font=("Arial", 12, "bold"),
            fill="red",
        )
        if batch_num > 1:
            separator_x = left_padding + current_x_offset_px * scale
            canvas.create_line(
                separator_x,
                0,
                separator_x,
                max_height_px * scale,
                fill="red",
                width=2,
            )


def _draw_single_design(
    canvas: tk.Canvas,
    design: Dict[str, Any],
    x: float,
    y: float,
    width: float,
    height: float,
    idx: int,
) -> None:
    """Draw a single design in the preview."""
    max_preview_size = 200
    preview_size = (int(width), int(height))

    if preview_size[0] > max_preview_size or preview_size[1] > max_preview_size:
        aspect = width / height if height > 0 else 1
        if width > height:
            preview_size = (max_preview_size, int(max_preview_size / aspect))
        else:
            preview_size = (int(max_preview_size * aspect), max_preview_size)

    if preview_size[0] > 0 and preview_size[1] > 0:
        try:
            img = design["image"].copy()
            img = img.resize(preview_size, Image.Resampling.BILINEAR)
            photo = ImageTk.PhotoImage(img)

            if "photos" not in design:
                design["photos"] = []
            design["photos"].append(photo)

            canvas.create_image(x, y, anchor=tk.NW, image=photo)
        except Exception as e:
            print(f"Error drawing preview for {design.get('sku', 'unknown')}: {e}")
            canvas.create_rectangle(
                x,
                y,
                x + width,
                y + height,
                outline="red",
                width=2,
                fill="lightgray",
            )

        canvas.create_rectangle(
            x, y, x + width, y + height, outline="blue", width=1
        )

        if width > 50 and height > 20:
            canvas.create_text(
                x + width / 2,
                y + height + 10,
                text=str(design["sku"]),
                font=("Arial", 8),
                fill="blue",
            )

    if idx % 10 == 0:
        canvas.update_idletasks()


def draw_preview(
    canvas: tk.Canvas,
    arranged_designs: List[Dict[str, Any]],
    all_batches: List[List[Dict[str, Any]]],
    canvas_width_mm: float,
    canvas_height_mm: float,
    mm_to_pixel_factor: float,
    zoom_level: float = 1.0,
    root: Optional[tk.Tk] = None,
) -> None:
    """Draw preview of arranged designs on canvas."""
    try:
        canvas.delete("all")

        batches_to_draw = _prepare_batches_for_preview(arranged_designs, all_batches, canvas)
        if not batches_to_draw:
            return

        preview_width = canvas.winfo_width()
        preview_height = canvas.winfo_height()
        if preview_width <= 1 or preview_height <= 1:
            preview_width = 800
            preview_height = 600

        scale, max_height_px, _ = _calculate_preview_scale(
            batches_to_draw,
            canvas_width_mm,
            canvas_height_mm,
            mm_to_pixel_factor,
            preview_width,
            preview_height,
            zoom_level,
        )

        canvas_width_px = int(canvas_width_mm * mm_to_pixel_factor)
        batch_spacing_px = 200
        border_width = 2
        batch_spacing_px += border_width * 2

        left_padding = 5
        current_x_offset_px = 0

        for batch_num, batch in enumerate(batches_to_draw, 1):
            if not batch:
                continue

            _draw_batch_header(
                canvas,
                batch_num,
                len(batches_to_draw),
                current_x_offset_px,
                canvas_width_px,
                scale,
                max_height_px,
                left_padding,
            )

            scaled_width = canvas_width_px * scale
            scaled_height = max_height_px * scale
            canvas.create_rectangle(
                left_padding + current_x_offset_px * scale,
                0,
                left_padding + current_x_offset_px * scale + scaled_width,
                scaled_height,
                outline="black",
                width=2,
                fill="white",
            )

            for idx, design in enumerate(batch):
                x = left_padding + current_x_offset_px * scale + design["x"] * scale
                y = design["y"] * scale
                width = design["width"] * scale
                height = design["height"] * scale

                _draw_single_design(canvas, design, x, y, width, height, idx)

            current_x_offset_px += canvas_width_px + batch_spacing_px

        bbox = canvas.bbox("all")
        if bbox:
            scroll_region = (bbox[0] - left_padding, bbox[1], bbox[2] + left_padding, bbox[3])
            canvas.config(scrollregion=scroll_region)
        else:
            canvas.config(scrollregion=canvas.bbox("all"))
    except Exception as e:
        print(f"Error drawing preview: {e}")
        import traceback

        traceback.print_exc()
        canvas.create_text(
            400,
            300,
            text=f"Error drawing preview: {str(e)}",
            font=("Arial", 12),
            fill="red",
        )

