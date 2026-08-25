from __future__ import annotations

import argparse
import sys

from scripts.app.config.load import load_config
from scripts.app.flows.convert.run import run_convert
from scripts.app.flows.label_report.run import run_label_report
from scripts.app.flows.print_labels.run import run_manual_print, run_print
from scripts.app.flows.void_labels.run import run_void
from scripts.app.logging.jsonl import JsonlLogger
from scripts.app.util.win_console import configure_windows_console


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shipping-label-app")
    p.add_argument(
        "--config",
        default="shipping_config.yaml",
        help="Path to shipping_config.yaml (default: shipping_config.yaml)",
    )
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("convert", help="Convert Excel/CSV inputs to canonical orders CSV")
    sub.add_parser("print", help="Generate labels + PDFs from canonical orders CSV")
    manual = sub.add_parser("manual-print", help="Generate labels from Manual Print Input/Order Numbers.csv")
    manual_mode = manual.add_mutually_exclusive_group()
    manual_mode.add_argument("--new", action="store_true", help="New manual job (name from process numbers in CSV)")
    manual_mode.add_argument("--replace", metavar="JOB_ID", help="Archive and replace an existing job (e.g. 2000-2400-2450)")
    sub.add_parser("void", help="Void labels listed in void CSV")
    lr = sub.add_parser(
        "label-report",
        help="Report orders printed outside the app (ShipStation-direct) vs printed by this app today",
    )
    lr.add_argument(
        "--date",
        metavar="YYYY-MM-DD",
        help="Report date (default: today)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    configure_windows_console()
    args = _build_parser().parse_args(argv)

    cfg = load_config(args.config)
    log = JsonlLogger.from_config(cfg)

    try:
        if args.command == "convert":
            rc = run_convert(cfg, log)
        elif args.command == "print":
            rc = run_print(cfg, log)
        elif args.command == "manual-print":
            replace_job_id = args.replace
            if not args.new and not args.replace:
                print("Manual Print")
                print("  1) New manual job (name from process numbers in CSV)")
                print("  2) Replace existing job (archive old outputs first)")
                choice = (input("Enter choice (1-2): ") or "").strip()
                if choice == "2":
                    replace_job_id = (input("Enter job id to replace (e.g. 2000-2400-2450): ") or "").strip()
                elif choice != "1":
                    return 2
            rc = run_manual_print(cfg, log, replace_job_id=replace_job_id)
        elif args.command == "void":
            rc = run_void(cfg, log)
        elif args.command == "label-report":
            rc = run_label_report(cfg, log, date_dir=getattr(args, "date", None))
        else:
            rc = 2
    except Exception as e:
        rc = 2

    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

