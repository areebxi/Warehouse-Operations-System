"""Preview panel builder for the Queue App UI."""

import tkinter as tk
from tkinter import ttk


def build_preview_panel(gui, main_frame):
    """Build right-side preview panel and canvas widgets."""
    preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding="10")
    preview_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))

    canvas_container = ttk.Frame(preview_frame)
    canvas_container.pack(fill=tk.BOTH, expand=True)

    v_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
    v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
    h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    from gui_helpers.canvas.gui_preview_helpers import PREVIEW_BG

    gui.preview_canvas = tk.Canvas(
        canvas_container,
        bg=PREVIEW_BG,
        yscrollcommand=v_scrollbar.set,
        xscrollcommand=h_scrollbar.set,
    )
    gui.preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    v_scrollbar.config(command=gui.preview_canvas.yview)
    h_scrollbar.config(command=gui.preview_canvas.xview)

    gui.preview_canvas.bind("<Configure>", gui.on_canvas_resize)
    gui.preview_canvas.bind("<MouseWheel>", gui.on_mousewheel)
    gui.preview_canvas.bind("<Shift-MouseWheel>", gui.on_mousewheel)
    gui.preview_canvas.bind("<Button-4>", gui.on_mousewheel)
    gui.preview_canvas.bind("<Button-5>", gui.on_mousewheel)
    gui.preview_canvas.focus_set()
