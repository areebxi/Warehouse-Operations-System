"""PO GUI layout + small UI helpers."""

from __future__ import annotations

import os
import shutil
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk

from run_script_gui_settings import save_gui_settings


class ShipStationGuiUiMixin:
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)

        title_label = ttk.Label(main_frame, text="Purchase Order App", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        ttk.Label(main_frame, text="Tag Name:").grid(row=1, column=0, sticky=tk.W, pady=5)

        self.tag_combobox = ttk.Combobox(
            main_frame, textvariable=self.tag_name_var, width=30, state="readonly"
        )
        self.tag_combobox.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))

        tag_names = list(self.tag_mapping.keys())
        self.tag_combobox["values"] = sorted(tag_names)
        self.tag_combobox.bind("<<ComboboxSelected>>", self.on_tag_selected)

        self.run_button = ttk.Button(main_frame, text="Run", command=self.run_script)
        self.run_button.grid(row=1, column=2, sticky=(tk.W, tk.E), padx=(20, 0))

        ttk.Label(main_frame, text="PDF copy folder:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pdf_copy_entry = ttk.Entry(
            main_frame, textvariable=self.pdf_copy_folder_var, state="readonly"
        )
        self.pdf_copy_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        pdf_folder_btns = ttk.Frame(main_frame)
        pdf_folder_btns.grid(row=2, column=2, sticky=(tk.W, tk.E), padx=(20, 0))
        self.browse_button = ttk.Button(
            pdf_folder_btns, text="Browse...", command=self.browse_pdf_copy_folder
        )
        self.browse_button.pack(side=tk.LEFT)
        self.clear_pdf_folder_button = ttk.Button(
            pdf_folder_btns, text="Remove", command=self.clear_pdf_copy_folder
        )
        self.clear_pdf_folder_button.pack(side=tk.LEFT, padx=(6, 0))

        self.logs_text = scrolledtext.ScrolledText(
            main_frame, height=20, width=80, font=("Consolas", 9)
        )
        self.logs_text.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0)
        )

        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        self.status_label = ttk.Label(main_frame, text="Ready", font=("Arial", 9))
        self.status_label.grid(row=5, column=0, columnspan=3, pady=(5, 0))

    def browse_pdf_copy_folder(self):
        """Let the user pick a folder; remember it for later runs."""
        initial = self.pdf_copy_folder_var.get().strip()
        if not initial or not os.path.isdir(initial):
            initial = None
        chosen = filedialog.askdirectory(
            title="Select PDF copy folder",
            initialdir=initial or None,
            mustexist=True,
        )
        if not chosen:
            return
        self.pdf_copy_folder_var.set(chosen)
        self.gui_settings["pdf_copy_folder"] = chosen
        save_gui_settings(self.gui_settings)
        self.log_message(f"[SETTINGS] PDF copy folder set to: {chosen}")

    def clear_pdf_copy_folder(self):
        """Clear the remembered PDF copy folder."""
        if not self.pdf_copy_folder_var.get().strip() and not self.gui_settings.get(
            "pdf_copy_folder"
        ):
            self.log_message("[SETTINGS] No PDF copy folder to remove.")
            return
        self.pdf_copy_folder_var.set("")
        self.gui_settings.pop("pdf_copy_folder", None)
        save_gui_settings(self.gui_settings)
        self.log_message("[SETTINGS] PDF copy folder removed.")

    def log_message(self, message: str):
        self.logs_text.insert(tk.END, f"{message}\n")
        self.logs_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, status: str):
        self.status_label.config(text=status)

    def on_tag_selected(self, event):
        """Set Tag ID when a Tag Name is selected."""
        selected_tag_name = self.tag_name_var.get()
        if selected_tag_name in self.tag_mapping:
            self.selected_tag_id = self.tag_mapping[selected_tag_name]
            self.selected_tag_name = selected_tag_name
            self.log_message(f"Selected Tag: {selected_tag_name} (ID: {self.selected_tag_id})")
        else:
            self.selected_tag_id = None
            self.selected_tag_name = None

    def copy_pdf_to_selected_folder(self, pdf_output_path: str) -> None:
        """Copy a generated PDF into the remembered folder, if configured."""
        dest_folder = self.pdf_copy_folder_var.get().strip()
        if not dest_folder:
            self.log_message("[PDF] Copy skipped — no PDF copy folder selected (use Browse).")
            return
        if not os.path.isdir(dest_folder):
            self.log_message(
                f"[WARNING] PDF copy skipped — folder does not exist: {dest_folder} "
                "(use Browse to pick a new folder)."
            )
            return
        try:
            dest_path = shutil.copy2(pdf_output_path, dest_folder)
            self.log_message(f"[SUCCESS] PDF copied to: {os.path.abspath(dest_path)}")
        except Exception as e:
            self.log_message(f"[WARNING] PDF copy failed: {e}")
