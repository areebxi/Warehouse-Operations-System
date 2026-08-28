import json
import queue
import sys
import threading
from datetime import date, datetime
from pathlib import Path
from tkinter import (
    BOTH,
    DISABLED,
    END,
    NORMAL,
    Listbox,
    MULTIPLE,
    StringVar,
    Tk,
    BooleanVar,
    filedialog,
    messagebox,
    ttk,
)

from scripts.gui_theme import (
    apply_theme,
    make_log_text,
    make_scrollable_form,
    refresh_tag_chip_grid,
    set_listbox_enabled,
    set_tag_chip_grid_enabled,
    style_listbox,
)
from scripts.pipeline_runtime.runner_utils import (
    _FILENAME_UNSAFE,
    _shift_subdir_name,
)
from scripts.pipeline_shipstation.client import ShipStationClient
from scripts.pipeline_shipstation.credentials import load_shipstation_credentials
from scripts.pipeline_shipstation.orders_to_csv import fetch_tag_orders_to_csv
from scripts.pipeline_shipstation.sync_tags_xlsx import DEFAULT_XLSX_PATH
from scripts.pipeline_shipstation.tags_process_lookup import (
    lookup_process_number,
    parse_shipstation_tags_config,
    resolve_tag_list_processes,
    shipstation_tags_config_payload,
)

from .config import (
    CONFIG_DIR,
    DEFAULT_CL_CSV,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_WORKBOOK,
    NO_ISSUES,
    PREFLIGHT_CONFIG,
    PROJECT_ROOT,
    UNMATCHED_CONFIG,
)
from .service import PreflightResult, run_preflight_audit


class PreflightIssuesApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Preflight Issues App")

        self.input_paths: list[Path] = []
        self.workbook_var = StringVar(value=str(DEFAULT_WORKBOOK))
        self.cl_csv_var = StringVar(value=str(DEFAULT_CL_CSV))
        self.output_dir_var = StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.apparel_dir_var = StringVar()
        self.logo_normal_dir_var = StringVar()
        self.logo_custom_single_dir_var = StringVar()
        self.logo_custom_double_dir_var = StringVar()
        self.use_demo_images_var = BooleanVar(value=False)
        self.date_var = StringVar(value=date.today().strftime("%d-%m-%Y"))
        self.shift_var = StringVar()
        self.process_number_var = StringVar()
        self.input_mode_var = StringVar(value="file")  # "file" | "tag"
        self.shipstation_tag_var = StringVar()  # Combobox pick
        self.selected_tags: list[tuple[int, str]] = []
        self._shipstation_tags: list[dict] = []
        self._tags_loading = False
        self._syncing_inputs = False
        self._log_queue: queue.Queue[str | None] | None = None
        self._run_result = None

        self._load_config()

        self._build_ui()
        self._refresh_input_listbox()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        if self.is_tag_mode():
            self.root.after(100, self._refresh_shipstation_tags)

    def _load_config(self) -> None:
        path_candidates = [
            PREFLIGHT_CONFIG,
            UNMATCHED_CONFIG,
            PROJECT_ROOT / "preflight_issues_config.json",
            PROJECT_ROOT / "unmatched_skus_config.json",
        ]
        data: dict | None = None
        for path in path_candidates:
            if not path.is_file():
                continue
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
                    break
            except Exception:
                continue
        if data is None:
            return
        # ponytail: never restore date — always open as today (field stays editable)
        mapping = {
            "workbook_path": self.workbook_var,
            "cl_csv_path": self.cl_csv_var,
            "output_dir": self.output_dir_var,
            "apparel_dir": self.apparel_dir_var,
            "logo_normal_dir": self.logo_normal_dir_var,
            "logo_custom_single_dir": self.logo_custom_single_dir_var,
            "logo_custom_double_dir": self.logo_custom_double_dir_var,
            "shift": self.shift_var,
            "process_number": self.process_number_var,
        }
        for key, var in mapping.items():
            val = str(data.get(key, "")).strip()
            if val:
                var.set(val)
        mode = str(data.get("input_mode", "")).strip().lower()
        self.input_mode_var.set("tag" if mode == "tag" else "file")
        self.selected_tags = parse_shipstation_tags_config(data)
        self.input_paths = self._parse_saved_input_files(data)
        if isinstance(data.get("use_demo_images"), bool):
            self.use_demo_images_var.set(data["use_demo_images"])

    @staticmethod
    def _parse_saved_input_files(data: dict) -> list[Path]:
        raw = data.get("input_files")
        paths: list[Path] = []
        if isinstance(raw, list):
            for item in raw:
                text = str(item or "").strip()
                if not text:
                    continue
                path = Path(text)
                if path.is_file() and path not in paths:
                    paths.append(path)
        elif isinstance(raw, str) and raw.strip():
            # Legacy / accidental single-string form
            path = Path(raw.strip())
            if path.is_file():
                paths.append(path)
        return paths

    def _refresh_input_listbox(self) -> None:
        if not hasattr(self, "listbox"):
            return
        self.listbox.delete(0, END)
        for path in self.input_paths:
            self.listbox.insert(END, str(path))

    def _save_config(self) -> None:
        tags_payload, legacy_name, legacy_id = shipstation_tags_config_payload(self.selected_tags)
        data = {
            "workbook_path": (self.workbook_var.get() or "").strip(),
            "cl_csv_path": (self.cl_csv_var.get() or "").strip(),
            "output_dir": (self.output_dir_var.get() or "").strip(),
            "apparel_dir": (self.apparel_dir_var.get() or "").strip(),
            "logo_normal_dir": (self.logo_normal_dir_var.get() or "").strip(),
            "logo_custom_single_dir": (self.logo_custom_single_dir_var.get() or "").strip(),
            "logo_custom_double_dir": (self.logo_custom_double_dir_var.get() or "").strip(),
            "use_demo_images": self.use_demo_images_var.get(),
            "date": (self.date_var.get() or "").strip(),
            "shift": (self.shift_var.get() or "").strip(),
            "process_number": (self.process_number_var.get() or "").strip(),
            "input_mode": "tag" if (self.input_mode_var.get() or "").strip() == "tag" else "file",
            "input_files": [str(p) for p in self.input_paths],
            "shipstation_tags": tags_payload,
            "shipstation_tag_name": legacy_name,
            "shipstation_tag_id": legacy_id,
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            PREFLIGHT_CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(
                f"[preflight issues] config save failed ({PREFLIGHT_CONFIG}): {exc}",
                file=sys.stderr,
                flush=True,
            )

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

    def is_tag_mode(self) -> bool:
        return (self.input_mode_var.get() or "").strip() == "tag"

    def selected_shipstation_tags(self) -> list[tuple[int, str]]:
        return list(self.selected_tags)

    def selected_shipstation_tag(self) -> tuple[int, str] | None:
        tags = self.selected_shipstation_tags()
        return tags[0] if len(tags) == 1 else None

    def _refresh_tag_chips(self) -> None:
        if not hasattr(self, "tag_chips_frame"):
            return
        enabled = self.is_tag_mode() and not getattr(self, "_tags_loading", False)
        refresh_tag_chip_grid(
            self.tag_chips_frame,
            self.selected_tags,
            self._remove_tag_by_id if enabled else None,
            enabled=enabled,
        )

    def _update_process_entry_for_tags(self) -> None:
        if not hasattr(self, "process_entry"):
            return
        # File mode: unused (CSV stem is Process Number). Tag mode: enabled for
        # one tag, disabled when multiple tags (each uses Tags.xlsx).
        if not self.is_tag_mode():
            self.process_entry.config(state=DISABLED)
            if hasattr(self, "process_label"):
                self.process_label.configure(style="Muted.TLabel")
            return
        if hasattr(self, "process_label"):
            self.process_label.configure(style="TLabel")
        multi = len(self.selected_tags) > 1
        self.process_entry.config(state=DISABLED if multi else NORMAL)
        if not multi:
            self._soft_fill_process_from_tags_sheet()

    def _enter_tag_mode_clearing_files(self) -> None:
        self.input_mode_var.set("tag")
        self._syncing_inputs = True
        try:
            self.input_paths.clear()
            if hasattr(self, "listbox"):
                self.listbox.delete(0, END)
        finally:
            self._syncing_inputs = False

    def _add_selected_tag(self) -> None:
        if not self.is_tag_mode():
            return
        name = (self.shipstation_tag_var.get() or "").strip()
        if not name:
            return
        tag_id: int | None = None
        for t in self._shipstation_tags:
            if str(t.get("name") or "") == name:
                try:
                    tag_id = int(t.get("tagId"))
                except (TypeError, ValueError):
                    tag_id = None
                break
        if tag_id is None:
            messagebox.showwarning("ShipStation tags", f"Could not resolve tag id for '{name}'.")
            return
        if any(existing_id == tag_id for existing_id, _ in self.selected_tags):
            return
        self.selected_tags.append((tag_id, name))
        self._enter_tag_mode_clearing_files()
        self._refresh_tag_chips()
        self._update_process_entry_for_tags()
        self._sync_input_mode()

    def _remove_tag_by_id(self, tag_id: int) -> None:
        if not self.is_tag_mode():
            return
        self.selected_tags = [(tid, name) for tid, name in self.selected_tags if tid != tag_id]
        self._refresh_tag_chips()
        self._update_process_entry_for_tags()
        self._sync_input_mode()

    def _remove_all_tags(self) -> None:
        if not self.is_tag_mode():
            return
        self.selected_tags.clear()
        self._refresh_tag_chips()
        self._update_process_entry_for_tags()
        self._sync_input_mode()

    def _on_input_mode_changed(self, *args: object) -> None:
        self._sync_input_mode()
        if self.is_tag_mode() and not self._shipstation_tags and not self._tags_loading:
            self._refresh_shipstation_tags()

    def _on_shift_changed(self, *args: object) -> None:
        self._soft_fill_process_from_tags_sheet()

    def _soft_fill_process_from_tags_sheet(self) -> None:
        """If process is empty with exactly one tag, prefill from ShipStation Tags.xlsx."""
        if not self.is_tag_mode():
            return
        if len(self.selected_tags) != 1:
            return
        if (self.process_number_var.get() or "").strip():
            return
        tag_id, tag_name = self.selected_tags[0]
        shift = (self.shift_var.get() or "").strip()
        if not shift:
            return
        try:
            found = lookup_process_number(
                tag_id=tag_id, tag_name=tag_name, shift_label=shift
            )
        except Exception:
            return
        if found:
            self.process_number_var.set(found)

    def _set_tag_controls_enabled(self, enabled: bool, *, loading: bool = False) -> None:
        state_cb = "readonly" if enabled else DISABLED
        btn_state = DISABLED if (not enabled or loading) else NORMAL
        if hasattr(self, "tag_cb"):
            self.tag_cb.config(state=state_cb)
        for attr in ("add_tag_btn", "refresh_tags_btn", "remove_all_tags_btn"):
            if hasattr(self, attr):
                getattr(self, attr).config(state=btn_state)
        if hasattr(self, "tag_chips_frame"):
            set_tag_chip_grid_enabled(self.tag_chips_frame, bool(enabled) and not loading)

    def _sync_input_mode(self) -> None:
        tag_mode = self.is_tag_mode()
        loading = bool(getattr(self, "_tags_loading", False))
        if tag_mode:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="TLabel")
            if hasattr(self, "input_files_label"):
                self.input_files_label.configure(style="Muted.TLabel")
            self._set_tag_controls_enabled(True, loading=loading)
            self.add_files_btn.config(state=DISABLED)
            self.remove_selected_btn.config(state=DISABLED)
            self.remove_all_btn.config(state=DISABLED)
            set_listbox_enabled(self.listbox, False)
            self.date_entry.config(state=NORMAL)
            self.shift_cb.config(state="readonly")
            self._update_process_entry_for_tags()
        else:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="Muted.TLabel")
            if hasattr(self, "input_files_label"):
                self.input_files_label.configure(style="TLabel")
            self._set_tag_controls_enabled(False)
            self.add_files_btn.config(state=NORMAL)
            self.remove_selected_btn.config(state=NORMAL)
            self.remove_all_btn.config(state=NORMAL)
            set_listbox_enabled(self.listbox, True)
            self.date_entry.config(state=NORMAL)
            self.shift_cb.config(state="readonly")
            self._update_process_entry_for_tags()

    def _refresh_shipstation_tags(self) -> None:
        if not self.is_tag_mode():
            return
        if getattr(self, "_tags_loading", False):
            return
        self._tags_loading = True
        self._sync_input_mode()

        def worker() -> None:
            try:
                client = ShipStationClient(load_shipstation_credentials())
                tags = client.list_tags()
                self.root.after(0, self._on_tags_loaded, tags, None)
            except Exception as exc:
                self.root.after(0, self._on_tags_loaded, [], str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_tags_loaded(self, tags: list, error: str | None) -> None:
        self._tags_loading = False
        self._shipstation_tags = tags or []
        names = [str(t.get("name") or "") for t in self._shipstation_tags]
        self.tag_cb["values"] = names

        by_id: dict[int, str] = {}
        for t in self._shipstation_tags:
            try:
                by_id[int(t.get("tagId"))] = str(t.get("name") or "")
            except (TypeError, ValueError):
                continue
        refreshed: list[tuple[int, str]] = []
        for tag_id, name in self.selected_tags:
            if tag_id in by_id:
                refreshed.append((tag_id, by_id[tag_id] or name))
            else:
                refreshed.append((tag_id, name))
        self.selected_tags = refreshed
        self._refresh_tag_chips()

        current_pick = (self.shipstation_tag_var.get() or "").strip()
        if current_pick and current_pick not in names:
            self.shipstation_tag_var.set("")
        elif not current_pick and names:
            self.shipstation_tag_var.set(names[0])

        self._sync_input_mode()
        if error:
            messagebox.showwarning("ShipStation tags", f"Could not load tags:\n{error}")

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

        ttk.Label(frm, text="Input source:").grid(row=2, column=0, sticky="w", padx=(0, 10), pady=3)
        mode_frame = ttk.Frame(frm)
        mode_frame.grid(row=2, column=1, columnspan=2, sticky="w", pady=3)
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
        self.tag_label.grid(row=3, column=0, sticky="nw", padx=(0, 10), pady=3)
        tag_outer = ttk.Frame(frm)
        tag_outer.grid(row=3, column=1, columnspan=2, sticky="we", pady=3)

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
            row=4, column=0, sticky="w", padx=(0, 10), pady=3
        )
        self.date_entry = ttk.Entry(frm, textvariable=self.date_var, width=20)
        self.date_entry.grid(row=4, column=1, sticky="w", pady=3)

        ttk.Label(frm, text="Shift:").grid(row=5, column=0, sticky="w", padx=(0, 10), pady=3)
        self.shift_cb = ttk.Combobox(
            frm,
            textvariable=self.shift_var,
            values=["1st", "2nd", "3rd", "4th", "5th"],
            state="readonly",
            width=10,
        )
        self.shift_cb.grid(row=5, column=1, sticky="w", pady=3)

        self.process_label = ttk.Label(frm, text="Process number:")
        self.process_label.grid(row=6, column=0, sticky="w", padx=(0, 10), pady=3)
        self.process_entry = ttk.Entry(frm, textvariable=self.process_number_var, width=20)
        self.process_entry.grid(row=6, column=1, sticky="w", pady=3)

        self.input_files_label = ttk.Label(frm, text="Input CSV(s):")
        self.input_files_label.grid(row=7, column=0, sticky="w", padx=(0, 10), pady=3)
        list_frame = ttk.Frame(frm)
        list_frame.grid(row=7, column=1, sticky="nsew", pady=3)
        self.listbox = style_listbox(
            Listbox(list_frame, height=6, width=70, selectmode=MULTIPLE, exportselection=False)
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scroll.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scroll.set)
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=8, column=1, sticky="w", pady=(0, 6))
        self.add_files_btn = ttk.Button(btn_frame, text="Add files…", command=self._add_files)
        self.add_files_btn.pack(side="left", padx=(0, 6))
        self.remove_selected_btn = ttk.Button(
            btn_frame, text="Remove selected", command=self._remove_selected
        )
        self.remove_selected_btn.pack(side="left", padx=(0, 6))
        self.remove_all_btn = ttk.Button(btn_frame, text="Remove all", command=self._remove_all)
        self.remove_all_btn.pack(side="left")

        self._add_dir_row(frm, 9, "Workbook:", self.workbook_var, self._browse_workbook)
        self._add_dir_row(
            frm,
            10,
            "Custom Label Database (CSV):",
            self.cl_csv_var,
            self._browse_cl_csv,
        )
        self._add_dir_row(frm, 11, "Output directory:", self.output_dir_var, self._browse_output_dir)
        ttk.Label(frm, text="Use demo images:").grid(row=12, column=0, sticky="w", padx=(0, 10), pady=3)
        ttk.Checkbutton(
            frm,
            text="Offline testing — placeholders from Demo Images Database/",
            variable=self.use_demo_images_var,
        ).grid(row=12, column=1, columnspan=2, sticky="w", pady=3)
        self._add_dir_row(
            frm, 13, "Apparel Image folder:", self.apparel_dir_var, self._browse_apparel_dir
        )
        self._add_dir_row(
            frm,
            14,
            "Normal Logo/Design folder:",
            self.logo_normal_dir_var,
            self._browse_logo_normal_dir,
        )
        self._add_dir_row(
            frm,
            15,
            "Customise Single Position Logo/Design folder:",
            self.logo_custom_single_dir_var,
            self._browse_logo_custom_single_dir,
        )
        self._add_dir_row(
            frm,
            16,
            "Customise Double Position Logo/Design folder:",
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

    def _add_files(self) -> None:
        if self.is_tag_mode():
            return

        # Selecting CSVs must block tag input.
        self.input_mode_var.set("file")
        self.selected_tags.clear()
        self._refresh_tag_chips()
        self.shipstation_tag_var.set("")

        paths = filedialog.askopenfilenames(
            title="Select ShipStation CSV(s)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not paths:
            return
        for p in paths:
            path = Path(p)
            if path not in self.input_paths:
                self.input_paths.append(path)
                self.listbox.insert(END, str(path))

    def _remove_selected(self) -> None:
        if self.is_tag_mode():
            return
        sel = set(self.listbox.curselection())
        self.input_paths = [p for i, p in enumerate(self.input_paths) if i not in sel]
        self.listbox.delete(0, END)
        for p in self.input_paths:
            self.listbox.insert(END, str(p))

    def _remove_all(self) -> None:
        if self.is_tag_mode():
            return
        self.input_paths.clear()
        self.listbox.delete(0, END)

    def _browse_workbook(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Workbook",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )
        if path:
            self.workbook_var.set(path)

    def _browse_cl_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Custom Label Database CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.cl_csv_var.set(path)

    def _browse_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Select output directory")
        if path:
            self.output_dir_var.set(path)

    def _browse_apparel_dir(self) -> None:
        path = filedialog.askdirectory(title="Select Apparel Image folder")
        if path:
            self.apparel_dir_var.set(path)

    def _browse_logo_normal_dir(self) -> None:
        path = filedialog.askdirectory(title="Select Normal Logo/Design folder")
        if path:
            self.logo_normal_dir_var.set(path)

    def _browse_logo_custom_single_dir(self) -> None:
        path = filedialog.askdirectory(title="Select Customise Single Position Logo/Design folder")
        if path:
            self.logo_custom_single_dir_var.set(path)

    def _browse_logo_custom_double_dir(self) -> None:
        path = filedialog.askdirectory(title="Select Customise Double Position Logo/Design folder")
        if path:
            self.logo_custom_double_dir_var.set(path)

    def _validate_image_folders(self) -> bool:
        folders = (
            ("Apparel Image folder", self.apparel_dir_var.get()),
            ("Normal Logo/Design folder", self.logo_normal_dir_var.get()),
            ("Customise Single Position Logo/Design folder", self.logo_custom_single_dir_var.get()),
            ("Customise Double Position Logo/Design folder", self.logo_custom_double_dir_var.get()),
        )
        for label, raw in folders:
            path_str = (raw or "").strip()
            if not path_str:
                continue
            if not Path(path_str).is_dir():
                messagebox.showerror("Error", f"{label} is not a valid directory:\n{path_str}")
                return False
        return True

    def _optional_dir(self, var: StringVar) -> Path | None:
        raw = (var.get() or "").strip()
        return Path(raw) if raw else None

    def _append_log_ui(self, msg: str) -> None:
        self.log.insert(END, msg + "\n")
        self.log.see(END)

    def _enqueue_log(self, msg: str) -> None:
        if self._log_queue is not None:
            self._log_queue.put(msg)

    def _drain_log_queue(self) -> bool:
        if self._log_queue is None:
            return False
        while True:
            try:
                msg = self._log_queue.get_nowait()
            except queue.Empty:
                return False
            if msg is None:
                return True
            self._append_log_ui(msg)

    def _poll_log_queue(self) -> None:
        if self._drain_log_queue():
            return
        self.root.after(80, self._poll_log_queue)

    def _on_run(self) -> None:
        tag_mode = self.is_tag_mode()
        tags = self.selected_shipstation_tags() if tag_mode else []
        if tag_mode:
            if not tags:
                messagebox.showwarning("No tag", "Please select at least one ShipStation tag.")
                return
        elif not self.input_paths:
            messagebox.showwarning(
                "No input",
                "Add at least one input CSV file (or switch Input source to ShipStation tag(s)).",
            )
            return
        workbook_path = Path(self.workbook_var.get())
        if not workbook_path.is_file():
            messagebox.showerror("Workbook missing", f"Workbook not found:\n{workbook_path}")
            return
        cl_csv_path = Path((self.cl_csv_var.get() or "").strip() or str(DEFAULT_CL_CSV))
        if not cl_csv_path.is_file():
            messagebox.showerror(
                "Custom Label Database missing",
                f"Custom Label Database CSV not found:\n{cl_csv_path}",
            )
            return
        if not self._validate_image_folders():
            return

        output_dir = Path(self.output_dir_var.get())
        input_paths = list(self.input_paths)
        resolved_tags: list[tuple[int, str, str]] = []
        multi_tags = False
        gui_at_resolve = ""

        date_str = (self.date_var.get() or "").strip()
        shift_str = (self.shift_var.get() or "").strip()
        try:
            datetime.strptime(date_str, "%d-%m-%Y")
        except Exception:
            messagebox.showerror("Error", "Date must be in DD-MM-YYYY format.")
            return
        if not shift_str:
            messagebox.showerror("Error", "Please select a shift.")
            return
        # Nest issues output under {date}/{shift} Shift/ (file and tag modes)
        output_dir = output_dir / date_str / _shift_subdir_name(shift_str)

        if tag_mode:
            multi_tags = len(tags) > 1
            gui_at_resolve = "" if multi_tags else (self.process_number_var.get() or "").strip()
            resolved_tags, err = resolve_tag_list_processes(
                tags,
                shift_label=shift_str,
                gui_value=gui_at_resolve,
            )
            if err or not resolved_tags:
                messagebox.showerror("Error", err or "Could not resolve process numbers.")
                return
            for _tag_id, _tag_name, process_name in resolved_tags:
                if _FILENAME_UNSAFE.search(process_name):
                    messagebox.showerror(
                        "Error", 'Process number cannot contain / \\ : * ? " < > |'
                    )
                    return
            if len(resolved_tags) == 1 and not gui_at_resolve:
                self.process_number_var.set(resolved_tags[0][2])

        self.log.delete("1.0", END)
        self.run_btn.config(state=DISABLED)
        self._log_queue = queue.Queue()
        self.root.after(80, self._poll_log_queue)

        apparel_dir = self._optional_dir(self.apparel_dir_var)
        logo_normal_dir = self._optional_dir(self.logo_normal_dir_var)
        logo_custom_single_dir = self._optional_dir(self.logo_custom_single_dir_var)
        logo_custom_double_dir = self._optional_dir(self.logo_custom_double_dir_var)

        def worker() -> None:
            try:
                paths = input_paths
                if resolved_tags:
                    paths = []
                    for tag_id, tag_name, process_name in resolved_tags:
                        prefix = f"[{process_name}] " if multi_tags else ""
                        self._enqueue_log(
                            f"{prefix}Fetching ShipStation orders for tag '{tag_name}' "
                            f"(awaiting_shipment)…"
                        )
                        if multi_tags or not gui_at_resolve:
                            self._enqueue_log(
                                f"{prefix}Using process {process_name} from "
                                f"{DEFAULT_XLSX_PATH.name} for tag '{tag_name}' / "
                                f"shift '{shift_str}'."
                            )
                        csv_path = fetch_tag_orders_to_csv(
                            tag_id=int(tag_id),
                            tag_name=str(tag_name or ""),
                            date_dd_mm_yyyy=str(date_str),
                            shift_label=str(shift_str),
                            process_number=str(process_name),
                            input_root=PROJECT_ROOT / "Input",
                            log=self._enqueue_log,
                        )
                        paths.append(csv_path)
                out = run_preflight_audit(
                    paths,
                    workbook_path,
                    output_dir,
                    log_callback=self._enqueue_log,
                    cl_csv_path=cl_csv_path,
                    apparel_dir=apparel_dir,
                    logo_normal_dir=logo_normal_dir,
                    logo_custom_single_dir=logo_custom_single_dir,
                    logo_custom_double_dir=logo_custom_double_dir,
                    use_demo_images=self.use_demo_images_var.get(),
                )
                self._run_result = out
                if self._log_queue is not None:
                    self._log_queue.put(None)
                self.root.after(0, self._on_run_success)
            except Exception as exc:
                if self._log_queue is not None:
                    self._log_queue.put(None)
                self.root.after(0, self._on_run_error, str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_run_success(self) -> None:
        self._drain_log_queue()
        out = self._run_result
        self.run_btn.config(state=NORMAL)
        self._save_config()
        if out is NO_ISSUES:
            messagebox.showinfo("Done", "No preflight issues found.")
        elif isinstance(out, PreflightResult):
            messagebox.showinfo(
                "Done",
                f"Preflight issues written to:\n{out.path}\n\n"
                f"Unmatched SKU: {out.unmatched_count}\n"
                f"Missing Logo: {out.missing_logo_count}\n"
                f"Missing Apparel: {out.missing_apparel_count}\n"
                f"Issue rows written: {out.issue_row_count}",
            )
        elif out is None:
            messagebox.showerror("Error", "Preflight failed. See the log for details.")

    def _on_run_error(self, message: str) -> None:
        self._drain_log_queue()
        self._append_log_ui(f"Error: {message}")
        self.run_btn.config(state=NORMAL)
        messagebox.showerror("Error", message)

    def _on_closing(self) -> None:
        self._save_config()
        self.root.destroy()


# Back-compat alias
UnmatchedSkusApp = PreflightIssuesApp
