"""
GUI canvas settings helper functions.

This module contains canvas size and DPI update functions extracted from
queue_app.py to reduce the main GUI file size.
"""
from tkinter import messagebox

from gui_helpers.common.gui_common import validate_and_update_numeric_var


def update_canvas_size(gui):
    """Update canvas dimensions"""
    old_width = gui.canvas_width_mm
    old_height = gui.canvas_height_mm

    def update_width(new_width):
        gui.canvas_width_mm = new_width
        update_canvas_label(gui)

    width_valid = validate_and_update_numeric_var(
        gui,
        var_attr="canvas_width_var",
        min_val=100,
        max_val=2000,
        gui_value_attr="canvas_width_mm",
        update_func=update_width,
        error_message="Width must be between 100-2000mm, Height must be between 100-10000mm",
    )

    def update_height(new_height):
        gui.canvas_height_mm = new_height
        update_canvas_label(gui)

    height_valid = validate_and_update_numeric_var(
        gui,
        var_attr="canvas_height_var",
        min_val=100,
        max_val=10000,
        gui_value_attr="canvas_height_mm",
        update_func=update_height,
        error_message="Width must be between 100-2000mm, Height must be between 100-10000mm",
    )

    if width_valid and height_valid:
        update_canvas_label(gui)
        if gui.arranged_designs and (
            gui.canvas_width_mm != old_width or gui.canvas_height_mm != old_height
        ):
            messagebox.showinfo(
                "Canvas Size Updated",
                f"Canvas size changed to {gui.canvas_width_mm}mm × {gui.canvas_height_mm}mm. "
                "Please click 'Normal' again to apply new size.",
            )


def update_canvas_label(gui):
    """Update canvas size label text"""
    gui.canvas_size_label.config(
        text=f"Canvas Size: {gui.canvas_width_mm}mm × {gui.canvas_height_mm}mm"
    )


def update_dpi(gui):
    """Update DPI and recalculate mm to pixel conversion"""

    def update_dpi_value(new_dpi):
        gui.dpi = int(new_dpi)
        gui.mm_to_pixel = gui.dpi / 25.4
        if gui.arranged_designs:
            messagebox.showinfo(
                "DPI Updated",
                f"DPI changed to {gui.dpi}. Please click 'Normal' again to apply new sizes.",
            )

    validate_and_update_numeric_var(
        gui,
        var_attr="dpi_var",
        min_val=72,
        max_val=600,
        gui_value_attr="dpi",
        update_func=update_dpi_value,
        error_message="DPI must be between 72 and 600",
    )
