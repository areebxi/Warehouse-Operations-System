"""Parallel ShipStation addtag helpers for tag_shift_orders."""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from shared.shipstation import ShipStationError

WORKERS = 8
_GATE = threading.Lock()


def pause_seconds(headers, *, floor: int = 1) -> float:
    """Sleep when remaining calls are at or below floor."""
    raw = (headers.get("X-Rate-Limit-Remaining") or "").strip()
    if not raw:
        return 0.0
    try:
        remaining = int(raw)
    except ValueError:
        return 0.0
    if remaining > floor:
        return 0.0
    reset = (headers.get("X-Rate-Limit-Reset") or "").strip()
    try:
        return max(0.5, float(reset))
    except ValueError:
        return 2.0


def add_tag(
    session: requests.Session,
    base: str,
    order_id: int,
    tag_id: int,
    *,
    floor: int = 1,
) -> None:
    url = f"{base.rstrip('/')}/orders/addtag"
    body = {"orderId": int(order_id), "tagId": int(tag_id)}
    last = "addtag failed"
    for _attempt in range(6):
        resp = session.post(url, json=body, timeout=30)
        with _GATE:
            if resp.status_code == 429:
                retry = (resp.headers.get("Retry-After") or "").strip()
                try:
                    wait = float(retry) if retry else 2.0
                except ValueError:
                    wait = 2.0
                time.sleep(min(max(wait, 1.0), 30.0))
                last = "HTTP 429"
                continue
            if not resp.ok:
                raise ShipStationError(
                    f"addtag HTTP {resp.status_code}: {(resp.text or '')[:200]}"
                )
            pause = pause_seconds(resp.headers, floor=floor)
            if pause:
                time.sleep(pause)
            return
    raise ShipStationError(last)


def tag_all(
    *,
    auth: tuple[str, str],
    base_url: str,
    tag_id: int,
    todo: list[tuple[str, int]],
    log=print,
) -> tuple[int, list[str]]:
    """Tag every (order_number, order_id). Returns (ok_count, error lines)."""
    if not todo:
        return 0, []
    errors: list[str] = []
    ok = 0
    total = len(todo)

    def one(number: str, order_id: int) -> str:
        session = requests.Session()
        session.auth = auth
        session.headers.update({"Accept": "application/json"})
        add_tag(session, base_url, order_id, tag_id, floor=WORKERS)
        return number

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(one, number, order_id): number for number, order_id in todo
        }
        for fut in as_completed(futures):
            number = futures[fut]
            try:
                fut.result()
                ok += 1
                log(f"tagged {ok}/{total} {number}")
            except Exception as exc:  # noqa: BLE001 — report every failure
                errors.append(f"{number}: {exc}")
                log(f"failed {number}: {exc}")
    return ok, errors
