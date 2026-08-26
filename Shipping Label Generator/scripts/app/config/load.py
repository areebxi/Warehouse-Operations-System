from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from scripts.app.config.defaults import default_config_dict


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _coerce_int(val: Any, *, name: str) -> int:
    try:
        return int(str(val).strip())
    except Exception as e:
        raise ValueError(f"Invalid int for {name}: {val!r}") from e


@dataclass(frozen=True)
class AppConfig:
    raw: dict[str, Any]
    provider_name: str


def _repo_root() -> Path:
    # scripts/app/config/load.py -> Shipping Label Generator app root
    return Path(__file__).resolve().parents[3]


def _warehouse_paths():
    warehouse = _repo_root().parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    return wh


def _resolve_config_path(config_path: str | os.PathLike[str]) -> Path:
    path = Path(config_path)
    if path.is_absolute():
        return path
    wh = _warehouse_paths()
    cfg_candidate = wh.shipping_config_dir() / path.name
    if cfg_candidate.exists():
        return cfg_candidate
    cwd_candidate = Path.cwd() / path
    if cwd_candidate.exists():
        return cwd_candidate
    repo_candidate = _repo_root() / path
    if repo_candidate.exists():
        return repo_candidate
    return cfg_candidate


def _absolutize_shipping_paths(cfg: dict[str, Any]) -> dict[str, Any]:
    """Resolve relative path values against Runtime/Shipping."""
    wh = _warehouse_paths()
    base = wh.shipping_runtime_dir()
    paths = dict(cfg.get("paths") or {})
    for key in ("output_dir", "logs_dir", "reports_dir", "desfiles_dir"):
        val = paths.get(key)
        if not val:
            continue
        p = Path(str(val))
        if not p.is_absolute():
            paths[key] = str((base / p).resolve())
    # orders_csv / void_csv may be relative to runtime
    for key in ("orders_csv", "void_csv"):
        val = paths.get(key)
        if not val:
            continue
        p = Path(str(val))
        if not p.is_absolute():
            paths[key] = str((base / p).resolve())
    cfg = dict(cfg)
    cfg["paths"] = paths
    manual = dict(cfg.get("manual_print") or {})
    if manual.get("input_csv"):
        p = Path(str(manual["input_csv"]))
        if not p.is_absolute():
            manual["input_csv"] = str((base / p).resolve())
        cfg["manual_print"] = manual
    return cfg


def load_config(config_path: str | os.PathLike[str] | None = None) -> AppConfig:
    wh = _warehouse_paths()
    warehouse = _repo_root().parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared.shipstation.credentials import ensure_shipstation_env

    ensure_shipstation_env()
    load_dotenv(wh.shipstation_env_path(), override=False)
    # App-only overrides (provider, concurrency notes) — not ShipStation API keys
    load_dotenv(wh.shipping_env_path(), override=False)
    load_dotenv(override=False)

    cfg: dict[str, Any] = default_config_dict()

    path = _resolve_config_path(config_path or wh.shipping_yaml_path())
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("shipping_config.yaml must contain a YAML mapping at top level")
        cfg = _deep_merge(cfg, data)

    if os.getenv("MAX_CONCURRENCY"):
        cfg = _deep_merge(cfg, {"concurrency": {"max_workers": _coerce_int(os.getenv("MAX_CONCURRENCY"), name="MAX_CONCURRENCY")}})
    if os.getenv("BATCH_NOTES"):
        cfg = _deep_merge(cfg, {"batch": {"notes": os.getenv("BATCH_NOTES")}})
    if os.getenv("PROCESSED_BY"):
        cfg = _deep_merge(cfg, {"batch": {"processed_by": os.getenv("PROCESSED_BY")}})
    if os.getenv("SHIP_FROM"):
        cfg = _deep_merge(cfg, {"batch": {"ship_from": os.getenv("SHIP_FROM")}})

    provider = (os.getenv("SHIPPING_PROVIDER") or "real").strip().lower()
    if provider != "real":
        raise ValueError("SHIPPING_PROVIDER must be 'real'")

    if "paths" not in cfg or not isinstance(cfg["paths"], dict):
        raise ValueError("config missing 'paths' mapping")
    if "logging" not in cfg or not isinstance(cfg["logging"], dict):
        raise ValueError("config missing 'logging' mapping")
    if "concurrency" not in cfg or not isinstance(cfg["concurrency"], dict):
        raise ValueError("config missing 'concurrency' mapping")

    cfg = _absolutize_shipping_paths(cfg)
    return AppConfig(raw=cfg, provider_name=provider)
