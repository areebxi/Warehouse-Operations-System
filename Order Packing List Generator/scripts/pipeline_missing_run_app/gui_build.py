"""Missing Run GUI form layout."""

from __future__ import annotations

from tkinter import BOTH, END, StringVar, ttk

from scripts.gui_theme import make_log_text, make_scrollable_form


def build_missing_run_ui(app) -> None:
    outer = ttk.Frame(app.root, padding=14)
    outer.pack(fill=BOTH, expand=True)

    footer = ttk.Frame(outer)
    footer.pack(side="bottom", fill="x")

    scroll_container, frm = make_scrollable_form(outer)
    scroll_container.pack(fill=BOTH, expand=True)

    ttk.Label(frm, text="Missing Run", style="Title.TLabel").grid(
        row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)
    )
    ttk.Label(
        frm,
        text="Run a missing subset through the packing pipeline.",
        style="Muted.TLabel",
    ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

    def add_row(row: int, label: str, var: StringVar, browse_for_dir: bool | None) -> None:
        ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Entry(frm, textvariable=var, width=60).grid(row=row, column=1, sticky="we", pady=3)
        if browse_for_dir:
            ttk.Button(
                frm, text="Browse…", command=lambda v=var: app._browse_directory(v)
            ).grid(row=row, column=2, padx=(8, 0), pady=3)

    ttk.Checkbutton(
        frm,
        text="Testing",
        variable=app.use_demo_images_var,
    ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 6))

    ttk.Label(frm, text="Missing type:").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=3)
    type_frame = ttk.Frame(frm)
    type_frame.grid(row=3, column=1, columnspan=2, sticky="w", pady=3)
    ttk.Radiobutton(
        type_frame, text="Missing Logo", variable=app.missing_type_var, value="Missing Logo"
    ).pack(side="left", padx=(0, 16))
    ttk.Radiobutton(
        type_frame, text="Missing Apparel", variable=app.missing_type_var, value="Missing Apparel"
    ).pack(side="left")
    ttk.Label(frm, text="Date (DD-MM-YYYY):").grid(row=4, column=0, sticky="w", padx=(0, 10), pady=3)
    ttk.Entry(frm, textvariable=app.date_var, width=25).grid(row=4, column=1, sticky="w", pady=3)
    ttk.Label(frm, text="Shift:").grid(row=5, column=0, sticky="w", padx=(0, 10), pady=3)
    app.shift_cb = ttk.Combobox(
        frm,
        textvariable=app.shift_var,
        values=["1st", "2nd", "3rd", "4th", "5th"],
        state="readonly",
        width=10,
    )
    app.shift_cb.grid(row=5, column=1, sticky="w", pady=3)
    ttk.Label(frm, text="Process name:").grid(row=6, column=0, sticky="w", padx=(0, 10), pady=3)
    ttk.Entry(frm, textvariable=app.process_name_var, width=60).grid(
        row=6, column=1, sticky="we", pady=3, columnspan=2
    )
    ttk.Label(frm, text="Missing Input CSV:").grid(row=7, column=0, sticky="w", padx=(0, 10), pady=3)
    ttk.Entry(frm, textvariable=app.missing_input_var, width=60).grid(
        row=7, column=1, sticky="we", pady=3
    )
    ttk.Button(frm, text="Browse…", command=app._browse_missing_input).grid(
        row=7, column=2, padx=(8, 0), pady=3
    )
    ttk.Label(frm, text="All Orders CSV:").grid(row=8, column=0, sticky="w", padx=(0, 10), pady=3)
    ttk.Entry(frm, textvariable=app.all_orders_var, width=60).grid(
        row=8, column=1, sticky="we", pady=3
    )
    ttk.Button(frm, text="Browse…", command=app._browse_all_orders).grid(
        row=8, column=2, padx=(8, 0), pady=3
    )
    add_row(9, "Apparel Image folder:", app.apparel_dir_var, browse_for_dir=True)
    add_row(10, "Normal Design folder:", app.logo_normal_dir_var, browse_for_dir=True)
    add_row(
        11,
        "Customise Single Position Design folder:",
        app.logo_custom_single_dir_var,
        browse_for_dir=True,
    )
    add_row(
        12,
        "Customise Double Position Design folder:",
        app.logo_custom_double_dir_var,
        browse_for_dir=True,
    )
    add_row(13, "PDF copy directory (optional):", app.pdf_copy_dir_var, browse_for_dir=True)
    ttk.Label(
        frm,
        text="PDFs copy into {PDF copy dir}/Missing Logo or …/Missing Apparel when set.",
        style="Muted.TLabel",
    ).grid(row=14, column=1, columnspan=2, sticky="w", pady=(0, 3))
    add_row(15, "Excel copy directory (optional):", app.excel_copy_dir_var, browse_for_dir=True)
    frm.columnconfigure(1, weight=1)

    app.run_btn = ttk.Button(
        footer, text="Run missing pipeline", style="Accent.TButton", command=app._on_run
    )
    app.run_btn.pack(anchor="w", pady=(8, 6))
    app.log = make_log_text(footer, height=10)
    app.log.insert(END, "Set Date, Shift, Process name, and CSV paths, then click 'Run missing pipeline'.")
