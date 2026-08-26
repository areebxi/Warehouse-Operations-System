from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.app.config.load import load_config
from scripts.app.flows.amendments.run import read_order_numbers_file, run_amendments_check
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.util.win_console import configure_windows_console

# warehouse root on path for shared.paths
_WAREHOUSE = Path(__file__).resolve().parents[4]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="check-amendments",
        description=(
            "Standalone tool: read ShipStation tags for order number(s) and report "
            "whether the Amendments tag is present. Does not print labels."
        ),
    )
    p.add_argument(
        "--config",
        default=str(wh.shipping_yaml_path()),
        help="Path to shipping_config.yaml",
    )
    p.add_argument(
        "--order",
        action="append",
        default=[],
        metavar="ORDER_NUMBER",
        help="Order number to inspect (repeatable)",
    )
    p.add_argument(
        "--orders-file",
        default=None,
        metavar="PATH",
        help="Text/CSV file with one order number per line (first column)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    configure_windows_console()
    args = _build_parser().parse_args(argv)

    order_numbers: list[str] = list(args.order or [])
    if args.orders_file:
        path = Path(str(args.orders_file))
        if not path.exists():
            print(f"Orders file not found: {path}")
            return 2
        order_numbers.extend(read_order_numbers_file(path))

    if not order_numbers:
        print("Provide at least one --order or --orders-file.")
        return 2

    cfg = load_config(args.config)
    log = JsonlLogger.from_config(cfg)
    return run_amendments_check(cfg, log, order_numbers=order_numbers)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
