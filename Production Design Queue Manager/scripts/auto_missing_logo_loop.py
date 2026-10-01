"""Poll / once-run loop for SharedInbox Missing Logo watcher."""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from src.system import create_settings_manager, setup_error_logging
from auto_missing_logo_inbox import (
    LOG,
    POLL_SECONDS,
    WAREHOUSE_ROOT,
    _inbox_root,
    _iter_inbox_files,
    _move_to,
    _wait_stable,
)
from auto_missing_logo_process import _build_ctx, process_missing_logo_file_headless


def process_one(path: Path, ctx: SimpleNamespace, inbox_root: Path) -> bool:
    LOG.info("Processing %s", path)
    try:
        if not _wait_stable(path):
            LOG.warning("File not stable yet, will retry: %s", path)
            return False
        if str(WAREHOUSE_ROOT) not in sys.path:
            sys.path.insert(0, str(WAREHOUSE_ROOT))
        from shared.demo_images import demo_image_lookup

        with demo_image_lookup(getattr(ctx, "use_demo_images", False)):
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
        "Testing=%s  Folders: designs=%s single=%s double=%s",
        getattr(ctx, "use_demo_images", False),
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
    from shared.missing_logo_watcher import claim_this_process

    claim_this_process()
    watch_loop()


if __name__ == "__main__":
    main()
