from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from scripts.app.util.win_console import configure_windows_console


def _repo_root() -> Path:
    # scripts/app/launchers/ -> repo root
    return Path(__file__).resolve().parents[3]


def _run(cmd: list[str]) -> int:
    try:
        p = subprocess.run(cmd, check=False, cwd=str(_repo_root()))
        return int(p.returncode)
    except FileNotFoundError:
        return 127


def _python_cmd() -> list[str]:
    return [sys.executable]


def _app_cmd(*args: str) -> list[str]:
    return _python_cmd() + ["-m", "scripts.app.main", *args]


def _pause() -> None:
    try:
        input("\nPress Enter to continue...")
    except EOFError:
        pass


def _print_header() -> None:
    print("=" * 60)
    print("Shipping Label App")
    print("=" * 60)
    print(f"Workspace: {_repo_root()}")
    print(f"Python: {sys.executable}")
    print()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--void", action="store_true", help="Void ALL active shipments for each order in void CSV, then exit.")
    return p


def main() -> int:
    configure_windows_console()
    args, _rest = _build_parser().parse_known_args()
    if args.void:
        return _run(_app_cmd("void"))

    while True:
        _print_header()
        print("Choose an option:")
        print("  1) Convert inputs (DTF Des Files/ -> output/Order_Numbers/YYYY-MM-DD/Order Numbers.csv)")
        print("  2) Print labels (output/Order_Numbers/YYYY-MM-DD/Order Numbers.csv -> dated PDFs)")
        print("  3) Convert + Print (one run)")
        print("  4) Manual Print (Manual Print Input/Order Numbers.csv -> manual outputs)")
        print("  5) Void labels (Void Label Input/void_labels.csv)")
        print("  6) Exit")
        choice = (input("\nEnter choice (1-6): ") or "").strip()

        if choice == "1":
            rc = _run(_app_cmd("convert"))
            print(f"\nConvert finished with exit code {rc}.")
            _pause()
        elif choice == "2":
            rc = _run(_app_cmd("print"))
            print(f"\nPrint finished with exit code {rc}.")
            _pause()
        elif choice == "3":
            rc1 = _run(_app_cmd("convert"))
            if rc1 != 0:
                print(f"\nConvert failed (exit code {rc1}); skipping print.")
                _pause()
                continue
            rc2 = _run(_app_cmd("print"))
            print(f"\nConvert+Print finished with exit codes convert={rc1}, print={rc2}.")
            _pause()
        elif choice == "4":
            rc = _run(_app_cmd("manual-print"))
            print(f"\nManual Print finished with exit code {rc}.")
            _pause()
        elif choice == "5":
            rc = _run(_app_cmd("void"))
            print(f"\nVoid finished with exit code {rc}.")
            _pause()
        elif choice == "6":
            return 0
        else:
            print("\nInvalid choice.")
            _pause()


if __name__ == "__main__":
    raise SystemExit(main())

