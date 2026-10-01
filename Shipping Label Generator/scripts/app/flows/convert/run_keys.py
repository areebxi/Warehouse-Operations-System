from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from app.config.load import AppConfig
from app.flows.convert.archive import Manifest, archive_file
from app.flows.convert.canonicalize import canonicalize_orders
from app.flows.convert.discover import discover_input_files
from app.flows.convert.parse_csv import parse_csv_file
from app.flows.convert.parse_excel import parse_excel_file
from app.logging.jsonl import JsonlLogger
from app.logging.orders_audit import OrderAuditLogger
from app.util.hashing import sha256_file
from app.util.process_numbers import dtf_id_from_stem, process_number_sort_key
from app.util.time import local_date_ymd
def _orders_csv_path(cfg: AppConfig) -> Path:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    p = Path(str(cfg.raw["paths"]["orders_csv"]))
    if p.is_absolute() or len(p.parts) > 1:
        return p
    date_dir = out_dir / "Order_Numbers" / local_date_ymd()
    return date_dir / p
def _dtf_id_from_source_files(source_files: list[Path]) -> str | None:
    if not source_files or len(source_files) != 1:
        return None
    return dtf_id_from_stem(source_files[0].stem)
def _dtf_range_key(source_files: list[Path]) -> str | None:
    """
    If multiple input files are present, build a stable key from every file id
    in their stems, e.g. "200-300-400" or "B100-S1-B8000-S1".
    Returns None if any id can't be parsed.
    """
    ids: list[str] = []
    for p in source_files:
        key = dtf_id_from_stem(p.stem)
        if not key:
            return None
        ids.append(key)
    if not ids:
        return None
    uniq = sorted(set(ids), key=process_number_sort_key)
    if len(uniq) == 1:
        return uniq[0]
    return "-".join(uniq)
def _dtf_key_for_manifest(source_files: list[Path]) -> str | None:
    """
    Key used by Print to name the combined PDF:
    - single file: batch+shift (`B100-S1`) or legacy last numeric token (`200`)
    - multiple files: all ids joined (e.g. "200-300-400", "B100-S1-B8000-S1")
    """
    if len(source_files) == 1:
        return _dtf_id_from_source_files(source_files)
    return _dtf_range_key(source_files)
