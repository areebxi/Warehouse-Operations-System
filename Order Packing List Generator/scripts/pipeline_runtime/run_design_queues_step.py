"""Invoke Queue Design Queues CLI after Packing Excel, before PDFs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, Optional, Sequence

from shared import paths as wh
from pipeline_runtime.runner_utils_paths import _shift_subdir_name

LogFn = Optional[Callable[[str], None]]


def collect_dtf_des_files(output_roots: Iterable[Path]) -> list[Path]:
    """Find DTF Des workbooks under one or more packing output folders."""
    found: list[Path] = []
    seen: set[str] = set()
    for root in output_roots:
        root = Path(root)
        if not root.is_dir():
            continue
        for pattern in ("DTF Des*.xlsx", "DTF Des*.xls"):
            for p in sorted(root.glob(pattern)):
                key = str(p.resolve())
                if key in seen:
                    continue
                seen.add(key)
                found.append(p)
    return found


def prefer_shared_inbox_copies(
    output_files: Sequence[Path],
    *,
    date_dd_mm_yyyy: str,
    shift_label: str,
) -> list[Path]:
    """Prefer SharedInbox copies so --files moves them to Processed (no watcher race)."""
    date_part = (date_dd_mm_yyyy or "").replace("/", "-").strip()
    if not date_part or not output_files:
        return list(output_files)
    inbox_dir = (
        wh.shared_inbox_dtf_des_root()
        / date_part
        / _shift_subdir_name(shift_label)
    )
    preferred: list[Path] = []
    for p in output_files:
        inbox_copy = inbox_dir / p.name
        preferred.append(inbox_copy if inbox_copy.is_file() else p)
    return preferred


def run_design_queues_step(
    dtf_des_paths: Sequence[Path],
    *,
    log: LogFn = None,
) -> int:
    """Subprocess Queue watcher --files; wait. Returns exit code (0 = ok)."""
    paths = [Path(p) for p in dtf_des_paths if Path(p).is_file()]
    if not paths:
        if log:
            log("Design Queues step: no DTF Des files to process")
        return 0

    script = wh.queue_app_dir() / "scripts" / "design_queues_watcher.py"
    if not script.is_file():
        msg = f"Design Queues step: watcher script missing: {script}"
        if log:
            log(msg)
        return 1

    cmd = [sys.executable, str(script), "--files", *[str(p) for p in paths]]
    if log:
        log(f"Design Queues step: starting ({len(paths)} file(s))…")
        for p in paths:
            log(f"  queue: {p.name}")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(script.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as exc:
        if log:
            log(f"Design Queues step: failed to start: {exc}")
        return 1

    if log:
        for line in (proc.stdout or "").splitlines():
            log(f"  [queues] {line}")
        for line in (proc.stderr or "").splitlines():
            log(f"  [queues:err] {line}")
        if proc.returncode == 0:
            log("Design Queues step: done")
        else:
            log(f"Design Queues step: exit {proc.returncode} (PDFs will still run)")
    return int(proc.returncode)


def run_design_queues_for_outputs(
    output_roots: Sequence[Path],
    *,
    make_design_queues: bool,
    log: LogFn = None,
    date_dd_mm_yyyy: str = "",
    shift_label: str = "",
) -> int:
    """Collect DTF Des under outputs and run queues when enabled."""
    if not make_design_queues:
        if log:
            log("Design Queues step: skipped (Make design queues off)")
        return 0
    files = collect_dtf_des_files(output_roots)
    files = prefer_shared_inbox_copies(
        files,
        date_dd_mm_yyyy=date_dd_mm_yyyy,
        shift_label=shift_label,
    )
    return run_design_queues_step(files, log=log)
