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
from src.core.canvas_arranger import pack_designs  # noqa: E402
from src.core.canvas_creation import create_canvas_image, save_canvas_image  # noqa: E402
from src.core.design_processor import (  # noqa: E402
    process_personalised_designs,
    process_single_designs,
)
from src.core import DEFAULT_DESIGN_PADDING  # noqa: E402
from src.io import load_color_bar_from_app_dir, load_configuration_workbook  # noqa: E402
from src.system import create_settings_manager, setup_error_logging  # noqa: E402
from gui_helpers.processing.gui_processing_helpers_folder import (  # noqa: E402
    auto_detect_customise_column,
    auto_detect_order_column,
    auto_detect_sku_column,
    load_dataframe_from_file,
)
from gui_helpers.processing.gui_processing_helpers_messages import (  # noqa: E402
    is_customise_yes,
    is_plainlg_sku,
)

LOG = logging.getLogger("auto_missing_logo_watcher")
STABLE_SECONDS = 2.0
POLL_SECONDS = 3.0
DTF_NAME_RE = re.compile(r"dtf\s*des", re.IGNORECASE)


def _setup_logging() -> Path:
    logs_dir = APP_ROOT / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / f"auto_missing_logo_{datetime.now().strftime('%Y%m%d')}.log"
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


def _build_ctx(settings: dict) -> SimpleNamespace:
    size_df, size_path, overrides = load_configuration_workbook(str(APP_ROOT))
    color_bar_image, color_bar_path = load_color_bar_from_app_dir(str(APP_ROOT))
    dpi = 300
    return SimpleNamespace(
        canvas_width_mm=570.0,
        canvas_height_mm=3000.0,
        dpi=dpi,
        mm_to_pixel=dpi / 25.4,
        design_padding=DEFAULT_DESIGN_PADDING,
        designs_folder=settings.get("designs_folder") or None,
        single_designs_folder=settings.get("single_designs_folder") or None,
        double_designs_folder=settings.get("double_designs_folder") or None,
        size_reference_df=size_df,
        size_reference_path=size_path,
        print_size_overrides=overrides or {},
        pocket_design_ids_set=set((overrides or {}).keys()),
        color_bar_image=color_bar_image,
        color_bar_path=color_bar_path,
        is_personalised=True,
    )


def _output_stem(file_path: Path) -> str:
    stem = re.sub(r"^DTF\s*Des-", "", file_path.stem, flags=re.IGNORECASE).strip()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_{stamp}"


def _save_batches(ctx: SimpleNamespace, batches: list, file_path: Path) -> list[Path]:
    out_dir = APP_ROOT / "Output" / datetime.now().strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = _output_stem(file_path)
    # DES label without timestamp for canvas text; file name keeps timestamp
    des_label = re.sub(r"^DTF\s*Des-", "", file_path.stem, flags=re.IGNORECASE).strip()
    saved: list[Path] = []
    for i, batch in enumerate(batches, 1):
        part_text = f"PART {i}" if len(batches) > 1 else None
        canvas = create_canvas_image(
            batch,
            ctx.canvas_width_mm,
            ctx.canvas_height_mm,
            ctx.mm_to_pixel,
            ctx.dpi,
            color_bar_image=ctx.color_bar_image,
            des_text=des_label,
            part_text=part_text,
        )
        if len(batches) > 1:
            out_path = out_dir / f"{stem}_Part {i}.png"
        else:
            out_path = out_dir / f"{stem}.png"
        save_canvas_image(canvas, str(out_path), ctx.dpi)
        saved.append(out_path)
    return saved


def process_missing_logo_file_headless(ctx: SimpleNamespace, file_path: Path) -> list[Path]:
    df = load_dataframe_from_file(str(file_path))
    order_column = auto_detect_order_column(df)
    sku_column = auto_detect_sku_column(df)
    if not order_column or not sku_column:
        raise ValueError("DTF Des missing Order Number or Item SKU column")
    if not (
        ctx.single_designs_folder or ctx.double_designs_folder or ctx.designs_folder
    ):
        raise ValueError(
            "No design folders in queue_app_settings.json "
            "(designs_folder / single_designs_folder / double_designs_folder)"
        )

    customise_col = auto_detect_customise_column(df)
    mask = df[order_column].notna() & df[sku_column].notna()
    order_numbers = df.loc[mask, order_column].tolist()
    item_skus = df.loc[mask, sku_column].tolist()
    customise_vals = (
        df.loc[mask, customise_col].tolist() if customise_col else [None] * len(order_numbers)
    )

    designs = []
    order_total_counts: dict = {}
    for order_number in order_numbers:
        order_total_counts[order_number] = order_total_counts.get(order_number, 0) + 1
    order_occurrences: dict = {}

    for order_number, item_sku, customise in zip(order_numbers, item_skus, customise_vals):
        if is_plainlg_sku(item_sku):
            continue
        order_occurrences[order_number] = order_occurrences.get(order_number, 0) + 1
        duplicate_index = order_occurrences[order_number] - 1
        is_duplicate_order = order_total_counts.get(order_number, 0) > 1
        force_single = is_customise_yes(customise)
        design_items = []
        if ctx.single_designs_folder or ctx.double_designs_folder:
            design_items = process_personalised_designs(
                order_number,
                item_sku,
                duplicate_index,
                is_duplicate_order,
                ctx.single_designs_folder,
                ctx.double_designs_folder,
                ctx.size_reference_df,
                ctx.mm_to_pixel,
                ctx.canvas_width_mm,
                ctx.design_padding,
                ctx.print_size_overrides or ctx.pocket_design_ids_set,
                canvas_height_mm=ctx.canvas_height_mm,
                force_single=force_single,
            )
        if not design_items and ctx.designs_folder:
            design_items = process_single_designs(
                item_sku,
                ctx.designs_folder,
                ctx.size_reference_df,
                ctx.mm_to_pixel,
                ctx.print_size_overrides or ctx.pocket_design_ids_set,
                canvas_width_mm=ctx.canvas_width_mm,
                canvas_height_mm=ctx.canvas_height_mm,
                design_padding=ctx.design_padding,
                force_single=force_single,
            )
        for design_data in design_items:
            designs.append(
                {
                    "sku": design_data["sku"],
                    "image": design_data["image"],
                    "path": design_data["path"],
                    "width": design_data["width"],
                    "height": design_data["height"],
                    "width_mm": design_data["width_mm"],
                    "height_mm": design_data["height_mm"],
                    "size_code": design_data.get("size_code"),
                    "design_type": design_data.get("design_type", "single"),
                }
            )

    if not designs:
        raise ValueError("No designs found for Missing Logo auto-run")

    batches = pack_designs(
        designs,
        ctx.canvas_width_mm,
        ctx.canvas_height_mm,
        ctx.mm_to_pixel,
        ctx.design_padding,
    )
    return _save_batches(ctx, batches, file_path)


def process_one(path: Path, ctx: SimpleNamespace, inbox_root: Path) -> bool:
    LOG.info("Processing %s", path)
    try:
        if not _wait_stable(path):
            LOG.warning("File not stable yet, will retry: %s", path)
            return False
        saved = process_missing_logo_file_headless(ctx, path)
        dest = _move_to(path, inbox_root, "Processed")
        LOG.info("Saved %s PNG(s); moved to %s", len(saved), dest)
        for p in saved:
            LOG.info("  PNG: %s", p)
        return True
    except Exception as exc:
        LOG.exception("Failed %s: %s", path, exc)
        try:
            if path.exists():
                failed = _move_to(path, inbox_root, "Failed")
                LOG.info("Moved to Failed: %s", failed)
        except OSError as move_exc:
            LOG.error("Could not move to Failed: %s", move_exc)
        return False


def run_once() -> int:
    setup_error_logging()
    settings_manager = create_settings_manager()
    settings = settings_manager.saved_settings or {}
    ctx = _build_ctx(settings)
    inbox_root = _inbox_root()
    files = _iter_inbox_files(inbox_root)
    if not files:
        LOG.info("No pending DTF Des files in %s", inbox_root)
        return 0
    n_ok = 0
    for f in files:
        if process_one(f, ctx, inbox_root):
            n_ok += 1
    return n_ok


def watch_loop() -> None:
    setup_error_logging()
    settings_manager = create_settings_manager()
    settings = settings_manager.saved_settings or {}
    ctx = _build_ctx(settings)
    inbox_root = _inbox_root()
    LOG.info("Watching %s (Missing Logo auto-run)", inbox_root)
    LOG.info(
        "Folders: designs=%s single=%s double=%s",
        ctx.designs_folder,
        ctx.single_designs_folder,
        ctx.double_designs_folder,
    )
    seen_failed: set[str] = set()
    while True:
        try:
            # Reload settings periodically so folder changes apply
            settings_manager = create_settings_manager()
            settings = settings_manager.saved_settings or {}
            ctx = _build_ctx(settings)
            for f in _iter_inbox_files(inbox_root):
                key = str(f.resolve())
                if key in seen_failed:
                    continue
                ok = process_one(f, ctx, inbox_root)
                if not ok and f.exists():
                    # still in inbox (unstable) — retry next poll
                    pass
                elif not ok:
                    seen_failed.add(key)
        except Exception:
            LOG.exception("Watcher loop error")
        time.sleep(POLL_SECONDS)


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
    watch_loop()


if __name__ == "__main__":
    main()
