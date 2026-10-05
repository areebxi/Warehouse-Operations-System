"""Skip Batches: digit list from Queue Configuration Workbook + filename parse."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Set

import pandas as pd

from shared import paths as wh

# Sorter: B70-S1 / PB70-S1. Packing: P3570 (no B).
_BATCH_B_RE = re.compile(r"^P?B(\d+)", re.IGNORECASE)
_BATCH_P_RE = re.compile(r"^P(\d+)$", re.IGNORECASE)


def load_skip_batches(workbook_path: Optional[str | Path] = None) -> Set[str]:
    """Return digit strings from Configuration Workbook sheet Skip Batches col A."""
    path = Path(workbook_path) if workbook_path else wh.queue_config_workbook_path()
    if not path.is_file():
        return set()
    try:
        xl = pd.ExcelFile(path)
        if "Skip Batches" not in xl.sheet_names:
            return set()
        df = pd.read_excel(xl, sheet_name="Skip Batches", header=None)
    except Exception:
        return set()
    out: Set[str] = set()
    for val in df.iloc[:, 0].tolist() if len(df.columns) else []:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        text = str(val).strip()
        if not text or text.lower() in ("skip batches", "nan", "none"):
            continue
        if text.upper().startswith("B") and text[1:].isdigit():
            out.add(text[1:])
            continue
        try:
            out.add(str(int(float(text))))
        except (TypeError, ValueError):
            digits = re.sub(r"\D", "", text)
            if digits:
                out.add(str(int(digits)))
    return out


def batch_digits_from_name(name: str) -> Optional[str]:
    """Parse batch digits (PB70-S1 -> 70; P3570 -> 3570)."""
    stem = Path(name).stem
    stem = re.sub(r"^DTF\s*Des-", "", stem, flags=re.IGNORECASE).strip()
    m = _BATCH_B_RE.match(stem) or _BATCH_P_RE.match(stem)
    return m.group(1) if m else None


def should_skip_batch(file_path: Path, skip_batches: Set[str]) -> bool:
    if not skip_batches:
        return False
    digits = batch_digits_from_name(file_path.name)
    return bool(digits and digits in skip_batches)


def output_stem_from_dtf_name(name: str) -> str:
    return re.sub(r"^DTF\s*Des-", "", Path(name).stem, flags=re.IGNORECASE).strip()


def remove_queue_pngs_for_stem(
    stem: str,
    *,
    dtf_queues_folder: Optional[str] = None,
) -> list[Path]:
    """Delete Output + DTF Queues PNGs for a skipped stem (P3570 / P3570_Part N)."""
    removed: list[Path] = []
    if not stem:
        return removed
    out_dir = wh.queue_output_dir() / datetime.now().strftime("%Y-%m-%d")
    folders = [out_dir]
    if dtf_queues_folder:
        folders.append(Path(dtf_queues_folder))
    for folder in folders:
        if not folder.is_dir():
            continue
        for p in list(folder.glob(f"{stem}.png")) + list(folder.glob(f"{stem}_Part *.png")):
            try:
                p.unlink()
                removed.append(p)
            except OSError:
                pass
    return removed
