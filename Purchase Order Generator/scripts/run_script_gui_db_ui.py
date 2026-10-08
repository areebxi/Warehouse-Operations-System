"""PO GUI: Custom Label / Plain / Packs database file pickers."""

from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from run_script_gui_settings import (
    KEY_CL_CSV,
    KEY_PACKS_DB,
    KEY_PLAIN_DB,
    default_cl_csv_path,
    default_packs_database_path,
    default_plain_database_path,
    save_gui_settings,
)


class ShipStationGuiDbUiMixin:
    def _add_db_path_row(
        self,
        main_frame: ttk.Frame,
        row: int,
        label: str,
        var: tk.StringVar,
        browse_cmd,
        clear_cmd,
    ) -> None:
        ttk.Label(main_frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=var, state="readonly").grid(
            row=row, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0)
        )
        btns = ttk.Frame(main_frame)
        btns.grid(row=row, column=2, sticky=(tk.W, tk.E), padx=(20, 0))
        ttk.Button(btns, text="Browse...", command=browse_cmd).pack(side=tk.LEFT)
        ttk.Button(btns, text="Remove", command=clear_cmd).pack(side=tk.LEFT, padx=(6, 0))

    def setup_db_path_rows(self, main_frame: ttk.Frame, start_row: int = 3) -> int:
        """Add CL / Plain / Packs rows; return next free row index."""
        self._add_db_path_row(
            main_frame,
            start_row,
            "Custom Label CSV:",
            self.cl_csv_var,
            self.browse_cl_csv,
            self.clear_cl_csv,
        )
        self._add_db_path_row(
            main_frame,
            start_row + 1,
            "Plain Database:",
            self.plain_db_var,
            self.browse_plain_database,
            self.clear_plain_database,
        )
        self._add_db_path_row(
            main_frame,
            start_row + 2,
            "Packs Database:",
            self.packs_db_var,
            self.browse_packs_database,
            self.clear_packs_database,
        )
        return start_row + 3

    def _browse_db_file(
        self,
        *,
        title: str,
        filetypes: list[tuple[str, str]],
        var: tk.StringVar,
        settings_key: str,
        log_label: str,
    ) -> None:
        initial = var.get().strip()
        initialdir = None
        if initial:
            parent = os.path.dirname(initial)
            if parent and os.path.isdir(parent):
                initialdir = parent
        chosen = filedialog.askopenfilename(
            title=title,
            initialdir=initialdir,
            filetypes=filetypes,
        )
        if not chosen:
            return
        var.set(chosen)
        self.gui_settings[settings_key] = chosen
        save_gui_settings(self.gui_settings)
        self.log_message(f"[SETTINGS] {log_label} set to: {chosen}")

    def _clear_db_file(
        self,
        *,
        var: tk.StringVar,
        settings_key: str,
        default: Path,
        log_label: str,
    ) -> None:
        if not self.gui_settings.get(settings_key) and var.get().strip() == str(default):
            self.log_message(f"[SETTINGS] No {log_label} override to remove.")
            return
        self.gui_settings.pop(settings_key, None)
        save_gui_settings(self.gui_settings)
        var.set(str(default))
        self.log_message(f"[SETTINGS] {log_label} reset to default: {default}")

    def browse_cl_csv(self) -> None:
        self._browse_db_file(
            title="Select Custom Label Database CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            var=self.cl_csv_var,
            settings_key=KEY_CL_CSV,
            log_label="Custom Label CSV",
        )

    def clear_cl_csv(self) -> None:
        self._clear_db_file(
            var=self.cl_csv_var,
            settings_key=KEY_CL_CSV,
            default=default_cl_csv_path(),
            log_label="Custom Label CSV",
        )

    def browse_plain_database(self) -> None:
        self._browse_db_file(
            title="Select Plain Database",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            var=self.plain_db_var,
            settings_key=KEY_PLAIN_DB,
            log_label="Plain Database",
        )

    def clear_plain_database(self) -> None:
        self._clear_db_file(
            var=self.plain_db_var,
            settings_key=KEY_PLAIN_DB,
            default=default_plain_database_path(),
            log_label="Plain Database",
        )

    def browse_packs_database(self) -> None:
        self._browse_db_file(
            title="Select Packs Database",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            var=self.packs_db_var,
            settings_key=KEY_PACKS_DB,
            log_label="Packs Database",
        )

    def clear_packs_database(self) -> None:
        self._clear_db_file(
            var=self.packs_db_var,
            settings_key=KEY_PACKS_DB,
            default=default_packs_database_path(),
            log_label="Packs Database",
        )
