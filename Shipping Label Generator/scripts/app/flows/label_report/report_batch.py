from __future__ import annotations

from pathlib import Path

from app.config.load import AppConfig
from app.flows.print_labels.read_group import read_and_group_orders


def _repo_root() -> Path:
    # scripts/app/flows/label_report/ -> repo root
    return Path(__file__).resolve().parents[4]


def _reports_dir(cfg: AppConfig) -> Path:
    paths = cfg.raw.get("paths") or {}
    raw = str(paths.get("reports_dir") or "Reports")
    p = Path(raw)
    if p.is_absolute():
        return p
    return _repo_root() / p


def _orders_csv_path(cfg: AppConfig, date_dir: str) -> Path:
    out_dir = Path(str(cfg.raw["paths"]["output_dir"]))
    p = Path(str(cfg.raw["paths"]["orders_csv"]))
    if p.is_absolute() or len(p.parts) > 1:
        return p
    return out_dir / "Order_Numbers" / date_dir / p


def _batch_orders(cfg: AppConfig, date_dir: str) -> dict[str, tuple[str, str]]:
    """
    order_number -> (process_number, customer_name) from today's converted CSV, if present.
    """
    csv_path = _orders_csv_path(cfg, date_dir)
    if not csv_path.exists():
        return {}
    try:
        groups = read_and_group_orders(csv_path)
    except Exception:
        return {}
    out: dict[str, tuple[str, str]] = {}
    for g in groups:
        for o in g.orders:
            on = str(o.order_number).strip()
            if on:
                out[on] = (str(g.process_number).strip(), str(o.customer_name).strip())
    return out
