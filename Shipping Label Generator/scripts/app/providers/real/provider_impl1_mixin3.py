from __future__ import annotations
import base64
import os
import asyncio
import json
from dataclasses import dataclass
from time import monotonic
from typing import Any
import aiohttp
from app.config.load import AppConfig
from app.logging.jsonl import JsonlLogger
from app.models.label import Label
from app.models.order import Order
from app.models.shipment import Shipment
from app.providers.base import Provider

class RealProviderMixin3:
    def _as_int(v: Any, *, field: str) -> int:
        try:
            return int(v)
        except Exception as e:
            raise ValueError(f"Invalid int for {field}: {v!r}") from e

    def _get(d: dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d:
                return d.get(k)
        return None

    def _provider_cfg(self) -> dict[str, Any]:
        raw = self._cfg.raw.get("provider") or {}
        return raw if isinstance(raw, dict) else {}

    def _http_cfg(self) -> dict[str, Any]:
        raw = self._provider_cfg().get("http") or {}
        return raw if isinstance(raw, dict) else {}

    async def aclose(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    def _auth(self) -> aiohttp.BasicAuth:
        return aiohttp.BasicAuth(self._api_key, self._api_secret)

    def _as_str(v: Any) -> str:
        return str(v).strip()

    async def void_label(self, shipment_id: int) -> None:
        await self._request_json(method="POST", path="/shipments/voidlabel", json_body={"shipmentId": int(shipment_id)})

