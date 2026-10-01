from pathlib import Path
from tkinter import END, StringVar, filedialog, messagebox


class PreflightFilesMixin:

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
        path = filedialog.askdirectory(title="Select Normal Design folder")
        if path:
            self.logo_normal_dir_var.set(path)


    def _browse_logo_custom_single_dir(self) -> None:
        path = filedialog.askdirectory(title="Select Customise Single Position Design folder")
        if path:
            self.logo_custom_single_dir_var.set(path)


    def _browse_logo_custom_double_dir(self) -> None:
        path = filedialog.askdirectory(title="Select Customise Double Position Design folder")
        if path:
            self.logo_custom_double_dir_var.set(path)


    def _validate_image_folders(self) -> bool:
        folders = (
            ("Apparel Image folder", self.apparel_dir_var.get()),
            ("Normal Design folder", self.logo_normal_dir_var.get()),
            ("Customise Single Position Design folder", self.logo_custom_single_dir_var.get()),
            ("Customise Double Position Design folder", self.logo_custom_double_dir_var.get()),
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

