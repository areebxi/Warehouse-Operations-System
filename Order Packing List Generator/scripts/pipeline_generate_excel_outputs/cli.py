import re
import sys
from datetime import datetime
from pathlib import Path

from .service import run


def main() -> None:
    """CLI: python scripts/generate_excel_outputs.py <step6_csv> <output_dir> <date_dd_mm_yyyy>"""
    if len(sys.argv) < 4:
        print(
            "Usage: python scripts/generate_excel_outputs.py <step6_csv> <output_dir> <date_dd_mm_yyyy>",
            file=sys.stderr,
        )
        raise SystemExit(1)
    csv_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    date_str = sys.argv[3]
    date_str = date_str.replace("/", "-")
    if not csv_path.exists():
        print(f"Error: CSV not found: {csv_path}", file=sys.stderr)
        raise SystemExit(1)
    try:
        if re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
            dispatch_date = datetime.strptime(date_str, "%d-%m-%Y").date()
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            dispatch_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            raise ValueError(f"Unrecognized date format: {date_str}")
    except ValueError:
        print(f"Error: date must be YYYY-MM-DD or DD-MM-YYYY, got: {date_str}", file=sys.stderr)
        raise SystemExit(1)
    run(csv_path, output_dir, dispatch_date)
    print(f"Wrote Picking, Orders Details, DTF Des -> {output_dir}")

