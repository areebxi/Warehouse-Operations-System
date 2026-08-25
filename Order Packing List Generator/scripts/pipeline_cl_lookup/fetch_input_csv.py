"""
Step 1: Fetch data from ShipStation CSV (Current View).

Reads the CSV, keeps selected columns (with renames), strips whitespace,
and returns a list of dicts. When run as main, also writes to Output/1_fetch_input_csv_{token}.csv.
"""

import csv
import sys
from pathlib import Path

INPUT_COLUMN_ALIASES = [
    ("Order Number", ["Order #", "Order - Number"]),
    ("Ship By", ["Ship By"]),
    ("Item Quantity", ["Quantity", "Item - Qty"]),
    ("Item Image URL", ["Item - Image URL", "Item Image URL"]),
    ("Gift Message", ["Gift - Message", "Gift Message"]),
    ("Item SKU", ["Item SKU", "Item - SKU"]),
    ("Item Name", ["Item Name", "Item - Name"]),
    ("Item Options", ["Item - Options", "Item Options"]),
    ("Recipient Name", ["Recipient", "Ship To - Name"]),
    ("Tags", ["Tags"]),
]

OUTPUT_COLUMNS = [
    "Order Number",
    "Ship By",
    "Item Quantity",
    "Item Image URL",
    "Gift Message",
    "Item SKU",
    "Item Name",
    "Item Options",
    "Recipient Name",
    "Tags",
]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "Output"


def _strip(value: str) -> str:
    if isinstance(value, str):
        return value.strip()
    return value


def fetch_input_csv(csv_path: str | Path, warn_missing_columns: bool = True) -> list[dict]:
    csv_path = Path(csv_path)
    missing_warned = set()

    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            out = {}
            for out_key, candidate_columns in INPUT_COLUMN_ALIASES:
                value = ""
                found_col = None
                for in_col in candidate_columns:
                    if in_col in raw:
                        value = raw[in_col]
                        found_col = in_col
                        break
                if (
                    warn_missing_columns
                    and found_col is None
                    and candidate_columns
                    and candidate_columns[0] not in missing_warned
                ):
                    missing_warned.add(candidate_columns[0])
                    print(
                        f"Warning: column '{candidate_columns[0]}' not found in CSV; using empty string.",
                        file=sys.stderr,
                    )
                out[out_key] = _strip(value)
            item_name = out.get("Item Name", "") or ""
            if "discount" in str(item_name).casefold():
                continue
            rows.append(out)

    return rows


def write_fetched_csv(rows: list[dict], output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "Usage: python scripts/fetch_input_csv.py <input_csv> [output_csv]",
            file=sys.stderr,
        )
        raise SystemExit(1)

    input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
    else:
        token = input_path.stem
        output_path = DEFAULT_OUTPUT_DIR / f"1_fetch_input_csv_{token}.csv"

    rows = fetch_input_csv(input_path)
    write_fetched_csv(rows, output_path)
    print(f"Fetched {len(rows)} rows -> {output_path}")


if __name__ == "__main__":
    main()
