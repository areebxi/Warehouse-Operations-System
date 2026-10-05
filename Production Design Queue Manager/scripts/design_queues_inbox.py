"""SharedInbox path helpers for Design Queues watcher."""

from __future__ import annotations

import logging
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

from PIL import Image

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

LOG = logging.getLogger("design_queues_watcher")
STABLE_SECONDS = 2.0
POLL_SECONDS = 3.0
DTF_NAME_RE = re.compile(r"dtf\s*des", re.IGNORECASE)


def _setup_logging() -> Path:
    logs_dir = wh.queue_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"design_queues_{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_path


def _inbox_root() -> Path:
    root = shared_inbox_dtf_des_root(APP_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    (root / "Processed").mkdir(parents=True, exist_ok=True)
    (root / "Failed").mkdir(parents=True, exist_ok=True)
    return root


def _is_inbox_candidate(path: Path, inbox_root: Path) -> bool:
    if not path.is_file():
        return False
    if path.name.startswith("~$"):
        return False
    if path.suffix.lower() not in (".xlsx", ".xls", ".csv"):
        return False
    if not DTF_NAME_RE.search(path.name):
        return False
    try:
        rel = path.resolve().relative_to(inbox_root.resolve())
    except ValueError:
        return False
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in ("Processed", "Failed"):
        return False
    return True


def _iter_inbox_files(inbox_root: Path) -> list[Path]:
    found: list[Path] = []
    for p in inbox_root.rglob("*"):
        if _is_inbox_candidate(p, inbox_root):
            found.append(p)
    return sorted(found)


def _wait_stable(path: Path, seconds: float = STABLE_SECONDS) -> bool:
    try:
        size1 = path.stat().st_size
        time.sleep(seconds)
        size2 = path.stat().st_size
        return size1 == size2 and size2 > 0
    except OSError:
        return False


def _rel_date_shift(path: Path, inbox_root: Path) -> tuple[str, str]:
    """Infer date/shift from Shared Inbox/DTF Des/{date}/{shift}/file."""
    try:
        rel = path.resolve().relative_to(inbox_root.resolve())
        parts = rel.parts
        if len(parts) >= 3:
            return parts[0], parts[1]
        if len(parts) == 2:
            return parts[0], "Shift"
    except ValueError:
        pass
    return datetime.now().strftime("%d-%m-%Y"), "Shift"


def _move_to(path: Path, inbox_root: Path, bucket: str) -> Path:
    date_part, shift_part = _rel_date_shift(path, inbox_root)
    dest_dir = inbox_root / bucket / date_part / shift_part
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    if dest.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = dest_dir / f"{path.stem}_{stamp}{path.suffix}"
    shutil.move(str(path), str(dest))
    return dest
