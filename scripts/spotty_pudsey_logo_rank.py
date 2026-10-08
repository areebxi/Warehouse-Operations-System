"""Rank logo IDs on 2025 ShipStation orders (spotty/pudsey/children in need).

API itemName is ignored here — page all in-range orders; filter locally.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.shipstation import ShipStationClient, ShipStationError  # noqa: E402

LOGO_RE = re.compile(r"([0-9A-Za-z]+(?:LG|TSU|AV|HK))(?:-[0-9A-Za-z]+|\b)", re.I)
BARE_LG_RE = re.compile(r"\b([0-9A-Za-z]*\d+[0-9A-Za-z]*LG)\b", re.I)
KEYWORDS = ("spotty", "pudsey", "children in need")
DATE_START = "2025-01-01"
DATE_END = "2025-12-31T23:59:59"
# Shipped holds nearly all of last year; others are small leftovers.
STATUSES = (
    "shipped",
    "awaiting_shipment",
    "on_hold",
    "pending_fulfillment",
    "awaiting_payment",
)
CACHE = ROOT / "scripts" / "_cache" / "spotty_pudsey_2025"
OUT = ROOT / "scripts" / "_spotty_pudsey_logo_rank.json"


def _name_hits(name: str) -> bool:
    n = (name or "").casefold()
    return any(k in n for k in KEYWORDS)


def _logos_from_text(text: str) -> set[str]:
    found: set[str] = set()
    for m in LOGO_RE.finditer(text or ""):
        found.add(m.group(1))
    for m in BARE_LG_RE.finditer(text or ""):
        found.add(m.group(1))
    return found


def _meta_path(status: str) -> Path:
    return CACHE / f"{status}.meta.json"


def _page_path(status: str, page: int) -> Path:
    return CACHE / f"{status}_p{page:05d}.json"


def _load_meta(status: str) -> dict:
    p = _meta_path(status)
    if not p.exists():
        return {"next_page": 1, "total_pages": None, "done": False}
    return json.loads(p.read_text(encoding="utf-8"))


def _save_meta(status: str, meta: dict) -> None:
    _meta_path(status).write_text(json.dumps(meta), encoding="utf-8")


def fetch_status(client: ShipStationClient, status: str) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    meta = _load_meta(status)
    if meta.get("done"):
        print(f"[{status}] already cached, skip fetch")
        return
    page = int(meta.get("next_page") or 1)
    total_pages = meta.get("total_pages")
    while True:
        print(
            f"[{status}] page {page}"
            + (f"/{total_pages}" if total_pages else "")
            + "..."
        )
        data = client._get(
            "orders",
            params={
                "orderStatus": status,
                "orderDateStart": DATE_START,
                "orderDateEnd": DATE_END,
                "page": page,
                "pageSize": 500,
                "sortBy": "OrderDate",
                "sortDir": "ASC",
            },
        )
        if not isinstance(data, dict):
            raise ShipStationError("Unexpected orders response.")
        orders = [o for o in (data.get("orders") or []) if isinstance(o, dict)]
        _page_path(status, page).write_text(
            json.dumps(orders), encoding="utf-8"
        )
        try:
            total_pages = int(data.get("pages") or 1)
        except (TypeError, ValueError):
            total_pages = 1
        meta = {"next_page": page + 1, "total_pages": total_pages, "done": False}
        _save_meta(status, meta)
        if page >= total_pages:
            meta["done"] = True
            _save_meta(status, meta)
            print(f"[{status}] done ({total_pages} pages)")
            return
        page += 1
        time.sleep(0.25)


def iter_cached_orders():
    for status in STATUSES:
        meta = _load_meta(status)
        if not meta.get("done"):
            raise RuntimeError(f"Cache incomplete for {status}")
        total = int(meta["total_pages"] or 0)
        for page in range(1, total + 1):
            raw = json.loads(_page_path(status, page).read_text(encoding="utf-8"))
            for o in raw:
                if isinstance(o, dict):
                    yield o


def rank() -> dict:
    by_id: dict[int, dict] = {}
    for o in iter_cached_orders():
        oid = o.get("orderId")
        if isinstance(oid, int):
            by_id[oid] = o

    logo_orders: dict[str, set[int]] = defaultdict(set)
    matched = 0
    no_logo = 0
    for oid, order in by_id.items():
        logos: set[str] = set()
        hit = False
        for it in order.get("items") or []:
            if not isinstance(it, dict):
                continue
            name = str(it.get("name") or "")
            if not _name_hits(name):
                continue
            hit = True
            logos |= _logos_from_text(str(it.get("sku") or ""))
            logos |= _logos_from_text(name)
        if not hit:
            continue
        matched += 1
        if not logos:
            no_logo += 1
            continue
        for logo in logos:
            logo_orders[logo].add(oid)

    ranked = sorted(
        ((lg, len(oids)) for lg, oids in logo_orders.items()),
        key=lambda x: (-x[1], x[0].upper()),
    )
    return {
        "year": 2025,
        "keywords": list(KEYWORDS),
        "orders_scanned": len(by_id),
        "orders_with_matching_item": matched,
        "orders_matching_no_logo": no_logo,
        "unique_logo_ids": len(ranked),
        "ranked": [
            {"rank": i + 1, "logo_id": lg, "orders": n}
            for i, (lg, n) in enumerate(ranked)
        ],
    }


def main() -> int:
    client = ShipStationClient(log=lambda _m: None)
    for status in STATUSES:
        fetch_status(client, status)
    payload = rank()
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("=" * 60)
    print(f"Orders scanned: {payload['orders_scanned']}")
    print(f"Matching item name: {payload['orders_with_matching_item']}")
    print(f"Matching, no logo id: {payload['orders_matching_no_logo']}")
    print(f"Unique logo ids: {payload['unique_logo_ids']}")
    print(f"Wrote {OUT}")
    for row in payload["ranked"][:40]:
        print(f"  {row['rank']:3d}. {row['logo_id']:<24} {row['orders']}")
    if payload["unique_logo_ids"] > 40:
        print(f"  ... {payload['unique_logo_ids'] - 40} more in JSON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
