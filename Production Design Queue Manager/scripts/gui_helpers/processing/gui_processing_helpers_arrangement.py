"""Arrangement finalization helpers."""

from typing import List, Dict, Any, Optional
from gui_helpers.common import gui_theme


def finalize_arrangement(gui, batches: List[List[Dict[str, Any]]], show_progress: bool, file_path: Optional[str], mode: str = "standard") -> None:
    if batches:
        gui.all_batches = [list(batch) for batch in batches]
    else:
        gui.all_batches = []
    gui.arranged_designs = batches[0] if batches and len(batches) > 0 else []
    if show_progress:
        from gui_helpers.common.gui_progress import update_progress, reset_progress
        update_progress(gui, 80, "Drawing preview...")
    total_designs = sum(len(batch) for batch in batches) if batches else 0
    mode_text = " (Personalised)" if mode == "personalised" else ""
    if len(batches) > 1:
        gui.stats_label.config(
            text=f"Arranged {total_designs} designs{mode_text} in {len(batches)} batches",
            foreground=gui_theme.FG,
        )
    else:
        gui.stats_label.config(
            text=f"Arranged {total_designs} designs{mode_text} on canvas",
            foreground=gui_theme.FG,
        )
    gui.root.after(100, gui.draw_preview)
    if show_progress:
        from gui_helpers.common.gui_progress import update_progress, reset_progress
        update_progress(gui, 100, "Complete!")
        reset_progress(gui)
    elif file_path:
        gui.save_canvas_for_file(batches, file_path)
