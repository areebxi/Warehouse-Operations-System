"""
Headless Missing Logo watcher for Shared Inbox/DTF Des.

Watches warehouse Shared Inbox/DTF Des/{date}/{shift}/ for new DTF Des files,
runs Missing Logo using folders from queue_app_settings.json, auto-saves PNG
with unique timestamps, then moves the source to Processed/ (or Failed/).

No Tk GUI. No approval gate. Re-runs always generate a new queue PNG.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import pandas as pd
from PIL import Image

# Queue app paths
APP_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = APP_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
WAREHOUSE_ROOT = APP_ROOT.parent
if str(WAREHOUSE_ROOT) not in sys.path:
    sys.path.insert(0, str(WAREHOUSE_ROOT))

Image.MAX_IMAGE_PIXELS = None

from shared.cl_sku_match import shared_inbox_dtf_des_root  # noqa: E402
from shared import paths as wh  # noqa: E402
from src.core.canvas_arranger import pack_designs  # noqa: E402
from src.core.canvas_creation import create_canvas_image, save_canvas_image  # noqa: E402
from src.core.design_folder_routing import find_designs_for_dtf_row  # noqa: E402
from src.core import DEFAULT_DESIGN_PADDING  # noqa: E402
from src.io import load_color_bar_from_app_dir, load_queue_data_sources  # noqa: E402
from src.system import create_settings_manager, setup_error_logging  # noqa: E402
from gui_helpers.processing.gui_processing_helpers_folder import (  # noqa: E402
    auto_detect_customise_column,
    auto_detect_order_column,
    auto_detect_sku_column,
    load_dataframe_from_file,
)
from gui_helpers.processing.gui_processing_helpers_messages import (  # noqa: E402
    is_plainlg_sku,
)
from auto_missing_logo_watcher_impl1 import (  # noqa: E402
    _build_ctx,
    _is_inbox_candidate,
    _output_stem,
    process_missing_logo_file_headless,
    watch_loop,
)
from auto_missing_logo_watcher_impl2 import (  # noqa: E402
    _inbox_root,
    _iter_inbox_files,
    _move_to,
    _rel_date_shift,
    _save_batches,
    _setup_logging,
    _wait_stable,
    process_one,
    run_once,
)

LOG = logging.getLogger("auto_missing_logo_watcher")
STABLE_SECONDS = 2.0
POLL_SECONDS = 3.0
DTF_NAME_RE = re.compile(r"dtf\s*des", re.IGNORECASE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto Missing Logo watcher for Shared Inbox")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process current inbox files once and exit",
    )
    args = parser.parse_args()
    _setup_logging()
    if args.once:
        n = run_once()
        raise SystemExit(0 if n >= 0 else 1)
    from shared.missing_logo_watcher import claim_this_process

    claim_this_process()
    watch_loop()


if __name__ == "__main__":
    main()
