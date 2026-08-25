from __future__ import annotations

from scripts.app.config.load import AppConfig
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.base import Provider
from scripts.app.providers.real.provider import RealProvider


def get_provider(cfg: AppConfig, log: JsonlLogger) -> Provider:
    if cfg.provider_name == "real":
        return RealProvider(cfg, log)
    raise ValueError(f"Unsupported provider: {cfg.provider_name!r}. Expected 'real'.")
