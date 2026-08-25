from __future__ import annotations

import json
import queue
import sys
import threading
from datetime import date
from pathlib import Path
from tkinter import DISABLED, END, NORMAL, StringVar, BooleanVar, Tk, filedialog, messagebox

from scripts.gui_theme import apply_theme, refresh_tag_chip_grid, set_listbox_enabled, set_tag_chip_grid_enabled
from scripts.pipeline_shipstation.client import ShipStationClient
from scripts.pipeline_shipstation.credentials import load_shipstation_credentials
from scripts.pipeline_shipstation.tags_process_lookup import (
    lookup_process_number,
    parse_shipstation_tags_config,
    shipstation_tags_config_payload,
)

from .config import CONFIG_DIR, CONFIG_KEYS, CONFIG_PATH, DEFAULT_OUTPUT_DIR, DEFAULT_WORKBOOK, PROJECT_ROOT
from .runner import (
    drain_log_queue,
    get_input_paths,
    on_pipeline_error,
    on_pipeline_success,
    on_run_clicked,
    poll_log_queue,
)
from .ui import build_ui, on_fixed_process_toggle, on_separate_by_logo_toggle


class PackingListApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Packing List App")
        self.input_csv_var = StringVar()
        self.date_var = StringVar(value=date.today().strftime("%d-%m-%Y"))
        self.shift_var = StringVar()
        self.output_dir_var = StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.workbook_var = StringVar(value=str(DEFAULT_WORKBOOK))
        self.apparel_dir_var = StringVar()
        self.logo_normal_dir_var = StringVar()
        self.logo_custom_single_dir_var = StringVar()
        self.logo_custom_double_dir_var = StringVar()
        self.pdf_copy_dir_var = StringVar()
        self.excel_copy_dir_var = StringVar()
        self.separate_by_logo_id_var = BooleanVar(value=False)
        self.logo_id_threshold_var = StringVar(value="5")
        self.use_fixed_process_number_var = BooleanVar(value=False)
        self.fixed_process_number_var = StringVar()
        self.run_missing_logo_pipeline_var = BooleanVar(value=False)
        self.input_mode_var = StringVar(value="file")  # "file" | "tag"
        self.shipstation_tag_var = StringVar()  # Combobox pick (not the selection list)
        self.selected_tags: list[tuple[int, str]] = []
        self.input_paths: list[Path] = []
        self._shipstation_tags: list[dict] = []
        self._tags_loading = False
        self._syncing_input_var = False

        self._load_config()
        # Migrate saved semicolon-joined input_csv into the live path list.
        self._sync_input_paths_from_var()
        self.unmatched_path: Path | None = None
        self.missing_logo_path: Path | None = None
        self.output_root: Path | None = None
        self._log_queue: queue.Queue[str | None] | None = None
        self._pipeline_results: list[dict[str, object]] | None = None

        build_ui(self)
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def is_tag_mode(self) -> bool:
        """True when ShipStation tag is the selected input source (not missing pipeline)."""
        if self.run_missing_logo_pipeline_var.get():
            return False
        return (self.input_mode_var.get() or "").strip() == "tag"

    def _on_fixed_process_toggle(self, *args: object) -> None:
        on_fixed_process_toggle(self, *args)

    def _on_separate_by_logo_toggle(self, *args: object) -> None:
        on_separate_by_logo_toggle(self, *args)

    def _on_missing_pipeline_toggle(self, *args: object) -> None:
        if self.run_missing_logo_pipeline_var.get():
            self.input_mode_var.set("file")
        self._sync_input_mode()

    def _on_input_mode_changed(self, *args: object) -> None:
        self._sync_input_mode()
        if self.is_tag_mode() and not self._shipstation_tags and not self._tags_loading:
            self._refresh_shipstation_tags()

    def selected_shipstation_tags(self) -> list[tuple[int, str]]:
        """Return selected (tagId, name) pairs."""
        return list(self.selected_tags)

    def selected_shipstation_tag(self) -> tuple[int, str] | None:
        """Return the sole selected tag, or None if zero/multiple."""
        tags = self.selected_shipstation_tags()
        return tags[0] if len(tags) == 1 else None

    def _sync_input_paths_from_var(self) -> None:
        raw = (self.input_csv_var.get() or "").strip()
        self.input_paths = [Path(p.strip()) for p in raw.split(";") if p.strip()] if raw else []

    def _sync_input_var_from_paths(self) -> None:
        self._syncing_input_var = True
        try:
            self.input_csv_var.set(";".join(str(p) for p in self.input_paths))
        finally:
            self._syncing_input_var = False

    def _refresh_input_listbox(self) -> None:
        if not hasattr(self, "input_listbox"):
            return
        self.input_listbox.delete(0, END)
        for path in self.input_paths:
            self.input_listbox.insert(END, str(path))

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
        """Disable fixed process when multiple tags are selected."""
        if not self.is_tag_mode():
            return
        multi = len(self.selected_tags) > 1
        if hasattr(self, "fixed_process_entry"):
            self.fixed_process_entry.config(state=DISABLED if multi else NORMAL)
        if multi:
            # Soft-fill does not apply; leave any leftover value unused.
            return
        self._soft_fill_process_from_tags_sheet()

    def _enter_tag_mode_clearing_csv(self) -> None:
        if self.run_missing_logo_pipeline_var.get():
            return
        self.input_mode_var.set("tag")
        self.input_paths.clear()
        self._sync_input_var_from_paths()
        self._refresh_input_listbox()

    def _enter_file_mode_clearing_tags(self) -> None:
        if self.run_missing_logo_pipeline_var.get():
            self.input_mode_var.set("file")
            return
        self.input_mode_var.set("file")
        self.selected_tags.clear()
        self._refresh_tag_chips()
        self.shipstation_tag_var.set("")

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
        self._enter_tag_mode_clearing_csv()
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

    def _add_files(self) -> None:
        if self.is_tag_mode():
            return
        paths = filedialog.askopenfilenames(
            title="Select ShipStation CSV(s)",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not paths:
            return
        self._enter_file_mode_clearing_tags()
        for p in paths:
            path = Path(p)
            if path not in self.input_paths:
                self.input_paths.append(path)
        if len(self.input_paths) > 1:
            self.use_fixed_process_number_var.set(True)
            if (self.fixed_process_number_var.get() or "").strip():
                self.fixed_process_number_var.set("")
        self._sync_input_var_from_paths()
        self._refresh_input_listbox()
        self._sync_input_mode()

    def _remove_selected_files(self) -> None:
        if self.is_tag_mode() or not hasattr(self, "input_listbox"):
            return
        sel = set(self.input_listbox.curselection())
        if not sel:
            return
        self.input_paths = [p for i, p in enumerate(self.input_paths) if i not in sel]
        self._sync_input_var_from_paths()
        self._refresh_input_listbox()

    def _remove_all_files(self) -> None:
        if self.is_tag_mode():
            return
        self.input_paths.clear()
        self._sync_input_var_from_paths()
        self._refresh_input_listbox()

    def _on_shift_changed(self, *args: object) -> None:
        self._soft_fill_process_from_tags_sheet()

    def _soft_fill_process_from_tags_sheet(self) -> None:
        """If process is empty with exactly one tag, prefill from ShipStation Tags.xlsx."""
        if not self.is_tag_mode():
            return
        if len(self.selected_tags) != 1:
            return
        if (self.fixed_process_number_var.get() or "").strip():
            return
        tag_id, tag_name = self.selected_tags[0]
        shift = (self.shift_var.get() or "").strip()
        if not shift:
            return
        try:
            found = lookup_process_number(
                tag_id=tag_id,
                tag_name=tag_name,
                shift_label=shift,
            )
        except Exception:
            return
        if found:
            self.fixed_process_number_var.set(found)

    def _set_tag_controls_enabled(self, enabled: bool, *, loading: bool = False) -> None:
        state_cb = "readonly" if enabled else DISABLED
        btn_state = DISABLED if (not enabled or loading) else NORMAL
        if hasattr(self, "tag_cb"):
            self.tag_cb.config(state=state_cb)
        if hasattr(self, "add_tag_btn"):
            self.add_tag_btn.config(state=btn_state)
        if hasattr(self, "refresh_tags_btn"):
            self.refresh_tags_btn.config(state=btn_state)
        if hasattr(self, "remove_all_tags_btn"):
            self.remove_all_tags_btn.config(state=btn_state)
        if hasattr(self, "tag_chips_frame"):
            set_tag_chip_grid_enabled(self.tag_chips_frame, bool(enabled) and not loading)

    def _set_file_controls_enabled(self, enabled: bool) -> None:
        btn_state = NORMAL if enabled else DISABLED
        for attr in ("add_files_btn", "remove_selected_btn", "remove_all_btn"):
            if hasattr(self, attr):
                getattr(self, attr).config(state=btn_state)
        if hasattr(self, "input_listbox"):
            set_listbox_enabled(self.input_listbox, bool(enabled))

    def _sync_input_mode(self) -> None:
        """Enable/disable tag vs CSV controls from the Input source radios."""
        missing = self.run_missing_logo_pipeline_var.get()
        tag_mode = self.is_tag_mode()
        loading = bool(getattr(self, "_tags_loading", False))

        if hasattr(self, "input_mode_file_rb"):
            self.input_mode_file_rb.config(state=NORMAL)
        if hasattr(self, "input_mode_tag_rb"):
            # Missing pipeline is file-only.
            self.input_mode_tag_rb.config(state=DISABLED if missing else NORMAL)

        if tag_mode:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="TLabel")
            if hasattr(self, "input_label"):
                self.input_label.configure(style="Muted.TLabel")
            self._set_tag_controls_enabled(True, loading=loading)
            self._set_file_controls_enabled(False)
            self.use_fixed_process_number_var.set(True)
            if hasattr(self, "use_fixed_process_cb"):
                self.use_fixed_process_cb.config(state=DISABLED)
            self._update_process_entry_for_tags()
        else:
            if hasattr(self, "tag_label"):
                self.tag_label.configure(style="Muted.TLabel")
            if hasattr(self, "input_label"):
                self.input_label.configure(style="TLabel")
            self._set_tag_controls_enabled(False)
            self._set_file_controls_enabled(True)
            if hasattr(self, "use_fixed_process_cb"):
                self.use_fixed_process_cb.config(state=NORMAL)
            # Refresh fixed-process entry state for file mode.
            on_fixed_process_toggle(self)

    def _refresh_shipstation_tags(self) -> None:
        """Load tags from ShipStation on a background thread."""
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
        if hasattr(self, "tag_cb"):
            self.tag_cb["values"] = names

        # Refresh selected list names from API when ids still exist.
        refreshed: list[tuple[int, str]] = []
        by_id = {}
        for t in self._shipstation_tags:
            try:
                by_id[int(t.get("tagId"))] = str(t.get("name") or "")
            except (TypeError, ValueError):
                continue
        for tag_id, name in self.selected_tags:
            if tag_id in by_id:
                refreshed.append((tag_id, by_id[tag_id] or name))
            else:
                # Keep saved selection even if temporarily missing from API.
                refreshed.append((tag_id, name))
        self.selected_tags = refreshed
        self._refresh_tag_chips()

        # Keep combobox on a sensible pick value.
        current_pick = (self.shipstation_tag_var.get() or "").strip()
        if current_pick and current_pick not in names:
            self.shipstation_tag_var.set("")
        elif not current_pick and names:
            self.shipstation_tag_var.set(names[0])

        self._sync_input_mode()
        if error:
            messagebox.showwarning("ShipStation tags", f"Could not load tags:\n{error}")

    def _load_config(self) -> None:
        data = None
        for path in (CONFIG_PATH, PROJECT_ROOT / "gui_config.json"):
            if not path.exists():
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
        var_map = {
            "input_csv": self.input_csv_var, "date": self.date_var, "shift": self.shift_var, "output_dir": self.output_dir_var,
            "workbook_path": self.workbook_var, "apparel_dir": self.apparel_dir_var, "logo_normal_dir": self.logo_normal_dir_var,
            "logo_custom_single_dir": self.logo_custom_single_dir_var, "logo_custom_double_dir": self.logo_custom_double_dir_var,
            "pdf_copy_dir": self.pdf_copy_dir_var, "excel_copy_dir": self.excel_copy_dir_var,
        }
        for key in CONFIG_KEYS:
            if key not in data:
                continue
            if key == "separate_by_logo_id" and isinstance(data[key], bool):
                self.separate_by_logo_id_var.set(data[key])
            elif key == "logo_id_threshold":
                self.logo_id_threshold_var.set(str(int(data[key])) if str(data[key]).strip().isdigit() else "5")
            elif key == "use_fixed_process_number" and isinstance(data[key], bool):
                self.use_fixed_process_number_var.set(data[key])
            elif key == "fixed_process_number" and isinstance(data[key], str):
                self.fixed_process_number_var.set(data[key])
            elif key == "run_missing_logo_pipeline" and isinstance(data[key], bool):
                self.run_missing_logo_pipeline_var.set(data[key])
            elif key == "input_mode" and isinstance(data[key], str):
                mode = data[key].strip().lower()
                self.input_mode_var.set("tag" if mode == "tag" else "file")
            elif key in ("shipstation_tag_name", "shipstation_tag_id", "shipstation_tags"):
                continue
            elif isinstance(data[key], str) and key in var_map:
                var_map[key].set(data[key])
        self.selected_tags = parse_shipstation_tags_config(data)

    def _save_config(self) -> None:
        self._sync_input_var_from_paths()
        tags_payload, legacy_name, legacy_id = shipstation_tags_config_payload(self.selected_tags)
        data = {
            "input_csv": self.input_csv_var.get() or "",
            "date": self.date_var.get() or "",
            "shift": self.shift_var.get() or "",
            "output_dir": self.output_dir_var.get() or "",
            "workbook_path": self.workbook_var.get() or "",
            "apparel_dir": self.apparel_dir_var.get() or "",
            "logo_normal_dir": self.logo_normal_dir_var.get() or "",
            "logo_custom_single_dir": (self.logo_custom_single_dir_var.get() or "").strip(),
            "logo_custom_double_dir": (self.logo_custom_double_dir_var.get() or "").strip(),
            "pdf_copy_dir": (self.pdf_copy_dir_var.get() or "").strip(),
            "excel_copy_dir": (self.excel_copy_dir_var.get() or "").strip(),
            "separate_by_logo_id": self.separate_by_logo_id_var.get(),
            "logo_id_threshold": int(self.logo_id_threshold_var.get()) if str(self.logo_id_threshold_var.get()).strip().isdigit() else 5,
            "use_fixed_process_number": self.use_fixed_process_number_var.get(),
            "fixed_process_number": (self.fixed_process_number_var.get() or "").strip(),
            "run_missing_logo_pipeline": self.run_missing_logo_pipeline_var.get(),
            "input_mode": "tag" if (self.input_mode_var.get() or "").strip() == "tag" else "file",
            "shipstation_tags": tags_payload,
            "shipstation_tag_name": legacy_name,
            "shipstation_tag_id": legacy_id,
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[packing list] config save failed ({CONFIG_PATH}): {exc}", file=sys.stderr, flush=True)

    def _on_closing(self) -> None:
        self._save_config()
        self.root.destroy()

    def _browse_directory(self, var: StringVar) -> None:
        dirname = filedialog.askdirectory()
        if dirname:
            var.set(dirname)

    def _browse_file(self, var: StringVar) -> None:
        filename = filedialog.askopenfilename()
        if filename:
            var.set(filename)

    def _get_input_paths(self) -> list[Path]:
        return get_input_paths(self)

    def _drain_log_queue(self) -> bool:
        return drain_log_queue(self)

    def _poll_log_queue(self) -> None:
        poll_log_queue(self)

    def _on_run_clicked(self) -> None:
        on_run_clicked(self)

    def _on_pipeline_success(self) -> None:
        on_pipeline_success(self)

    def _on_pipeline_error(self, message: str) -> None:
        on_pipeline_error(self, message)


def main() -> None:
    root = Tk()
    apply_theme(root)
    PackingListApp(root)
    root.deiconify()
    root.state("zoomed")
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    root.focus_force()
    root.mainloop()
