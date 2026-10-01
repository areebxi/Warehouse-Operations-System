"""Queue GUI left panel: design folders + canvas size controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_left_folders(gui, left_panel) -> None:
    folder_frame = ttk.LabelFrame(left_panel, text="Normal Designs Folder", padding="10")
    folder_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(
        folder_frame,
        text="Select Normal Designs Folder",
        command=gui.select_designs_folder,
    ).pack(fill=tk.X, pady=(0, 6))
    gui.folder_label = ttk.Label(
        folder_frame,
        text="No folder selected",
        style="Muted.TLabel",
    )
    gui.folder_label.pack(pady=(2, 0))

    single_folder_frame = ttk.LabelFrame(
        left_panel, text="Single Designs Folder (Personalised)", padding="10"
    )
    single_folder_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(
        single_folder_frame,
        text="Select Single Designs Folder",
        command=gui.select_single_designs_folder,
    ).pack(fill=tk.X, pady=(0, 6))
    gui.single_folder_label = ttk.Label(
        single_folder_frame,
        text="No folder selected",
        style="Muted.TLabel",
    )
    gui.single_folder_label.pack(pady=(2, 0))

    double_folder_frame = ttk.LabelFrame(
        left_panel, text="Double Designs Folder (Personalised)", padding="10"
    )
    double_folder_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(
        double_folder_frame,
        text="Select Double Designs Folder",
        command=gui.select_double_designs_folder,
    ).pack(fill=tk.X, pady=(0, 6))
    gui.double_folder_label = ttk.Label(
        double_folder_frame,
        text="No folder selected",
        style="Muted.TLabel",
    )
    gui.double_folder_label.pack(pady=(2, 0))

    dtf_queues_frame = ttk.LabelFrame(left_panel, text="DTF Queues Folder", padding="10")
    dtf_queues_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(
        dtf_queues_frame,
        text="Select DTF Queues Folder",
        command=gui.select_dtf_queues_folder,
    ).pack(fill=tk.X, pady=(0, 6))
    ttk.Button(
        dtf_queues_frame,
        text="Remove DTF Queues Folder",
        style="Secondary.TButton",
        command=gui.remove_dtf_queues_folder,
    ).pack(fill=tk.X, pady=(0, 6))
    gui.dtf_queues_label = ttk.Label(
        dtf_queues_frame,
        text="No folder selected",
        style="Muted.TLabel",
    )
    gui.dtf_queues_label.pack(pady=(2, 0))

    info_frame = ttk.LabelFrame(left_panel, text="Canvas Information", padding="10")
    info_frame.pack(fill=tk.X, pady=(0, 10))

    gui.canvas_size_label = ttk.Label(
        info_frame,
        text=f"Canvas Size: {gui.canvas_width_mm}mm × {gui.canvas_height_mm}mm",
    )
    gui.canvas_size_label.pack(anchor=tk.W)

    width_frame = ttk.Frame(info_frame)
    width_frame.pack(fill=tk.X, pady=(6, 0))
    ttk.Label(width_frame, text="Width (mm):").pack(side=tk.LEFT, padx=(0, 5))
    gui.canvas_width_var = tk.StringVar(value=str(gui.canvas_width_mm))
    width_spinbox = ttk.Spinbox(
        width_frame,
        from_=100,
        to=2000,
        textvariable=gui.canvas_width_var,
        width=10,
        command=gui.update_canvas_size,
    )
    width_spinbox.pack(side=tk.LEFT)
    width_spinbox.bind("<Return>", lambda e: gui.update_canvas_size())

    height_frame = ttk.Frame(info_frame)
    height_frame.pack(fill=tk.X, pady=(6, 0))
    ttk.Label(height_frame, text="Height (mm):").pack(side=tk.LEFT, padx=(0, 5))
    gui.canvas_height_var = tk.StringVar(value=str(gui.canvas_height_mm))
    height_spinbox = ttk.Spinbox(
        height_frame,
        from_=100,
        to=10000,
        textvariable=gui.canvas_height_var,
        width=10,
        command=gui.update_canvas_size,
    )
    height_spinbox.pack(side=tk.LEFT)
    height_spinbox.bind("<Return>", lambda e: gui.update_canvas_size())

    dpi_frame = ttk.Frame(info_frame)
    dpi_frame.pack(fill=tk.X, pady=(6, 0))
    ttk.Label(dpi_frame, text="DPI:").pack(side=tk.LEFT, padx=(0, 5))
    gui.dpi_var = tk.StringVar(value=str(gui.dpi))
    dpi_spinbox = ttk.Spinbox(
        dpi_frame,
        from_=72,
        to=600,
        textvariable=gui.dpi_var,
        width=10,
        command=gui.update_dpi,
    )
    dpi_spinbox.pack(side=tk.LEFT)
    dpi_spinbox.bind("<Return>", lambda e: gui.update_dpi())
    ttk.Label(
        dpi_frame,
        text="(for printing)",
        style="Hint.TLabel",
    ).pack(side=tk.LEFT, padx=(5, 0))
