import argparse
import sys
from pathlib import Path

from .core import ALL_ORDERS_PATH, DEFAULT_MISSING_INPUT, PROJECT_ROOT, run_missing_run_from_all_orders
from .gui import launch_gui


def main() -> None:
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Run a missing pipeline subset using Data/All Orders.csv and Missing/Missing Input.csv.")
        parser.add_argument("date", help="Dispatch date DD-MM-YYYY.")
        parser.add_argument("process_name", help="Name for this missing run.")
        parser.add_argument("--shift", default=None, help="Shift label (e.g. '1st').")
        parser.add_argument("--missing-input", type=Path, default=DEFAULT_MISSING_INPUT, help="Path to Missing/Missing Input.csv.")
        parser.add_argument("--all-orders", type=Path, default=ALL_ORDERS_PATH, help="Path to Data/All Orders.csv.")
        args = parser.parse_args()

        def _log(msg: str) -> None:
            print(msg, file=sys.stderr)

        try:
            output_root = run_missing_run_from_all_orders(
                missing_input_path=args.missing_input,
                all_orders_path=args.all_orders,
                process_name=args.process_name,
                date_dd_mm_yyyy=args.date,
                shift=args.shift,
                output_dir=PROJECT_ROOT / "Output",
                log=_log,
            )
        except Exception as exc:
            _log(f"Error: {exc}")
            raise SystemExit(1)
        print(f"Missing run outputs written to: {output_root}")
        return

    launch_gui()
