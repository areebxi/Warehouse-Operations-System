from __future__ import annotations

from pathlib import Path
from tkinter import END, StringVar, filedialog


class PackingListFilesMixin:
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

    def _enter_file_mode_clearing_tags(self) -> None:
        if self.run_missing_logo_pipeline_var.get():
            self.input_mode_var.set("file")
            return
        self.input_mode_var.set("file")
        self.selected_tags.clear()
        self._refresh_tag_chips()
        self.shipstation_tag_var.set("")

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

    def _browse_directory(self, var: StringVar) -> None:
        dirname = filedialog.askdirectory()
        if dirname:
            var.set(dirname)

    def _browse_file(self, var: StringVar) -> None:
        filename = filedialog.askopenfilename()
        if filename:
            var.set(filename)

    def _browse_cl_csv(self) -> None:
        filename = filedialog.askopenfilename(
            title="Select Custom Label Database CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if filename:
            self.cl_csv_var.set(filename)
