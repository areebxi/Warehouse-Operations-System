from __future__ import annotations

import json
import queue
import sys
import threading
from datetime import date
from pathlib import Path
from tkinter import DISABLED, END, NORMAL, StringVar, BooleanVar, Tk, filedialog, messagebox

from scripts.gui_theme import apply_theme, refresh_tag_chip_grid, set_listbox_enabled, set_tag_chip_grid_enabled
from pipeline_shipstation.client import ShipStationClient
from pipeline_shipstation.credentials import load_shipstation_credentials
from pipeline_shipstation.tags_process_lookup import (
    lookup_process_number,
    parse_shipstation_tags_config,
    shipstation_tags_config_payload,
)

from .config import CONFIG_DIR, CONFIG_KEYS, CONFIG_PATH, DEFAULT_CL_CSV, DEFAULT_OUTPUT_DIR, DEFAULT_WORKBOOK, PROJECT_ROOT
from .runner import (
    drain_log_queue,
    get_input_paths,
    on_pipeline_error,
    on_pipeline_success,
    on_run_clicked,
    poll_log_queue,
)
from .ui import build_ui, on_fixed_process_toggle, on_separate_by_logo_toggle

from .app_config import PackingListConfigMixin
from .app_files import PackingListFilesMixin
from .app_input_mode import PackingListInputModeMixin
from .app_tags import PackingListTagsMixin

class PackingListApp(PackingListConfigMixin, PackingListFilesMixin, PackingListInputModeMixin, PackingListTagsMixin):
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Order Packing List Generator")
        self.input_csv_var = StringVar()
        self.date_var = StringVar(value=date.today().strftime("%d-%m-%Y"))
        self.shift_var = StringVar()
        self.output_dir_var = StringVar(value=str(DEFAULT_OUTPUT_DIR))
        self.workbook_var = StringVar(value=str(DEFAULT_WORKBOOK))
        self.cl_csv_var = StringVar(value=str(DEFAULT_CL_CSV))
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
        self.make_design_queues_var = BooleanVar(value=True)
        self.use_demo_images_var = BooleanVar(value=False)
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
        self.root.after(300, self._ensure_design_queues_watcher)
    def _ensure_design_queues_watcher(self) -> None:
        """Start Queue SharedInbox watcher if it is not already running."""
        try:
            from shared.design_queues_watcher import ensure_running

            status, message = ensure_running()
            print(message, flush=True)
            if status == "failed":
                try:
                    messagebox.showwarning("Design Queues watcher", message)
                except Exception:
                    pass
        except Exception as exc:
            print(f"Could not ensure Design Queues watcher: {exc}", flush=True)
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
