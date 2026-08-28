from tkinter import DISABLED, NORMAL, Listbox, MULTIPLE, ttk



from scripts.gui_theme import make_log_text, make_scrollable_form, style_listbox





def build_ui(app) -> None:

    outer = ttk.Frame(app.root, padding=14)

    outer.pack(fill="both", expand=True)



    footer = ttk.Frame(outer)

    footer.pack(side="bottom", fill="x")



    scroll_container, frm = make_scrollable_form(outer)

    scroll_container.pack(fill="both", expand=True)



    ttk.Label(frm, text="Packing List", style="Title.TLabel").grid(

        row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)

    )

    ttk.Label(

        frm,

        text="Configure paths and options, then run the packing pipeline.",

        style="Muted.TLabel",

    ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))



    def add_row(row: int, label: str, var, browse_dir: bool | None) -> None:

        ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)

        entry = ttk.Entry(frm, textvariable=var, width=55)

        entry.grid(row=row, column=1, sticky="we", pady=3)

        if browse_dir is not None:

            cmd = (lambda v=var: app._browse_directory(v)) if browse_dir else (lambda v=var: app._browse_file(v))

            btn = ttk.Button(frm, text="Browse…", command=cmd)

            btn.grid(row=row, column=2, padx=(8, 0), pady=3)



    frm.columnconfigure(1, weight=1)



    ttk.Label(frm, text="Input source:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=3)

    mode_frame = ttk.Frame(frm)

    mode_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=3)

    app.input_mode_file_rb = ttk.Radiobutton(

        mode_frame,

        text="CSV file(s)",

        variable=app.input_mode_var,

        value="file",

    )

    app.input_mode_file_rb.pack(side="left", padx=(0, 16))

    app.input_mode_tag_rb = ttk.Radiobutton(

        mode_frame,

        text="ShipStation tag(s)",

        variable=app.input_mode_var,

        value="tag",

    )

    app.input_mode_tag_rb.pack(side="left")



    app.tag_label = ttk.Label(frm, text="ShipStation tag(s):")

    app.tag_label.grid(row=3, column=0, sticky="nw", padx=(0, 10), pady=3)

    tag_outer = ttk.Frame(frm)

    tag_outer.grid(row=3, column=1, columnspan=2, sticky="we", pady=3)



    pick_frame = ttk.Frame(tag_outer)

    pick_frame.pack(fill="x")

    app.tag_cb = ttk.Combobox(

        pick_frame, textvariable=app.shipstation_tag_var, state="readonly", width=40

    )

    app.tag_cb.pack(side="left", fill="x", expand=True)

    app.add_tag_btn = ttk.Button(pick_frame, text="Add", command=app._add_selected_tag)

    app.add_tag_btn.pack(side="left", padx=(8, 0))

    app.refresh_tags_btn = ttk.Button(

        pick_frame, text="Refresh tags", command=app._refresh_shipstation_tags

    )

    app.refresh_tags_btn.pack(side="left", padx=(8, 0))



    app.tag_chips_frame = ttk.Frame(tag_outer)

    app.tag_chips_frame.pack(fill="x", expand=True, pady=(6, 0))



    tag_btn_frame = ttk.Frame(tag_outer)

    tag_btn_frame.pack(fill="x", pady=(4, 0))

    app.remove_all_tags_btn = ttk.Button(

        tag_btn_frame, text="Remove all", command=app._remove_all_tags

    )

    app.remove_all_tags_btn.pack(side="left")



    add_row(4, "Date (DD-MM-YYYY):", app.date_var, browse_dir=None)



    ttk.Label(frm, text="Shift:").grid(row=5, column=0, sticky="w", padx=(0, 10), pady=3)

    app.shift_cb = ttk.Combobox(

        frm, textvariable=app.shift_var, values=["1st", "2nd", "3rd", "4th", "5th"], state="readonly", width=10

    )

    app.shift_cb.grid(row=5, column=1, sticky="w", pady=3)



    ttk.Label(frm, text="Use fixed process number:").grid(row=6, column=0, sticky="w", padx=(0, 10), pady=3)

    app.use_fixed_process_cb = ttk.Checkbutton(frm, text="Enable", variable=app.use_fixed_process_number_var)

    app.use_fixed_process_cb.grid(row=6, column=1, sticky="w", pady=3)



    ttk.Label(frm, text="Process number:").grid(row=7, column=0, sticky="w", padx=(0, 10), pady=3)

    app.fixed_process_entry = ttk.Entry(frm, textvariable=app.fixed_process_number_var, width=20)

    app.fixed_process_entry.grid(row=7, column=1, sticky="w", pady=3)



    app.input_label = ttk.Label(frm, text="Input CSV(s):")

    app.input_label.grid(row=8, column=0, sticky="nw", padx=(0, 10), pady=3)

    list_frame = ttk.Frame(frm)

    list_frame.grid(row=8, column=1, columnspan=2, sticky="nsew", pady=3)

    app.input_listbox = style_listbox(

        Listbox(list_frame, height=6, width=55, selectmode=MULTIPLE, exportselection=False)

    )

    app.input_listbox.pack(side="left", fill="both", expand=True)

    input_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=app.input_listbox.yview)

    input_scroll.pack(side="right", fill="y")

    app.input_listbox.config(yscrollcommand=input_scroll.set)



    input_btn_frame = ttk.Frame(frm)

    input_btn_frame.grid(row=9, column=1, columnspan=2, sticky="w", pady=(0, 6))

    app.add_files_btn = ttk.Button(input_btn_frame, text="Add files…", command=app._add_files)

    app.add_files_btn.pack(side="left", padx=(0, 6))

    app.remove_selected_btn = ttk.Button(

        input_btn_frame, text="Remove selected", command=app._remove_selected_files

    )

    app.remove_selected_btn.pack(side="left", padx=(0, 6))

    app.remove_all_btn = ttk.Button(

        input_btn_frame, text="Remove all", command=app._remove_all_files

    )

    app.remove_all_btn.pack(side="left")



    add_row(10, "Workbook path:", app.workbook_var, browse_dir=False)

    ttk.Label(frm, text="Custom Label Database (CSV):").grid(
        row=11, column=0, sticky="w", padx=(0, 10), pady=3
    )
    ttk.Entry(frm, textvariable=app.cl_csv_var, width=55).grid(
        row=11, column=1, sticky="we", pady=3
    )
    ttk.Button(frm, text="Browse…", command=app._browse_cl_csv).grid(
        row=11, column=2, padx=(8, 0), pady=3
    )

    add_row(12, "Output directory:", app.output_dir_var, browse_dir=True)

    ttk.Label(frm, text="Use demo images:").grid(row=13, column=0, sticky="w", padx=(0, 10), pady=3)
    ttk.Checkbutton(
        frm,
        text="Offline testing — placeholders from Demo Images Database/",
        variable=app.use_demo_images_var,
    ).grid(row=13, column=1, columnspan=2, sticky="w", pady=3)

    add_row(14, "Apparel Image folder:", app.apparel_dir_var, browse_dir=True)

    add_row(15, "Normal Logo/Design folder:", app.logo_normal_dir_var, browse_dir=True)

    add_row(16, "Customise Single Position Logo/Design folder:", app.logo_custom_single_dir_var, browse_dir=True)

    add_row(17, "Customise Double Position Logo/Design folder:", app.logo_custom_double_dir_var, browse_dir=True)

    add_row(18, "PDF copy directory (optional):", app.pdf_copy_dir_var, browse_dir=True)

    add_row(19, "Excel copy directory (optional):", app.excel_copy_dir_var, browse_dir=True)



    ttk.Label(frm, text="Separate by Logo ID:").grid(row=20, column=0, sticky="w", padx=(0, 10), pady=3)

    ttk.Checkbutton(frm, text="Enable", variable=app.separate_by_logo_id_var).grid(row=20, column=1, sticky="w", pady=3)



    ttk.Label(frm, text="Logo ID threshold:").grid(row=21, column=0, sticky="w", padx=(0, 10), pady=3)

    app.logo_id_threshold_entry = ttk.Entry(frm, textvariable=app.logo_id_threshold_var, width=8)

    app.logo_id_threshold_entry.grid(row=21, column=1, sticky="w", pady=3)



    ttk.Label(frm, text="Re-run pipeline:").grid(row=22, column=0, sticky="w", padx=(0, 10), pady=3)

    app.run_missing_logo_cb = ttk.Checkbutton(frm, text="Enable", variable=app.run_missing_logo_pipeline_var)

    app.run_missing_logo_cb.grid(row=22, column=1, sticky="w", pady=3)



    btn_frame = ttk.Frame(footer)

    btn_frame.pack(fill="x", pady=(8, 6))

    app.run_btn = ttk.Button(btn_frame, text="Run pipeline", style="Accent.TButton", command=app._on_run_clicked)

    app.run_btn.pack(side="left")



    app.log = make_log_text(footer, height=7)

    app.log.insert(

        "end",

        "Choose Input source (CSV file(s) or ShipStation tag(s)), set Date, Shift, "

        "Workbook (process sheets), Custom Label Database CSV, and image folders, then click Run pipeline.",

    )



    app.use_fixed_process_number_var.trace_add("write", app._on_fixed_process_toggle)

    app.separate_by_logo_id_var.trace_add("write", app._on_separate_by_logo_toggle)

    app.run_missing_logo_pipeline_var.trace_add("write", app._on_missing_pipeline_toggle)

    app.input_mode_var.trace_add("write", app._on_input_mode_changed)

    app.shift_var.trace_add("write", app._on_shift_changed)

    app._refresh_input_listbox()

    app._refresh_tag_chips()

    app._on_fixed_process_toggle()

    app._on_separate_by_logo_toggle()

    app._sync_input_mode()

    if app.is_tag_mode():

        app.root.after(100, app._refresh_shipstation_tags)





def on_fixed_process_toggle(app, *args: object) -> None:

    # Tag mode keeps fixed process enabled; multi-tag disables the entry.

    if getattr(app, "is_tag_mode", lambda: False)():

        app.use_fixed_process_number_var.set(True)

        multi = len(getattr(app, "selected_tags", []) or []) > 1

        if hasattr(app, "fixed_process_entry"):

            app.fixed_process_entry.config(state=DISABLED if multi else NORMAL)

        if hasattr(app, "use_fixed_process_cb"):

            app.use_fixed_process_cb.config(state=DISABLED)

        return

    if hasattr(app, "use_fixed_process_cb"):

        app.use_fixed_process_cb.config(state=NORMAL)

    if app.use_fixed_process_number_var.get():

        app.fixed_process_entry.config(state=NORMAL)

    else:

        app.fixed_process_number_var.set("")

        app.fixed_process_entry.config(state=DISABLED)





def on_separate_by_logo_toggle(app, *args: object) -> None:

    app.logo_id_threshold_entry.config(state=NORMAL if app.separate_by_logo_id_var.get() else DISABLED)


