"""RealProvider class shell — methods live in mixin modules."""

from __future__ import annotations

import asyncio
import os

import aiohttp

from app.config.load import AppConfig
from app.logging.jsonl import JsonlLogger
from app.providers.base import Provider
from app.providers.real.provider_impl1_mixin1 import RealProviderMixin1
from app.providers.real.provider_impl1_mixin2 import RealProviderMixin2
from app.providers.real.provider_impl1_mixin3 import RealProviderMixin3
from app.providers.real.provider_impl2 import _local_rate_limiter_from_cfg


class RealProvider(RealProviderMixin1, RealProviderMixin2, RealProviderMixin3, Provider):
    def __init__(self, cfg: AppConfig, log: JsonlLogger) -> None:
        self._cfg = cfg
        self._log = log
        self._base_url = (os.getenv("REAL_API_BASE_URL") or "").strip().rstrip("/")
        self._api_key = (os.getenv("REAL_API_KEY") or "").strip()
        self._api_secret = (os.getenv("REAL_API_SECRET") or "").strip()
        self._session: aiohttp.ClientSession | None = None

        if not self._base_url:
            raise ValueError("REAL_API_BASE_URL is required (e.g. https://ssapi.shipstation.com)")
        if not self._api_key or not self._api_secret:
            raise ValueError("REAL_API_KEY and REAL_API_SECRET are required")

        conc = cfg.raw.get("concurrency") or {}
        self._req_sem = asyncio.Semaphore(int(conc.get("max_workers", 25)))

        rl = cfg.raw.get("rate_limit") or {}
        rl_dict = rl if isinstance(rl, dict) else {}
        self._rate_limiter = _local_rate_limiter_from_cfg(rl=rl_dict, log=log)
