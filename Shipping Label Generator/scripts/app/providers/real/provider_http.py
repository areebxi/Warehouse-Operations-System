from __future__ import annotations

import json
from typing import Any

import aiohttp

from app.providers.real.errors import ProviderHttpError, ProviderParseError, _parse_retry_after_header


class ProviderHttpMixin:
    def _auth(self) -> aiohttp.BasicAuth:
        return aiohttp.BasicAuth(self._api_key, self._api_secret)

    def _provider_cfg(self) -> dict[str, Any]:
        raw = self._cfg.raw.get("provider") or {}
        return raw if isinstance(raw, dict) else {}

    def _http_cfg(self) -> dict[str, Any]:
        raw = self._provider_cfg().get("http") or {}
        return raw if isinstance(raw, dict) else {}

    def _connector(self) -> aiohttp.TCPConnector:
        http = self._http_cfg()
        conc = self._cfg.raw.get("concurrency") or {}
        max_workers = int(conc.get("max_workers", 25))
        limit = int(http.get("pool_limit", min(max_workers, 50)))
        limit_per_host = int(http.get("pool_limit_per_host", min(max_workers, 25)))
        return aiohttp.TCPConnector(
            limit=limit, limit_per_host=limit_per_host, enable_cleanup_closed=True
        )

    def _client_timeout(self) -> aiohttp.ClientTimeout:
        http = self._http_cfg()
        # call_with_retries enforces total request/label timeouts via asyncio.wait_for.
        # These are socket-level bounds to avoid hanging connections.
        sock_connect = float(http.get("sock_connect_timeout_sec", 30))
        sock_read = float(http.get("sock_read_timeout_sec", 60))
        return aiohttp.ClientTimeout(total=None, sock_connect=sock_connect, sock_read=sock_read)

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is not None and not self._session.closed:
            return self._session
        headers = {"Accept": "application/json"}
        self._session = aiohttp.ClientSession(
            auth=self._auth(),
            timeout=self._client_timeout(),
            headers=headers,
            connector=self._connector(),
        )
        return self._session

    async def aclose(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _request_json(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        session = await self._get_session()
        await self._rate_limiter.acquire()
        async with self._req_sem:
            async with session.request(method.upper(), url, params=params, json=json_body) as resp:
                retry_after = None
                if resp.status == 429:
                    retry_after = _parse_retry_after_header(resp.headers.get("Retry-After"))

                text = ""
                try:
                    text = await resp.text()
                except Exception:
                    text = ""

                if resp.status >= 400:
                    msg = (text or f"HTTP {resp.status}")[:2000]
                    raise ProviderHttpError(
                        method=str(method).upper(),
                        url=url,
                        status=int(resp.status),
                        message=msg,
                        retry_after=retry_after,
                    )

                if resp.status == 204:
                    return None
                try:
                    return json.loads(text or "null")
                except Exception as e:
                    snippet = (text or "")[:2000]
                    raise ProviderParseError(
                        method=str(method).upper(),
                        url=url,
                        status=int(resp.status),
                        message="Invalid JSON response",
                        body_snippet=snippet,
                        expected="JSON object",
                    ) from e

    @staticmethod
    def _as_int(v: Any, *, field: str) -> int:
        try:
            return int(v)
        except Exception as e:
            raise ValueError(f"Invalid int for {field}: {v!r}") from e

    @staticmethod
    def _as_str(v: Any) -> str:
        return str(v).strip()

    @staticmethod
    def _get(d: dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d:
                return d.get(k)
        return None
