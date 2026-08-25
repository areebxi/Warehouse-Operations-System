import sys
from pathlib import Path

from .config import DEFAULT_OUTPUT_DIR, DEFAULT_WORKBOOK
from .service import run


def main() -> None:
    """
    CLI entrypoint.

    Usage:
        python scripts/split_and_assign_position_codes.py <step3_csv> [workbook_path] [output_dir]
    """
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/split_and_assign_position_codes.py <step3_csv> [workbook_path] [output_dir]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    step3_path = Path(sys.argv[1])
    workbook_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_WORKBOOK
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OUTPUT_DIR

    if not step3_path.exists():
        print(f"Error: Step-3 CSV not found: {step3_path}", file=sys.stderr)
        raise SystemExit(1)

    run(step3_path, workbook_path, output_dir)

