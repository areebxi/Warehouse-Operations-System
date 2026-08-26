from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

from scripts.app.config.load import AppConfig
from scripts.app.flows.convert.archive import Manifest, archive_file
from scripts.app.flows.convert.canonicalize import canonicalize_orders
from scripts.app.flows.convert.discover import discover_input_files
from scripts.app.flows.convert.parse_csv import parse_csv_file
from scripts.app.flows.convert.parse_excel import parse_excel_file
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.logging.orders_audit import OrderAuditLogger
from scripts.app.util.hashing import sha256_file
from scripts.app.util.time import local_date_ymd


def _orders_csv_path(cfg: AppConfig) -> Path:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    p = Path(str(cfg.raw["paths"]["orders_csv"]))
    if p.is_absolute() or len(p.parts) > 1:
        return p
    date_dir = out_dir / "Order_Numbers" / local_date_ymd()
    return date_dir / p


_DTF_ID_RE = re.compile(r"(\d+)")


def _dtf_id_from_source_files(source_files: list[Path]) -> str | None:
    if not source_files:
        return None
    if len(source_files) != 1:
        return None
    stem = source_files[0].stem
    matches = _DTF_ID_RE.findall(stem)
    return matches[-1] if matches else None


def _dtf_range_key(source_files: list[Path]) -> str | None:
    """
    If multiple input files are present, build a stable key from every numeric id
    in their stems, e.g. "200-300-400" for three files (not just "200-400").
    Returns None if any id can't be parsed.
    """
    ids: list[int] = []
    for p in source_files:
        stem = p.stem
        matches = _DTF_ID_RE.findall(stem)
        if not matches:
            return None
        try:
            ids.append(int(matches[-1]))
        except Exception:
            return None
    if not ids:
        return None
    ids = sorted(set(ids))
    if len(ids) == 1:
        return str(ids[0])
    return "-".join(str(i) for i in ids)


def _dtf_key_for_manifest(source_files: list[Path]) -> str | None:
    """
    Key used by Print to name the combined PDF:
    - single file: last numeric token in stem (e.g. "200")
    - multiple files: all numeric ids joined (e.g. "200-300-400") when parseable
    """
    if len(source_files) == 1:
        return _dtf_id_from_source_files(source_files)
    return _dtf_range_key(source_files)


def run_convert(cfg: AppConfig, log: JsonlLogger) -> int:
    desfiles_dir = Path(str(cfg.raw["paths"]["desfiles_dir"]))
    import sys
    warehouse = Path(__file__).resolve().parents[4].parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    processed_dir = wh.shipping_desfiles_processed_dir()

    try:
        discovery = discover_input_files(desfiles_dir)
    except FileNotFoundError as e:
        log.error("convert_no_files", extra={"desfiles_dir": str(desfiles_dir)}, exc=e)
        return 2

    # Per-input log folder (e.g. logs/YYYY-MM-DD/200/)
    input_key = discovery.files[0].stem if len(discovery.files) == 1 else "multiple_inputs"
    try:
        if len(discovery.files) == 1:
            dtf = _dtf_id_from_source_files(discovery.files)
            if dtf:
                input_key = dtf
        else:
            rng = _dtf_range_key(discovery.files)
            if rng:
                input_key = rng
    except Exception:
        pass
    log = JsonlLogger.for_input_run(cfg, input_key=input_key, command="convert")
    log.info("run_start", extra={"command": "convert", "input_key": input_key})
    log.info("convert_run_context", extra={"mode": discovery.mode, "files": [p.name for p in discovery.files], "input_key": input_key})

    manifest = Manifest.load(processed_dir)

    dfs: list[pd.DataFrame] = []
    processed_hashes: list[str] = []
    processed_files: list[Path] = []

    for f in discovery.files:
        file_hash: str | None = None
        try:
            file_hash = sha256_file(f)
        except Exception:
            log.warning("convert_hash_failed", extra={"file": str(f)})

        if file_hash and file_hash in manifest.hashes:
            # Skip and attempt delete from desfiles/.
            try:
                f.unlink(missing_ok=True)  # py>=3.8 on windows supports missing_ok
            except Exception:
                pass
            log.info("convert_skipped_duplicate", extra={"file": str(f), "hash": file_hash})
            continue

        if discovery.mode == "csv":
            r = parse_csv_file(f)
            if not r.ok or r.df is None:
                log.warning(
                    "convert_invalid_csv",
                    extra={"file": str(f), "reason": r.reason, "available_columns": r.available_columns},
                )
                continue
            df = r.df.copy()
            df["Source File"] = f.name
            df["Source Index"] = int(len(dfs))
            dfs.append(df)
        else:
            r = parse_excel_file(f)
            if not r.ok or r.df is None:
                log.warning(
                    "convert_invalid_excel",
                    extra={"file": str(f), "reason": r.reason, "available_columns": r.available_columns},
                )
                continue
            df = r.df.copy()
            df["Source File"] = f.name
            df["Source Index"] = int(len(dfs))
            dfs.append(df)

        processed_files.append(f)
        if file_hash:
            processed_hashes.append(file_hash)

    if not dfs:
        log.error("convert_no_valid_inputs", extra={"mode": discovery.mode, "desfiles_dir": str(desfiles_dir)})
        log.info("run_end", extra={"command": "convert", "input_key": input_key, "exit_code": 2})
        return 2

    raw_df = pd.concat(dfs, ignore_index=True)
    out_df = canonicalize_orders(dfs)
    audit = OrderAuditLogger.for_log(log=log, command="convert", run_key=input_key)

    order_col = "orders Numbers"
    proc_col = "Process Number"
    cust_col = "Customer Name" if "Customer Name" in raw_df.columns else None

    if order_col in raw_df.columns:
        raw_orders = raw_df[order_col].astype("string").fillna("").str.strip()
        counts = raw_orders[raw_orders != ""].value_counts()
        for on, cnt in counts.items():
            if int(cnt) > 1:
                audit.record(
                    outcome="convert_deduped",
                    order_number=str(on),
                    duplicate_row_count=int(cnt) - 1,
                )

    for _, row in out_df.iterrows():
        on = str(row.get(order_col, "") or "").strip()
        if not on:
            continue
        fields: dict[str, str] = {
            "process_number": str(row.get(proc_col, "") or "").strip(),
        }
        if cust_col:
            fields["customer_name"] = str(row.get(cust_col, "") or "").strip()
        audit.record(outcome="converted", order_number=on, **fields)

    audit.summary(
        raw_row_count=int(len(raw_df)),
        output_row_count=int(len(out_df)),
        unique_orders=int(len(out_df)),
    )

    out_path = _orders_csv_path(cfg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)

    # Save a small manifest so `print` can name combined PDFs from the DTF source filename.
    try:
        dtf_id = _dtf_key_for_manifest(processed_files)
        manifest_path = out_path.parent / "source_manifest.json"
        manifest_payload = {
            "date": local_date_ymd(),
            "source_files": [p.name for p in processed_files],
            "dtf_id": dtf_id,
        }
        manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        log.warning("convert_manifest_write_failed", extra={"output_dir": str(out_path.parent)}, exc=e)

    # Archive successfully processed inputs and update manifest.
    for f in processed_files:
        try:
            archive_file(src=f, processed_dir=processed_dir)
        except Exception:
            log.warning("convert_archive_failed", extra={"file": str(f), "processed_dir": str(processed_dir)})

    if processed_hashes:
        manifest.hashes.update(processed_hashes)
        manifest.save(processed_dir)

    log.info("convert_done", extra={"rows": int(len(out_df)), "output_csv": str(out_path)})
    log.info("run_end", extra={"command": "convert", "input_key": input_key, "exit_code": 0})
    return 0

