from tkinter import BOTH, END, Listbox, MULTIPLE, StringVar, ttk

from scripts.gui_theme import make_log_text, make_scrollable_form, style_listbox


class PreflightUiMixin:

    def _add_dir_row(
        self,
        frm: ttk.Frame,
        row: int,
        label: str,
        var: StringVar,
        browse_cmd,
    ) -> None:
        ttk.Label(frm, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=3)
        entry = ttk.Entry(frm, textvariable=var, width=70)
        entry.grid(row=row, column=1, sticky="we", pady=3)
        ttk.Button(frm, text="Browse…", command=browse_cmd).grid(
            row=row, column=2, padx=(8, 0), pady=3
        )


    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=14)
        outer.pack(fill=BOTH, expand=True)

        footer = ttk.Frame(outer)
        footer.pack(side="bottom", fill="x")

        scroll_container, frm = make_scrollable_form(outer)
        scroll_container.pack(fill=BOTH, expand=True)

        ttk.Label(frm, text="Preflight Issues", style="Title.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 2)
        )
        ttk.Label(
            frm,
            text="Find unmatched SKUs and dry-run missing logo / apparel image issues.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 10))

        ttk.Checkbutton(
            frm,
            text="Testing",
            variable=self.use_demo_images_var,
        ).grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 6))

        ttk.Label(frm, text="Input source:").grid(row=3, column=0, sticky="w", padx=(0, 10), pady=3)
        mode_frame = ttk.Frame(frm)
        mode_frame.grid(row=3, column=1, columnspan=2, sticky="w", pady=3)
        ttk.Radiobutton(
            mode_frame,
            text="CSV file(s)",
            variable=self.input_mode_var,
            value="file",
        ).pack(side="left", padx=(0, 16))
        ttk.Radiobutton(
            mode_frame,
            text="ShipStation tag(s)",
            variable=self.input_mode_var,
            value="tag",
        ).pack(side="left")

        self.tag_label = ttk.Label(frm, text="ShipStation tag(s):")
        self.tag_label.grid(row=4, column=0, sticky="nw", padx=(0, 10), pady=3)
        tag_outer = ttk.Frame(frm)
        tag_outer.grid(row=4, column=1, columnspan=2, sticky="we", pady=3)

        pick_frame = ttk.Frame(tag_outer)
        pick_frame.pack(fill="x")
        self.tag_cb = ttk.Combobox(
            pick_frame, textvariable=self.shipstation_tag_var, state="readonly", width=40
        )
        self.tag_cb.pack(side="left", fill="x", expand=True)
        self.add_tag_btn = ttk.Button(pick_frame, text="Add", command=self._add_selected_tag)
        self.add_tag_btn.pack(side="left", padx=(8, 0))
        self.refresh_tags_btn = ttk.Button(
            pick_frame, text="Refresh tags", command=self._refresh_shipstation_tags
        )
        self.refresh_tags_btn.pack(side="left", padx=(8, 0))

        self.tag_chips_frame = ttk.Frame(tag_outer)
        self.tag_chips_frame.pack(fill="x", expand=True, pady=(6, 0))

        tag_btn_frame = ttk.Frame(tag_outer)
        tag_btn_frame.pack(fill="x", pady=(4, 0))
        self.remove_all_tags_btn = ttk.Button(
            tag_btn_frame, text="Remove all", command=self._remove_all_tags
        )
        self.remove_all_tags_btn.pack(side="left")

        ttk.Label(frm, text="Date (DD-MM-YYYY):").grid(
            row=5, column=0, sticky="w", padx=(0, 10), pady=3
        )
        self.date_entry = ttk.Entry(frm, textvariable=self.date_var, width=20)
        self.date_entry.grid(row=5, column=1, sticky="w", pady=3)

        ttk.Label(frm, text="Shift:").grid(row=6, column=0, sticky="w", padx=(0, 10), pady=3)
        self.shift_cb = ttk.Combobox(
            frm,
            textvariable=self.shift_var,
            values=["1st", "2nd", "3rd", "4th", "5th"],
            state="readonly",
            width=10,
        )
        self.shift_cb.grid(row=6, column=1, sticky="w", pady=3)

        self.process_label = ttk.Label(frm, text="Process number:")
        self.process_label.grid(row=7, column=0, sticky="w", padx=(0, 10), pady=3)
        self.process_entry = ttk.Entry(frm, textvariable=self.process_number_var, width=20)
        self.process_entry.grid(row=7, column=1, sticky="w", pady=3)

        self.input_files_label = ttk.Label(frm, text="Input CSV(s):")
        self.input_files_label.grid(row=8, column=0, sticky="w", padx=(0, 10), pady=3)
        list_frame = ttk.Frame(frm)
        list_frame.grid(row=8, column=1, sticky="nsew", pady=3)
        self.listbox = style_listbox(
            Listbox(list_frame, height=6, width=70, selectmode=MULTIPLE, exportselection=False)
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scroll.set)
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=9, column=1, sticky="w", pady=(0, 6))
        self.add_files_btn = ttk.Button(btn_frame, text="Add files…", command=self._add_files)
        self.add_files_btn.pack(side="left", padx=(0, 6))
        self.remove_selected_btn = ttk.Button(
            btn_frame, text="Remove selected", command=self._remove_selected
        )
        self.remove_selected_btn.pack(side="left", padx=(0, 6))
        self.remove_all_btn = ttk.Button(btn_frame, text="Remove all", command=self._remove_all)
        self.remove_all_btn.pack(side="left")

        self._add_dir_row(frm, 10, "Workbook:", self.workbook_var, self._browse_workbook)
        self._add_dir_row(
            frm,
            11,
            "Custom Label Database (CSV):",
            self.cl_csv_var,
            self._browse_cl_csv,
        )
        self._add_dir_row(frm, 12, "Output directory:", self.output_dir_var, self._browse_output_dir)
        self._add_dir_row(
            frm, 13, "Apparel Image folder:", self.apparel_dir_var, self._browse_apparel_dir
        )
        self._add_dir_row(
            frm,
            14,
            "Normal Design folder:",
            self.logo_normal_dir_var,
            self._browse_logo_normal_dir,
        )
        self._add_dir_row(
            frm,
            15,
            "Customise Single Position Design folder:",
            self.logo_custom_single_dir_var,
            self._browse_logo_custom_single_dir,
        )
        self._add_dir_row(
            frm,
            16,
            "Customise Double Position Design folder:",
            self.logo_custom_double_dir_var,
            self._browse_logo_custom_double_dir,
        )

        frm.columnconfigure(1, weight=1)

        self.run_btn = ttk.Button(footer, text="Run", style="Accent.TButton", command=self._on_run)
        self.run_btn.pack(anchor="w", pady=(8, 6))

        self.log = make_log_text(footer, height=16)
        self.log.insert(
            END,
            "Choose Input source (CSV file(s) or ShipStation tag(s)), set Workbook "
            "(process sheets) and Custom Label Database CSV "
            "(and image folders if checking logos/apparel), then Run.",
        )

        self.input_mode_var.trace_add("write", self._on_input_mode_changed)
        self.shift_var.trace_add("write", self._on_shift_changed)
        self._refresh_tag_chips()
        self._sync_input_mode()

