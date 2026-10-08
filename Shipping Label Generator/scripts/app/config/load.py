from __future__ import annotations

import os
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
    # scripts/app/config/load.py -> repo root (Shipping Label App By Tasmia)
    return Path(__file__).resolve().parents[3]


def _resolve_config_path(config_path: str | os.PathLike[str]) -> Path:
    path = Path(config_path)
    if path.is_absolute():
        return path
    cwd_candidate = Path.cwd() / path
    if cwd_candidate.exists():
        return cwd_candidate
    repo_candidate = _repo_root() / path
    if repo_candidate.exists():
        return repo_candidate
    return cwd_candidate


def load_config(config_path: str | os.PathLike[str] = "shipping_config.yaml") -> AppConfig:
    load_dotenv(override=False)

    cfg: dict[str, Any] = default_config_dict()

    path = _resolve_config_path(config_path)
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

    return AppConfig(raw=cfg, provider_name=provider)
