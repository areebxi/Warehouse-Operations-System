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
from pipeline_runtime.runner_utils import (
    _FILENAME_UNSAFE,
    _shift_subdir_name,
)
from pipeline_shipstation.client import ShipStationClient
from pipeline_shipstation.credentials import load_shipstation_credentials
from pipeline_shipstation.orders_to_csv import fetch_tag_orders_to_csv
from pipeline_shipstation.sync_tags_xlsx import DEFAULT_XLSX_PATH
from pipeline_shipstation.tags_process_lookup import (
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

from .app_config import PreflightConfigMixin
from .app_files import PreflightFilesMixin
from .app_run import PreflightRunMixin
from .app_tags_controls import PreflightTagsControlsMixin
from .app_tags_load import PreflightTagsLoadMixin
from .app_ui import PreflightUiMixin

class PreflightIssuesApp(PreflightConfigMixin, PreflightFilesMixin, PreflightRunMixin, PreflightTagsControlsMixin, PreflightTagsLoadMixin, PreflightUiMixin):
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Order Packing List Generator — Preflight Issues")

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

UnmatchedSkusApp = PreflightIssuesApp
