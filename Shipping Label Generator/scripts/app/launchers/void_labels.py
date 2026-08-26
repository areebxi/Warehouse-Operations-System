from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from scripts.app.config.load import load_config
from scripts.app.flows.void_labels.read_void_list import read_void_order_numbers
from scripts.app.flows.void_labels.void_shipments import VoidResult, void_for_order
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.providers.select_provider import get_provider


def _repo_root() -> Path:
    # scripts/app/launchers/ -> repo root
    return Path(__file__).resolve().parents[3]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="void-labels")
    warehouse = _repo_root().parent
    import sys
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    p.add_argument(
        "--config",
        default=str(wh.shipping_yaml_path()),
        help="Path to shipping_config.yaml",
    )
    p.add_argument(
        "--void-csv",
        default=None,
        help="Override void CSV path (default: config paths.void_csv)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    cfg = load_config(args.config)
    log = JsonlLogger.from_config(cfg)

    void_csv = Path(args.void_csv) if args.void_csv else Path(str(cfg.raw["paths"]["void_csv"]))
    try:
        order_numbers = read_void_order_numbers(void_csv)
    except FileNotFoundError as e:
        log.error("void_missing_csv", extra={"void_csv": str(void_csv)}, exc=e)
        return 2

    if not order_numbers:
        log.error("void_no_orders", extra={"void_csv": str(void_csv)})
        return 2

    provider = get_provider(cfg, log)

    async def runner() -> list[VoidResult]:
        sem = asyncio.Semaphore(int(cfg.raw["concurrency"]["max_workers"]))

        async def _wrap(o: str) -> VoidResult:
            async with sem:
                return await void_for_order(
                    cfg=cfg,
                    provider=provider,
                    log=log,
                    order_number=o,
                    max_shipments_per_order=1,
                )

        return await asyncio.gather(*[_wrap(o) for o in order_numbers])

    results = asyncio.run(runner())
    summary = {
        "orders": len(results),
        "attempted": sum(r.attempted for r in results),
        "voided": sum(r.voided for r in results),
        "not_voided": sum(1 for r in results if r.voided == 0),
        "mode": "one_shipment_per_order",
    }
    log.info("void_done", extra=summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

