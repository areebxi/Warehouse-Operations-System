"""
Headless Design Queues watcher for Shared Inbox/DTF Des.

Watches warehouse Shared Inbox/DTF Des/{date}/{shift}/ for new DTF Des files,
runs Design Queues using folders from queue_app_settings.json, auto-saves PNG
(and copies to DTF Queues folder when configured), then moves inbox sources to
Processed/ (or Failed/). Skip Batches sheet skips queue PNGs for listed codes.

No Tk GUI. No approval gate. PNG names match GUI (P50.png); re-runs overwrite.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

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

from design_queues_inbox import _setup_logging  # noqa: E402
from design_queues_loop import run_files, run_once, watch_loop  # noqa: E402

LOG = logging.getLogger("design_queues_watcher")


def main() -> None:
    parser = argparse.ArgumentParser(description="Design Queues watcher for Shared Inbox")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process current inbox files once and exit",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        metavar="PATH",
        help="Process these DTF Des files then exit (Packing sync step)",
    )
    args = parser.parse_args()
    _setup_logging()
    if args.files:
        paths = [Path(p) for p in args.files]
        n = run_files(paths)
        raise SystemExit(0 if n == len(paths) else 1)
    if args.once:
        n = run_once()
        raise SystemExit(0 if n >= 0 else 1)
    from shared.design_queues_watcher import claim_this_process

    claim_this_process()
    watch_loop()


if __name__ == "__main__":
    main()
