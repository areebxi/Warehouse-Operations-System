import sys
from pathlib import Path

from .config import DEFAULT_OUTPUT_DIR, DEFAULT_WORKBOOK
from .service import run


def main() -> None:
    """
    CLI entrypoint.

    Usage:
        python scripts/split_by_process_and_item_number.py <step5_csv> [workbook_path] [output_dir]
    """
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/split_by_process_and_item_number.py <step5_csv> [workbook_path] [output_dir]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    step5_path = Path(sys.argv[1])
    workbook_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_WORKBOOK
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_OUTPUT_DIR

    if not step5_path.exists():
        print(f"Error: Step-5 CSV not found: {step5_path}", file=sys.stderr)
        raise SystemExit(1)

    run(step5_path, output_dir, workbook_path)

