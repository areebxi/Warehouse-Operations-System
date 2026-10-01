from __future__ import annotations

from app.config.load import AppConfig
from app.logging.jsonl import JsonlLogger
from app.providers.base import Provider
from app.providers.real.provider import RealProvider


def get_provider(cfg: AppConfig, log: JsonlLogger) -> Provider:
    if cfg.provider_name == "real":
        return RealProvider(cfg, log)
    raise ValueError(f"Unsupported provider: {cfg.provider_name!r}. Expected 'real'.")
