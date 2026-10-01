"""Missing Run GUI — stable façade over gui_build / gui_config / gui_run."""

from __future__ import annotations

import queue
from datetime import date
from tkinter import BooleanVar, StringVar, Tk, messagebox

from scripts.gui_theme import apply_theme

from . import gui_build, gui_config, gui_run
from .core import (
    ALL_ORDERS_PATH,
    DEFAULT_MISSING_INPUT,
    DEFAULT_MISSING_TYPE,
)


class MissingRunApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Order Packing List Generator — Missing Run")
        self.date_var = StringVar(value=date.today().strftime("%d-%m-%Y"))
        self.shift_var = StringVar()
        self.process_name_var = StringVar()
        self.missing_type_var = StringVar(value=DEFAULT_MISSING_TYPE)
        self.missing_input_var = StringVar(value=str(DEFAULT_MISSING_INPUT))
        self.all_orders_var = StringVar(value=str(ALL_ORDERS_PATH))
        self.apparel_dir_var = StringVar()
        self.logo_custom_single_dir_var = StringVar()
        self.logo_custom_double_dir_var = StringVar()
        self.logo_normal_dir_var = StringVar()
        self.pdf_copy_dir_var = StringVar()
        self.excel_copy_dir_var = StringVar()
        self.use_demo_images_var = BooleanVar(value=False)
        self._log_queue: queue.Queue[str | None] | None = None
        self._run_output_root = None
        self._load_config()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _load_config(self) -> None:
        gui_config.load_missing_run_config(
            shift_var=self.shift_var,
            process_name_var=self.process_name_var,
            missing_type_var=self.missing_type_var,
            missing_input_var=self.missing_input_var,
            all_orders_var=self.all_orders_var,
            apparel_dir_var=self.apparel_dir_var,
            logo_custom_single_dir_var=self.logo_custom_single_dir_var,
            logo_custom_double_dir_var=self.logo_custom_double_dir_var,
            logo_normal_dir_var=self.logo_normal_dir_var,
            pdf_copy_dir_var=self.pdf_copy_dir_var,
            excel_copy_dir_var=self.excel_copy_dir_var,
            use_demo_images_var=self.use_demo_images_var,
        )

    def _save_config(self) -> None:
        gui_config.save_missing_run_config(
            date_var=self.date_var,
            shift_var=self.shift_var,
            process_name_var=self.process_name_var,
            missing_type_var=self.missing_type_var,
            missing_input_var=self.missing_input_var,
            all_orders_var=self.all_orders_var,
            apparel_dir_var=self.apparel_dir_var,
            logo_custom_single_dir_var=self.logo_custom_single_dir_var,
            logo_custom_double_dir_var=self.logo_custom_double_dir_var,
            logo_normal_dir_var=self.logo_normal_dir_var,
            pdf_copy_dir_var=self.pdf_copy_dir_var,
            excel_copy_dir_var=self.excel_copy_dir_var,
            use_demo_images_var=self.use_demo_images_var,
        )

    def _build_ui(self) -> None:
        gui_build.build_missing_run_ui(self)

    def _on_run(self) -> None:
        gui_run.on_run(self)

    def _browse_missing_input(self) -> None:
        gui_run.browse_missing_input(self)

    def _browse_all_orders(self) -> None:
        gui_run.browse_all_orders(self)

    def _browse_directory(self, var: StringVar) -> None:
        gui_run.browse_directory(var)

    def _append_log_ui(self, msg: str) -> None:
        gui_run.append_log_ui(self, msg)

    def _replace_log_step(self, msg: str) -> None:
        gui_run.replace_log_step(self, msg)

    def _drain_log_queue(self) -> bool:
        return gui_run.drain_log_queue(self)

    def _poll_log_queue(self) -> None:
        gui_run.poll_log_queue(self)

    def _on_run_success(self) -> None:
        self._drain_log_queue()
        output_root = self._run_output_root
        self._append_log_ui(f"Done. Outputs written to:\n  {output_root}")
        self.run_btn.configure(state="normal")
        self._save_config()
        messagebox.showinfo(
            "Finished",
            f"Missing run completed successfully.\n\nOutputs written to:\n  {output_root}",
        )

    def _on_run_error(self, message: str) -> None:
        self._drain_log_queue()
        self._append_log_ui(f"Error: {message}")
        self.run_btn.configure(state="normal")
        self._save_config()
        messagebox.showerror("Error", message)

    def _on_closing(self) -> None:
        self._save_config()
        self.root.destroy()


def launch_gui() -> None:
    root = Tk()
    apply_theme(root)
    MissingRunApp(root)
    root.deiconify()
    root.state("zoomed")
    root.lift()
    root.attributes("-topmost", True)
    root.after(200, lambda: root.attributes("-topmost", False))
    root.focus_force()
    root.mainloop()
