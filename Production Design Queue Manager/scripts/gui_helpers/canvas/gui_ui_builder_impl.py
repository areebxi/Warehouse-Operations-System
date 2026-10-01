"""
GUI UI builder functions.

This module contains the UI creation logic extracted from queue_app.py
to reduce the main GUI file size.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui_helpers.canvas.gui_ui_builder_controls import build_left_controls
from gui_helpers.canvas.gui_ui_builder_folders import build_left_folders
from gui_helpers.canvas.gui_ui_builder_preview import build_preview_panel
from gui_helpers.common import gui_theme
from src.system.logging.run_logger import log_run_event


def create_ui(gui) -> None:
    style = gui_theme.apply_theme(gui.root)
    log_run_event(
        "gui_theme_applied",
        theme=style.theme_use(),
        accent=gui_theme.ACCENT,
        preview_bg=gui_theme.PREVIEW_BG,
    )

    main_frame = ttk.Frame(gui.root, padding="12")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    gui.left_container = ttk.Frame(main_frame)
    gui.left_container.grid(
        row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 12)
    )

    left_canvas = tk.Canvas(
        gui.left_container,
        highlightthickness=0,
        bd=0,
        bg=gui_theme.BG,
    )
    left_scrollbar = ttk.Scrollbar(
        gui.left_container,
        orient="vertical",
        command=left_canvas.yview,
    )
    left_scrollable_frame = ttk.Frame(left_canvas, padding="8")

    def update_scroll_region(event=None):
        left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        canvas_width = event.width if event else left_canvas.winfo_width()
        if left_canvas.find_all():
            left_canvas.itemconfig(left_canvas.find_all()[0], width=canvas_width)

    left_scrollable_frame.bind("<Configure>", update_scroll_region)
    gui.left_container.bind(
        "<Configure>",
        lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all")),
    )

    canvas_window = left_canvas.create_window(
        (0, 0),
        window=left_scrollable_frame,
        anchor="nw",
    )
    left_canvas.configure(yscrollcommand=left_scrollbar.set)

    def on_canvas_configure(event):
        left_canvas.itemconfig(canvas_window, width=event.width)

    left_canvas.bind("<Configure>", on_canvas_configure)
    left_canvas.pack(side="left", fill="both", expand=True)
    left_scrollbar.pack(side="right", fill="y")

    left_panel = left_scrollable_frame
    build_left_controls(gui, left_panel)
    build_left_folders(gui, left_panel)
    build_preview_panel(gui, main_frame)

    gui.root.columnconfigure(0, weight=1)
    gui.root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=0, minsize=350)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)
    gui.left_container.columnconfigure(0, weight=1)
    gui.left_container.rowconfigure(0, weight=1)
    gui.root.after(100, gui.auto_load_settings)
