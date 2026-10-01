"""Queue GUI left panel: database, actions, progress, input files."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui_helpers.common import gui_theme
from gui_helpers.settings import gui_settings


def build_left_controls(gui, left_panel) -> None:
    offline_frame = ttk.Frame(left_panel)
    offline_frame.pack(fill=tk.X, pady=(0, 10))
    gui.use_demo_images_var = tk.BooleanVar(
        value=bool(getattr(gui, "saved_settings", {}).get("use_demo_images"))
    )
    ttk.Checkbutton(
        offline_frame,
        text="Testing",
        variable=gui.use_demo_images_var,
        command=lambda: gui_settings.on_offline_testing_toggle(gui),
    ).pack(anchor=tk.W)

    db_frame = ttk.LabelFrame(left_panel, text="Database", padding="10")
    db_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Label(db_frame, text="Custom Label Database (CSV):").pack(anchor=tk.W)
    cl_row = ttk.Frame(db_frame)
    cl_row.pack(fill=tk.X, pady=(2, 6))
    ttk.Entry(cl_row, textvariable=gui.cl_csv_var).pack(
        side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6)
    )
    ttk.Button(cl_row, text="Browse…", command=gui.select_cl_csv).pack(side=tk.LEFT)

    ttk.Label(db_frame, text="Configuration Workbook:").pack(anchor=tk.W)
    wb_row = ttk.Frame(db_frame)
    wb_row.pack(fill=tk.X, pady=(2, 0))
    ttk.Entry(wb_row, textvariable=gui.config_workbook_var).pack(
        side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6)
    )
    ttk.Button(wb_row, text="Browse…", command=gui.select_config_workbook).pack(side=tk.LEFT)

    action_frame = ttk.LabelFrame(left_panel, text="Actions", padding="10")
    action_frame.pack(fill=tk.X, pady=(0, 10))

    ttk.Button(
        action_frame,
        text="Run",
        style="Accent.TButton",
        command=gui.arrange_missing_logo_designs,
    ).pack(fill=tk.X, pady=(0, 6))
    ttk.Button(
        action_frame,
        text="Save PNG(s)",
        style="Secondary.TButton",
        command=gui.save_canvas_image,
    ).pack(fill=tk.X, pady=(0, 6))
    ttk.Button(
        action_frame,
        text="Clear Preview",
        style="Quiet.TButton",
        command=gui.clear_preview,
    ).pack(fill=tk.X, pady=(0, 4))

    gui.stats_label = ttk.Label(
        action_frame,
        text="No designs loaded",
        style="Muted.TLabel",
    )
    gui.stats_label.pack(anchor=tk.W, pady=(4, 0))

    progress_frame = ttk.LabelFrame(left_panel, text="Progress", padding="10")
    progress_frame.pack(fill=tk.X, pady=(0, 10))

    gui.progress_var = tk.DoubleVar()
    gui.progress_bar = ttk.Progressbar(
        progress_frame,
        variable=gui.progress_var,
        maximum=100,
        length=200,
        mode="determinate",
    )
    gui.progress_bar.pack(fill=tk.X, pady=5)

    gui.progress_label = ttk.Label(
        progress_frame,
        text="Ready",
        style="Muted.TLabel",
        width=48,
        anchor="w",
    )
    gui.progress_label.pack(fill=tk.X, pady=(0, 5))

    file_frame = ttk.LabelFrame(left_panel, text="Input Files", padding="10")
    file_frame.pack(fill=tk.X, pady=(0, 10))

    list_frame = ttk.Frame(file_frame)
    list_frame.pack(fill=tk.BOTH, expand=True)
    gui.input_listbox = tk.Listbox(
        list_frame,
        height=4,
        selectmode=tk.EXTENDED,
        exportselection=False,
        bg=gui_theme.SURFACE,
        fg=gui_theme.FG,
        highlightthickness=1,
        highlightbackground=gui_theme.BORDER,
        relief="flat",
        font=gui_theme.FONT_HINT,
    )
    gui.input_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    input_scroll = ttk.Scrollbar(
        list_frame, orient="vertical", command=gui.input_listbox.yview
    )
    input_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    gui.input_listbox.config(yscrollcommand=input_scroll.set)

    ttk.Button(
        file_frame,
        text="Add files…",
        command=gui.add_input_files,
    ).pack(fill=tk.X, pady=(6, 0))
    ttk.Button(
        file_frame,
        text="Remove selected",
        command=gui.remove_selected_input_files,
    ).pack(fill=tk.X, pady=(6, 0))
    ttk.Button(
        file_frame,
        text="Remove all",
        command=gui.remove_all_input_files,
    ).pack(fill=tk.X, pady=(6, 0))

    gui.file_label = ttk.Label(
        file_frame,
        text="No files selected",
        style="Muted.TLabel",
    )
    gui.file_label.pack(anchor=tk.W, pady=(6, 0))
