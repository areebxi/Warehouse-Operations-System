from __future__ import annotations

import asyncio
from pathlib import Path

from scripts.app.config.load import AppConfig
from scripts.app.flows.void_labels.read_void_list import read_void_order_numbers
from scripts.app.flows.void_labels.void_shipments import VoidResult, void_for_order
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.logging.orders_audit import OrderAuditLogger
from scripts.app.providers.select_provider import get_provider


def _void_csv_path(cfg: AppConfig) -> Path:
    p = Path(str(cfg.raw["paths"]["void_csv"]))
    return p


def run_void(cfg: AppConfig, log: JsonlLogger) -> int:
    void_csv = _void_csv_path(cfg)
    try:
        order_numbers = read_void_order_numbers(void_csv)
    except FileNotFoundError as e:
        log.error("void_missing_csv", extra={"void_csv": str(void_csv)}, exc=e)
        return 2

    if not order_numbers:
        log.error("void_no_orders", extra={"void_csv": str(void_csv)})
        return 2

    input_key = Path(str(void_csv)).stem
    log = JsonlLogger.for_input_run(cfg, input_key=input_key, command="void")
    log.info("run_start", extra={"command": "void", "input_key": input_key})
    log.info("void_run_context", extra={"void_csv": str(void_csv), "orders": len(order_numbers), "input_key": input_key})

    audit = OrderAuditLogger.for_log(log=log, command="void", run_key=input_key)

    async def runner() -> list[VoidResult]:
        provider = get_provider(cfg, log)
        sem = asyncio.Semaphore(int(cfg.raw["concurrency"]["max_workers"]))

        async def _wrap(o: str) -> VoidResult:
            async with sem:
                return await void_for_order(cfg=cfg, provider=provider, log=log, order_number=o, max_shipments_per_order=None, audit=audit)

        try:
            return await asyncio.gather(*[_wrap(o) for o in order_numbers])
        finally:
            aclose = getattr(provider, "aclose", None)
            if callable(aclose):
                await aclose()

    results = asyncio.run(runner())

    summary = {
        "orders": len(results),
        "attempted": sum(r.attempted for r in results),
        "voided": sum(r.voided for r in results),
        "not_voided": sum(1 for r in results if r.voided == 0),
    }
    log.info("void_done", extra=summary)
    audit.summary(
        orders=int(summary["orders"]),
        attempted=int(summary["attempted"]),
        voided=int(summary["voided"]),
        not_voided=int(summary["not_voided"]),
    )
    log.info("run_end", extra={"command": "void", "input_key": input_key, "exit_code": 0})
    return 0

