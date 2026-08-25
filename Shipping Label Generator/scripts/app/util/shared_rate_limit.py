from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SharedRateLimitConfig:
    enabled: bool
    state_path: Path
    requests_per_sec: float | None
    fallback_wait_sec: float


def _safe_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except Exception:
        return None


def _lock_file_blocking(fp) -> None:
    """
    Cross-platform advisory lock.

    We only need mutual exclusion among our own processes.
    """
    try:
        fp.seek(0)
    except Exception:
        pass
    if os.name == "nt":
        import msvcrt

        # Lock 1 byte at start of file.
        msvcrt.locking(fp.fileno(), msvcrt.LK_LOCK, 1)
        return
    import fcntl

    fcntl.flock(fp.fileno(), fcntl.LOCK_EX)


def _unlock_file_blocking(fp) -> None:
    try:
        fp.seek(0)
    except Exception:
        pass
    if os.name == "nt":
        import msvcrt

        msvcrt.locking(fp.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(fp.fileno(), fcntl.LOCK_UN)


def _read_state(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_state(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


class SharedRateLimiter:
    """
    Cross-process coordinator for:
    - pacing request starts (requests_per_sec)
    - a shared cooldown window (after 429)

    Implementation:
    - state lives in a small JSON file
    - updates are serialized via a file lock
    - timing is based on epoch seconds (time.time) so it is meaningful across processes
    """

    def __init__(self, cfg: SharedRateLimitConfig) -> None:
        self._cfg = cfg

    @staticmethod
    def from_app_config(*, raw_cfg: dict[str, Any], logs_dir: str | os.PathLike[str]) -> SharedRateLimitConfig:
        rl = raw_cfg.get("rate_limit") or {}
        if not isinstance(rl, dict):
            rl = {}
        enabled = bool(rl.get("shared_across_processes", False))
        state_file = rl.get("state_file") or "rate_limit_state.json"
        state_path = Path(str(logs_dir)) / str(state_file)
        rps = _safe_float(rl.get("requests_per_sec"))
        fallback_wait = float(_safe_float(rl.get("fallback_wait_sec")) or 60.0)
        return SharedRateLimitConfig(
            enabled=enabled,
            state_path=state_path,
            requests_per_sec=rps,
            fallback_wait_sec=fallback_wait,
        )

    async def acquire(self) -> None:
        if not self._cfg.enabled:
            return
        while True:
            delay = await asyncio.to_thread(self._acquire_once_blocking)
            if delay <= 0:
                return
            await asyncio.sleep(delay)

    def enter_cooldown(self, *, retry_after_sec: float | None) -> None:
        if not self._cfg.enabled:
            return
        wait = float(retry_after_sec) if retry_after_sec and retry_after_sec > 0 else float(self._cfg.fallback_wait_sec)
        until = time.time() + max(0.0, wait)
        # Fire-and-forget: this is fast and we don't want to block response handling.
        # Best-effort is fine; the local in-process cooldown still applies.
        try:
            self._set_cooldown_blocking(until_epoch=until)
        except Exception:
            return

    def _ensure_parent_dir(self) -> None:
        try:
            self._cfg.state_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If we can't create the directory, just fall back to in-process limiting.
            raise

    def _acquire_once_blocking(self) -> float:
        """
        Returns required delay in seconds before retrying acquire.
        If 0, the slot is acquired and state updated.
        """
        self._ensure_parent_dir()
        p = self._cfg.state_path
        interval = 0.0
        if self._cfg.requests_per_sec and self._cfg.requests_per_sec > 0:
            interval = 1.0 / float(self._cfg.requests_per_sec)

        # Open state file in r+ if possible, else create.
        with open(p, "a+", encoding="utf-8") as fp:
            _lock_file_blocking(fp)
            try:
                fp.seek(0)
                text = fp.read()
                state = _read_state(text)

                now = float(time.time())
                cooldown_until = float(state.get("cooldown_until_epoch", 0.0) or 0.0)
                next_at = float(state.get("next_at_epoch", 0.0) or 0.0)

                delay_cooldown = max(0.0, cooldown_until - now)
                delay_pacing = max(0.0, next_at - now)
                delay = max(delay_cooldown, delay_pacing)
                if delay > 0.0:
                    return delay

                # Acquire slot: update next_at based on interval.
                if interval > 0.0:
                    state["next_at_epoch"] = now + interval

                fp.seek(0)
                fp.truncate(0)
                fp.write(_write_state(state))
                fp.flush()
                return 0.0
            finally:
                _unlock_file_blocking(fp)

    def _set_cooldown_blocking(self, *, until_epoch: float) -> None:
        self._ensure_parent_dir()
        p = self._cfg.state_path
        with open(p, "a+", encoding="utf-8") as fp:
            _lock_file_blocking(fp)
            try:
                fp.seek(0)
                state = _read_state(fp.read())
                cur = float(state.get("cooldown_until_epoch", 0.0) or 0.0)
                if until_epoch > cur:
                    state["cooldown_until_epoch"] = float(until_epoch)
                fp.seek(0)
                fp.truncate(0)
                fp.write(_write_state(state))
                fp.flush()
            finally:
                _unlock_file_blocking(fp)

