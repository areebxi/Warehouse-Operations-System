from __future__ import annotations

import asyncio
from pathlib import Path

from scripts.app.config.load import AppConfig
from scripts.app.flows.amendments.shipstation_tags import inspect_order_tags, list_account_tags
from scripts.app.flows.amendments.tags import AMENDMENTS_TAG_NAME, amendments_skip_reason
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.real.provider import RealProvider
from scripts.app.providers.select_provider import get_provider


def _print_order_info(info) -> None:
    print(f"Order Number : {info.order_number}")
    print(f"Order ID     : {info.order_id if info.order_id is not None else '(unknown)'}")
    print(f"Customer     : {info.customer_name or '(none)'}")
    print(f"Status       : {info.order_status or '(none)'}")
    print(f"Tag Count    : {info.tag_count}")
    if info.tag_names:
        print("Tags         :")
        for name, tid in zip(info.tag_names, info.tag_ids):
            print(f"  - {name} (id={tid})")
    else:
        print("Tags         : (none)")
    print(f"Has {AMENDMENTS_TAG_NAME}: {'YES' if info.has_amendments else 'NO'}")
    if info.has_amendments:
        print(f"Skip Reason  : {amendments_skip_reason()}")
    print("")


async def _check_orders(*, provider: RealProvider, order_numbers: list[str], log: JsonlLogger) -> int:
    tag_map = await list_account_tags(provider)
    log.info(
        "amendments_account_tags_loaded",
        extra={"tag_count": int(len(tag_map)), "tag_names": sorted(tag_map.values())},
    )

    exit_code = 0
    orders_found = 0
    amendments_count = 0

    for on in order_numbers:
        infos = await inspect_order_tags(provider, on, tag_id_to_name=tag_map)
        if not infos:
            print(f"Order Number : {on}")
            print("Result       : not found in ShipStation")
            print("")
            log.warning("amendments_order_not_found", extra={"order_number": on})
            exit_code = max(exit_code, 1)
            continue

        orders_found += 1
        for info in infos:
            _print_order_info(info)
            log.info(
                "amendments_order_tags",
                extra={
                    "order_number": info.order_number,
                    "order_id": info.order_id,
                    "tag_count": info.tag_count,
                    "tag_ids": list(info.tag_ids),
                    "tag_names": list(info.tag_names),
                    "has_amendments": bool(info.has_amendments),
                },
            )
            if info.has_amendments:
                amendments_count += 1

    log.info(
        "amendments_check_done",
        extra={
            "orders_requested": int(len(order_numbers)),
            "orders_found": int(orders_found),
            "amendments_matches": int(amendments_count),
        },
    )
    return exit_code


def run_amendments_check(
    cfg: AppConfig,
    log: JsonlLogger,
    *,
    order_numbers: list[str],
) -> int:
    """
    Standalone Amendments inspector. Does not print labels or change Print outputs.
    """
    cleaned = [str(o).strip() for o in order_numbers if str(o).strip()]
    if not cleaned:
        print("No order numbers provided.")
        return 2

    provider = get_provider(cfg, log)
    if not isinstance(provider, RealProvider):
        print("Amendments check requires the real ShipStation provider.")
        return 2

    log.info("run_start", extra={"command": "amendments-check", "order_count": int(len(cleaned))})

    async def runner() -> int:
        try:
            return await _check_orders(provider=provider, order_numbers=cleaned, log=log)
        finally:
            aclose = getattr(provider, "aclose", None)
            if callable(aclose):
                await aclose()

    try:
        rc = asyncio.run(runner())
    except Exception as e:
        log.error("amendments_check_failed", exc=e)
        print(f"Amendments check failed: {e}")
        rc = 2

    log.info("run_end", extra={"command": "amendments-check", "exit_code": int(rc)})
    return rc


def read_order_numbers_file(path: Path) -> list[str]:
    """
    Read order numbers from a simple text/CSV-ish file (one order per line).
    Lines may be "order_number" or "order_number,..." — first column is used.
    """
    text = path.read_text(encoding="utf-8")
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        # Skip obvious header rows.
        if s.lower().replace(" ", "") in {"ordernumber", "order-number", "ordersnumbers"}:
            continue
        first = s.split(",")[0].strip().strip('"').strip("'")
        if first and first.lower() not in {"order number", "order - number"}:
            out.append(first)
    return out
