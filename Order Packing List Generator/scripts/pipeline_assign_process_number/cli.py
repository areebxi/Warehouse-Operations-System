import sys
from pathlib import Path

from .config import DEFAULT_OUTPUT_DIR, PROJECT_ROOT
from .service import run


def main() -> None:
    """
    CLI entrypoint.

    Usage:
        python scripts/assign_process_number.py <step4_matched_csv> <shift> [workbook_path] [output_dir]
        python scripts/assign_process_number.py <step4_matched_csv> <shift> [workbook_path] [output_dir] --separate-by-logo-id [--logo-id-threshold N]
        python scripts/assign_process_number.py <step4_matched_csv> <shift> [workbook_path] [output_dir] --fixed-process-number 100A

    shift: 1st, 2nd, 3rd, 4th, or 5th. When both --separate-by-logo-id and --fixed-process-number are set,
    threshold Logo IDs get Design ID lookup (or Logo ID) and the rest get the fixed value. When fixed is selected
    (fixed-only or both), Process Info Sheet is not loaded.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Assign process numbers (step 5)")
    parser.add_argument("step4_csv", type=Path, help="Step-4 matched CSV path")
    parser.add_argument("shift", type=str, help="Shift: 1st, 2nd, 3rd, 4th, 5th")
    parser.add_argument("workbook_path", type=Path, nargs="?", default=__import__('shared.paths', fromlist=['packing_workbook_path']).packing_workbook_path(), help="Workbook path")
    parser.add_argument("output_dir", type=Path, nargs="?", default=DEFAULT_OUTPUT_DIR, help="Output directory")
    parser.add_argument("--separate-by-logo-id", action="store_true", help="Use Logo ID as process number when order count >= threshold")
    parser.add_argument("--logo-id-threshold", type=int, default=5, help="Min units per Logo ID (full-logo orders only) to separate (default: 5)")
    parser.add_argument("--fixed-process-number", type=str, default=None, help="Use this value as Process and Item Number for all rows (overrides normal and Logo ID)")
    args = parser.parse_args()

    if not args.step4_csv.exists():
        print(f"Error: Step-4 CSV not found: {args.step4_csv}", file=sys.stderr)
        raise SystemExit(1)

    fixed = (args.fixed_process_number or "").strip() or None
    run(
        args.step4_csv,
        args.shift,
        args.workbook_path,
        args.output_dir,
        separate_by_logo_id=args.separate_by_logo_id,
        logo_id_threshold=args.logo_id_threshold,
        fixed_process_number=fixed,
    )

