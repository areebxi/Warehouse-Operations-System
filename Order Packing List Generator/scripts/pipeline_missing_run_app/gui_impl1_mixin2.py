from __future__ import annotations
import json
import queue
import sys
import threading
from datetime import date, datetime
from pathlib import Path
from tkinter import BOTH, DISABLED, END, NORMAL, StringVar, BooleanVar, Tk, filedialog, messagebox, ttk
from scripts.gui_theme import apply_theme, make_log_text, make_scrollable_form
from pipeline_packing_list_app.config import logs_directory
from pipeline_runtime.pipeline_log import PipelineLog
from pipeline_runtime.runner_utils import _sanitize_process_for_filename
from .core import (
    ALL_ORDERS_PATH,
    CONFIG_DIR,
    DEFAULT_MISSING_INPUT,
    DEFAULT_MISSING_TYPE,
    MISSING_PDF_SUBDIRS,
    MISSING_RUN_CONFIG,
    PROJECT_ROOT,
    resolve_missing_pdf_copy_dir,
    run_missing_run_from_all_orders,
)

class MissingRunAppMixin2:
    def _load_config(self) -> None:
        data = None
        for path in (MISSING_RUN_CONFIG, PROJECT_ROOT / "missing_run_config.json"):
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
        self.shift_var.set(str(data.get("shift", "")).strip())
        self.process_name_var.set(str(data.get("process_name", "")).strip())
        missing_type = str(data.get("missing_type", "")).strip()
        if missing_type in MISSING_PDF_SUBDIRS:
            self.missing_type_var.set(missing_type)
        for key, var in [
            ("missing_input", self.missing_input_var), ("all_orders", self.all_orders_var), ("apparel_dir", self.apparel_dir_var),
            ("logo_custom_single_dir", self.logo_custom_single_dir_var), ("logo_custom_double_dir", self.logo_custom_double_dir_var),
            ("logo_normal_dir", self.logo_normal_dir_var),             ("pdf_copy_dir", self.pdf_copy_dir_var), ("excel_copy_dir", self.excel_copy_dir_var),
        ]:
            val = str(data.get(key, "")).strip()
            if val:
                var.set(val)
        if isinstance(data.get("use_demo_images"), bool):
            self.use_demo_images_var.set(data["use_demo_images"])
        legacy_logo_custom = str(data.get("logo_custom_dir", "")).strip()
        if not self.logo_custom_single_dir_var.get() and legacy_logo_custom:
            self.logo_custom_single_dir_var.set(legacy_logo_custom)

    def _save_config(self) -> None:
        data = {
            "date": self.date_var.get().strip(),
            "shift": self.shift_var.get().strip(),
            "process_name": self.process_name_var.get().strip(),
            "missing_type": self.missing_type_var.get().strip() or DEFAULT_MISSING_TYPE,
            "missing_input": self.missing_input_var.get().strip(),
            "all_orders": self.all_orders_var.get().strip(),
            "apparel_dir": (self.apparel_dir_var.get() or "").strip(),
            "logo_custom_single_dir": (self.logo_custom_single_dir_var.get() or "").strip(),
            "logo_custom_double_dir": (self.logo_custom_double_dir_var.get() or "").strip(),
            "logo_normal_dir": (self.logo_normal_dir_var.get() or "").strip(),
            "pdf_copy_dir": (self.pdf_copy_dir_var.get() or "").strip(),
            "excel_copy_dir": (self.excel_copy_dir_var.get() or "").strip(),
            "use_demo_images": self.use_demo_images_var.get(),
        }
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            MISSING_RUN_CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"[missing run] config save failed ({MISSING_RUN_CONFIG}): {exc}", file=sys.stderr, flush=True)

    def _drain_log_queue(self) -> bool:
        if self._log_queue is None:
            return False
        last_step: str | None = None
        while True:
            try:
                msg = self._log_queue.get_nowait()
            except queue.Empty:
                if last_step is not None:
                    self._replace_log_step(last_step)
                return False
            if msg is None:
                if last_step is not None:
                    self._replace_log_step(last_step)
                return True
            last_step = msg

    def _on_run_success(self) -> None:
        self._drain_log_queue()
        output_root = self._run_output_root
        self._append_log_ui(f"Done. Outputs written to:\n  {output_root}")
        self.run_btn.configure(state=NORMAL)
        self._save_config()
        messagebox.showinfo("Finished", f"Missing run completed successfully.\n\nOutputs written to:\n  {output_root}")

    def _replace_log_step(self, msg: str) -> None:
        self.log.configure(state=NORMAL)
        self.log.delete("1.0", END)
        self.log.insert(END, msg)
        self.log.see(END)
        self.log.configure(state=DISABLED)

    def _on_run_error(self, message: str) -> None:
        self._drain_log_queue()
        self._append_log_ui(f"Error: {message}")
        self.run_btn.configure(state=NORMAL)
        self._save_config()
        messagebox.showerror("Error", message)

    def _append_log_ui(self, msg: str) -> None:
        self.log.configure(state=NORMAL)
        self.log.insert(END, "\n" + msg)
        self.log.see(END)
        self.log.configure(state=DISABLED)

    def _browse_missing_input(self) -> None:
        path = filedialog.askopenfilename(title="Select Missing Input CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.missing_input_var.set(path)

    def _browse_all_orders(self) -> None:
        path = filedialog.askopenfilename(title="Select All Orders CSV", filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.all_orders_var.set(path)

    def _browse_directory(self, var: StringVar) -> None:
        dirname = filedialog.askdirectory()
        if dirname:
            var.set(dirname)

    def _poll_log_queue(self) -> None:
        if self._drain_log_queue():
            return
        self.root.after(200, self._poll_log_queue)

    def _on_closing(self) -> None:
        self._save_config()
        self.root.destroy()

