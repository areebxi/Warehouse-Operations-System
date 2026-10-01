from __future__ import annotations

import asyncio
from pathlib import Path

from app.config.load import AppConfig
from app.flows.print_labels.failures import FailureRow
from app.flows.print_labels.process_group import _run_process_group
from app.flows.print_labels.read_group import GroupedOrders
from app.flows.print_labels.summary_buckets import ProcessGroupResult
from app.logging.jsonl import JsonlLogger
from app.logging.orders_audit import OrderAuditLogger
from app.providers.select_provider import get_provider


async def execute_process_groups(
    *,
    cfg: AppConfig,
    log: JsonlLogger,
    groups: list[GroupedOrders],
    labels_base_dir: Path,
    audit: OrderAuditLogger | None,
) -> tuple[dict[str, ProcessGroupResult], list[FailureRow]]:
    process_results_by_key: dict[str, ProcessGroupResult] = {}
    all_failures: list[FailureRow] = []
    provider = get_provider(cfg, log)
    conc = cfg.raw.get("concurrency") or {}
    max_groups = int(conc.get("max_process_groups", 3))
    group_sem = asyncio.Semaphore(max(1, max_groups))

    async def _run_one_group(g: GroupedOrders) -> ProcessGroupResult:
        async with group_sem:
            return await _run_process_group(
                cfg=cfg,
                log=log,
                provider=provider,
                process_number=g.process_number,
                orders=g.orders,
                labels_base_dir=labels_base_dir,
                audit=audit,
                source_file=g.source_file,
                source_index=g.source_index,
            )

    tasks = [_run_one_group(g) for g in groups]
    try:
        for coro in asyncio.as_completed(tasks):
            try:
                result = await coro
            except Exception as e:
                log.error("print_process_group_failed", exc=e)
                raise
            else:
                key = f"{int(result.source_index)}::{str(result.process_number).strip()}"
                process_results_by_key[key] = result
                all_failures.extend(result.failures)
    finally:
        from app.flows.amendments.shipstation_tags import clear_account_tags_cache

        clear_account_tags_cache()
        aclose = getattr(provider, "aclose", None)
        if callable(aclose):
            await aclose()
    return process_results_by_key, all_failures
