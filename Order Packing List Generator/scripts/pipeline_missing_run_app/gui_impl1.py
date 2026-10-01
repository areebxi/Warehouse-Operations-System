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
from pipeline_missing_run_app.gui_impl1_mixin1 import MissingRunAppMixin1
from pipeline_missing_run_app.gui_impl1_mixin2 import MissingRunAppMixin2

class MissingRunApp(MissingRunAppMixin1, MissingRunAppMixin2):
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
        self._run_output_root: Path | None = None
        self._load_config()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)


