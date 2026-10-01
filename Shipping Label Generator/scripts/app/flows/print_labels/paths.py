from __future__ import annotations

import json
import re
from pathlib import Path

from app.config.load import AppConfig
from app.util.time import local_date_ymd

_PROCESS_PDF_RE = re.compile(r"process_(\d+)", re.IGNORECASE)

def _orders_csv_path(cfg: AppConfig) -> Path:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    p = Path(str(cfg.raw["paths"]["orders_csv"]))
    if p.is_absolute() or len(p.parts) > 1:
        return p
    date_dir = out_dir / "Order_Numbers" / local_date_ymd()
    return date_dir / p

def _path_from_repo(value: str | Path) -> Path:
    p = Path(str(value))
    if p.is_absolute():
        return p
    return _repo_root() / p

def _combined_pdf_name_from_orders_dir(orders_dir: Path) -> str:
    """
    Prefer DTF id from convert's manifest (e.g. 3000 -> "3000.pdf").
    """
    manifest_path = orders_dir / "source_manifest.json"
    if not manifest_path.exists():
        return "combined"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8") or "{}")
    except Exception:
        return "combined"
    dtf_id = data.get("dtf_id")
    if isinstance(dtf_id, str) and dtf_id.strip():
        return dtf_id.strip()
    return "combined"

def _combined_pdf_name_for_run(*, orders_csv: Path, combined_name_override: str | None) -> str:
    if combined_name_override is not None and str(combined_name_override).strip():
        return str(combined_name_override).strip()
    return _combined_pdf_name_from_orders_dir(orders_csv.parent)

def _repo_root() -> Path:
    # scripts/app/flows/print_labels/ -> repo root
    return Path(__file__).resolve().parents[4]

def _process_number_key_from_pdf_path(p: Path) -> int:
    """
    Extract numeric process number from filenames like `process_2.pdf`.

    If parsing fails, return a large key so unknown names sort last.
    """
    m = _PROCESS_PDF_RE.search(p.stem)
    if not m:
        return 1_000_000_000
    try:
        return int(m.group(1))
    except Exception:
        return 1_000_000_000

