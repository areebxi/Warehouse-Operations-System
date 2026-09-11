"""
GUI UI builder functions.

This module contains the UI creation logic extracted from queue_app.py
to reduce the main GUI file size.
"""

import tkinter as tk
from tkinter import ttk
from gui_helpers.canvas.gui_ui_builder_preview import build_preview_panel
from gui_helpers.common import gui_theme
from gui_helpers.settings import gui_settings
from src.system.logging.run_logger import log_run_event


def create_ui(gui):
    """Create the main UI for the Queue App application"""
    style = gui_theme.apply_theme(gui.root)
    log_run_event(
        "gui_theme_applied",
        theme=style.theme_use(),
        accent=gui_theme.ACCENT,
        preview_bg=gui_theme.PREVIEW_BG,
    )

    # Main container
    main_frame = ttk.Frame(gui.root, padding="12")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    # Create a canvas and scrollbar for left panel (for responsive scrolling)
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
        # Update canvas window width
        canvas_width = event.width if event else left_canvas.winfo_width()
        left_canvas.itemconfig(
            left_canvas.find_all()[0] if left_canvas.find_all() else None,
            width=canvas_width,
        )

    left_scrollable_frame.bind("<Configure>", update_scroll_region)
    gui.left_container.bind(
        "<Configure>", lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
    )

    canvas_window = left_canvas.create_window(
        (0, 0),
        window=left_scrollable_frame,
        anchor="nw",
    )
    left_canvas.configure(yscrollcommand=left_scrollbar.set)

    def on_canvas_configure(event):
        canvas_width = event.width
        left_canvas.itemconfig(canvas_window, width=canvas_width)

    left_canvas.bind("<Configure>", on_canvas_configure)

    left_canvas.pack(side="left", fill="both", expand=True)
    left_scrollbar.pack(side="right", fill="y")

    # Use left_scrollable_frame for widgets
    left_panel = left_scrollable_frame

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
    ttk.Entry(cl_row, textvariable=gui.cl_csv_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
    ttk.Button(cl_row, text="Browse…", command=gui.select_cl_csv).pack(side=tk.LEFT)

    ttk.Label(db_frame, text="Configuration Workbook:").pack(anchor=tk.W)
    wb_row = ttk.Frame(db_frame)
    wb_row.pack(fill=tk.X, pady=(2, 0))
    ttk.Entry(wb_row, textvariable=gui.config_workbook_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
    ttk.Button(wb_row, text="Browse…", command=gui.select_config_workbook).pack(side=tk.LEFT)

    # Action buttons
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

    # Progress bar frame
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

    # File selection (multi-select, same pattern as Packing List)
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

    # Design folder selection
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

    # Single Design folder selection (for Personalised)
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

    # Double Design folder selection (for Personalised)
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

    # DTF Queues folder selection
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

    # Canvas info
    info_frame = ttk.LabelFrame(left_panel, text="Canvas Information", padding="10")
    info_frame.pack(fill=tk.X, pady=(0, 10))

    gui.canvas_size_label = ttk.Label(
        info_frame,
        text=f"Canvas Size: {gui.canvas_width_mm}mm × {gui.canvas_height_mm}mm",
    )
    gui.canvas_size_label.pack(anchor=tk.W)

    # Canvas width setting
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

    # Canvas height setting
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

    # DPI setting
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

    build_preview_panel(gui, main_frame)

    # Configure grid weights for responsive layout
    gui.root.columnconfigure(0, weight=1)
    gui.root.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=0, minsize=350)  # Left panel minimum width
    main_frame.columnconfigure(1, weight=1)  # Preview panel takes remaining space
    main_frame.rowconfigure(0, weight=1)

    # Make left container responsive
    gui.left_container.columnconfigure(0, weight=1)
    gui.left_container.rowconfigure(0, weight=1)

    # Auto-load saved settings after UI is created
    gui.root.after(100, gui.auto_load_settings)
