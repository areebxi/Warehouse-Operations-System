"""Poll / once-run / --files loop for SharedInbox Design Queues watcher."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Sequence

from src.system import create_settings_manager, setup_error_logging
from design_queues_inbox import (
    LOG,
    POLL_SECONDS,
    WAREHOUSE_ROOT,
    _inbox_root,
    _iter_inbox_files,
    _move_to,
    _wait_stable,
)
from design_queues_process import _build_ctx, process_design_queues_file_headless
from design_queues_skip import apply_skip_batches, load_skip_batches


def _under_inbox(path: Path, inbox_root: Path) -> bool:
    try:
        path.resolve().relative_to(inbox_root.resolve())
        return True
    except ValueError:
        return False


def process_one(
    path: Path,
    ctx: SimpleNamespace,
    inbox_root: Path,
    *,
    skip_batches: Optional[set[str]] = None,
) -> bool:
    LOG.info("Processing %s", path)
    try:
        if not path.is_file():
            LOG.warning("Missing file: %s", path)
            return False
        if not _wait_stable(path):
            LOG.warning("File not stable yet, will retry: %s", path)
            return False

        skips = skip_batches if skip_batches is not None else load_skip_batches(
            getattr(ctx, "config_workbook_path", None)
        )
        if apply_skip_batches(
            path,
            ctx,
            skips,
            log=LOG,
            under_inbox=lambda p: _under_inbox(p, inbox_root),
            move_to_processed=lambda p: _move_to(p, inbox_root, "Processed"),
        ):
            return True

        if str(WAREHOUSE_ROOT) not in sys.path:
            sys.path.insert(0, str(WAREHOUSE_ROOT))
        from shared.demo_images import demo_image_lookup

        with demo_image_lookup(getattr(ctx, "use_demo_images", False)):
            saved = process_design_queues_file_headless(ctx, path)
        if _under_inbox(path, inbox_root):
            dest = _move_to(path, inbox_root, "Processed")
            LOG.info("Saved %s PNG(s); moved to %s", len(saved), dest)
        else:
            LOG.info("Saved %s PNG(s); left source in place: %s", len(saved), path)
        for p in saved:
            LOG.info("  PNG: %s", p)
        return True
    except Exception as exc:
        LOG.exception("Failed %s: %s", path, exc)
        try:
            if path.exists() and _under_inbox(path, inbox_root):
                failed = _move_to(path, inbox_root, "Failed")
                LOG.info("Moved to Failed: %s", failed)
        except OSError as move_exc:
            LOG.error("Could not move to Failed: %s", move_exc)
        return False


def _ctx_and_skips() -> tuple[SimpleNamespace, Path, set[str]]:
    setup_error_logging()
    settings_manager = create_settings_manager()
    settings = settings_manager.saved_settings or {}
    ctx = _build_ctx(settings)
    inbox_root = _inbox_root()
    skips = load_skip_batches(getattr(ctx, "config_workbook_path", None))
    if skips:
        LOG.info("Skip Batches loaded: %s", ", ".join(sorted(skips, key=int)))
    return ctx, inbox_root, skips


def run_once() -> int:
    ctx, inbox_root, skips = _ctx_and_skips()
    files = _iter_inbox_files(inbox_root)
    if not files:
        LOG.info("No pending DTF Des files in %s", inbox_root)
        return 0
    n_ok = 0
    for f in files:
        if process_one(f, ctx, inbox_root, skip_batches=skips):
            n_ok += 1
    return n_ok


def run_files(paths: Sequence[Path]) -> int:
    """Process explicit DTF Des paths (Packing sync step). Exit count of successes."""
    ctx, inbox_root, skips = _ctx_and_skips()
    n_ok = 0
    for raw in paths:
        f = Path(raw)
        if process_one(f, ctx, inbox_root, skip_batches=skips):
            n_ok += 1
    return n_ok


def watch_loop() -> None:
    ctx, inbox_root, skips = _ctx_and_skips()
    LOG.info("Watching %s (Design Queues auto-run)", inbox_root)
    LOG.info(
        "Testing=%s  Folders: designs=%s single=%s double=%s  dtf_queues=%s",
        getattr(ctx, "use_demo_images", False),
        ctx.designs_folder,
        ctx.single_designs_folder,
        ctx.double_designs_folder,
        getattr(ctx, "dtf_queues_folder", None),
    )
    seen_failed: set[str] = set()
    while True:
        try:
            settings_manager = create_settings_manager()
            settings = settings_manager.saved_settings or {}
            ctx = _build_ctx(settings)
            skips = load_skip_batches(getattr(ctx, "config_workbook_path", None))
            for f in _iter_inbox_files(inbox_root):
                key = str(f.resolve())
                if key in seen_failed:
                    continue
                ok = process_one(f, ctx, inbox_root, skip_batches=skips)
                if not ok and f.exists():
                    pass
                elif not ok:
                    seen_failed.add(key)
        except Exception:
            LOG.exception("Watcher loop error")
        time.sleep(POLL_SECONDS)
