"""Helper functions for preview drawing."""

from PIL import Image, ImageDraw, ImageFont, ImageTk
from gui_helpers.common.gui_theme import PREVIEW_BG, PREVIEW_BG_RGBA

LEFT_PADDING = 5
RIGHT_PADDING = 8
# Room for the 2px batch outline (Tk draws outline centered on the edge)
OUTLINE_ALLOWANCE = 4
BATCH_SPACING_PX = 204  # 200 + border allowance
# Default view is zoomed out from fitting one batch width
DEFAULT_PREVIEW_ZOOM = 0.475


def calculate_preview_scale(gui, batches_to_draw, canvas_width_px, canvas_height_px):
    """Fit one batch width to the preview panel (slightly zoomed out); scroll for the rest."""
    preview_width = gui.preview_canvas.winfo_width()
    if preview_width <= 1:
        preview_width = 800

    batch_heights = []
    for batch in batches_to_draw:
        if batch:
            max_bottom = max(design["y"] + design["height"] for design in batch)
            batch_heights.append(max_bottom)
        else:
            batch_heights.append(canvas_height_px)
    max_height_px = max(batch_heights) if batch_heights else canvas_height_px

    # Leave left/right margin so the black outline is not clipped by the viewport edge
    usable_width = max(
        preview_width - LEFT_PADDING - RIGHT_PADDING - OUTLINE_ALLOWANCE,
        1,
    )
    scale = usable_width / canvas_width_px if canvas_width_px > 0 else 1.0
    scale *= DEFAULT_PREVIEW_ZOOM
    return scale, max_height_px, BATCH_SPACING_PX


def build_batch_preview_image(batch, canvas_width_px, max_height_px, scale):
    """Composite all designs in a batch into one scaled preview image."""
    out_w = max(int(canvas_width_px * scale), 1)
    out_h = max(int(max_height_px * scale), 1)
    composite = Image.new("RGBA", (out_w, out_h), PREVIEW_BG_RGBA)
    draw = ImageDraw.Draw(composite)

    try:
        font = ImageFont.truetype("arial.ttf", 10)
    except OSError:
        font = ImageFont.load_default()

    for design in batch:
        x = int(design["x"] * scale)
        y = int(design["y"] * scale)
        box_w = max(int(design["width"] * scale), 1)
        box_h = max(int(design["height"] * scale), 1)

        try:
            src = design["image"]
            if src.mode != "RGBA":
                src = src.convert("RGBA")
            thumb = src.resize((box_w, box_h), Image.Resampling.BILINEAR)
            composite.paste(thumb, (x, y), thumb)
            draw.rectangle([x, y, x + box_w - 1, y + box_h - 1], outline=(0, 0, 0, 255), width=1)
            if box_w > 50 and box_h > 20:
                sku = str(design.get("sku", ""))
                if sku:
                    draw.text(
                        (x + box_w / 2, y - 2),
                        sku,
                        fill=(0, 0, 0, 255),
                        font=font,
                        anchor="mb",
                    )
        except Exception:
            draw.rectangle(
                [x, y, x + box_w, y + box_h],
                outline=(255, 0, 0, 255),
                width=2,
                fill=(200, 200, 200, 255),
            )

    return ImageTk.PhotoImage(composite)


def get_cached_batch_photo(gui, cache_key, builder):
    """Return a cached PhotoImage for cache_key, or build and store it."""
    cache = getattr(gui, "_preview_photo_cache", None)
    if cache is None:
        cache = {}
        gui._preview_photo_cache = cache
    if cache_key in cache:
        return cache[cache_key]
    photo = builder()
    cache[cache_key] = photo
    return photo


def clear_preview_photo_refs(gui):
    """Drop PhotoImage references so Tk can free them."""
    gui._preview_photos = []
    gui._preview_photo_cache = {}
