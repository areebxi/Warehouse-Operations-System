"""Compatibility + controls for preview module."""

from .gui_preview_draw import draw_preview
from .gui_preview_helpers import clear_preview_photo_refs
from gui_helpers.common import gui_theme


def on_mousewheel(gui, event):
    """Scroll the preview canvas (Shift+wheel scrolls horizontally)."""
    canvas = gui.preview_canvas
    # Windows / macOS: event.delta; Linux: event.num 4/5
    if hasattr(event, "delta") and event.delta != 0:
        steps = -1 if event.delta > 0 else 1
    elif getattr(event, "num", None) == 4:
        steps = -1
    elif getattr(event, "num", None) == 5:
        steps = 1
    else:
        return "break"

    shift_held = bool(getattr(event, "state", 0) & 0x1)
    if shift_held:
        canvas.xview_scroll(steps, "units")
    else:
        canvas.yview_scroll(steps, "units")
    return "break"


def on_canvas_resize(gui, event=None):
    """Debounced redraw when the preview canvas is resized."""
    if not (gui.arranged_designs or (hasattr(gui, "all_batches") and gui.all_batches)):
        return

    pending = getattr(gui, "_preview_resize_after_id", None)
    if pending is not None:
        try:
            gui.root.after_cancel(pending)
        except Exception:
            pass

    gui._preview_resize_after_id = gui.root.after(150, lambda: _debounced_redraw(gui))


def _debounced_redraw(gui):
    gui._preview_resize_after_id = None
    if gui.arranged_designs or (hasattr(gui, "all_batches") and gui.all_batches):
        # Reuse composites when scale is unchanged; rebuild on scale miss via cache key
        draw_preview(gui, reuse_cache=True)


def clear_preview(gui):
    """Clear preview canvas and cached preview images."""
    pending = getattr(gui, "_preview_resize_after_id", None)
    if pending is not None:
        try:
            gui.root.after_cancel(pending)
        except Exception:
            pass
        gui._preview_resize_after_id = None

    clear_preview_photo_refs(gui)
    gui.preview_canvas.delete("all")
    gui.arranged_designs = []
    gui.all_batches = []
    gui.input_folder_path = None
    gui.folder_file_batches = {}
    if hasattr(gui, "stats_label"):
        gui.stats_label.config(text="No designs loaded", foreground=gui_theme.MUTED)
    gui.reset_progress()
