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
from pipeline_missing_run_app.gui_impl1 import MissingRunApp
from pipeline_missing_run_app.gui_impl2 import launch_gui


