from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from scripts.app.util.time import utc_iso_seconds


@dataclass(frozen=True)
class FailureRow:
    customer_name: str
    process_number: str
    order_number: str
    order_id: str
    reason: str


FAILURES_HEADER = ["Customer Name", "Process Number", "Order Number", "Order ID", "Error Reason"]


def write_failures_csv(path: Path, rows: list[FailureRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(FAILURES_HEADER)
        for r in rows:
            w.writerow([r.customer_name, r.process_number, r.order_number, r.order_id, r.reason])


def append_human_error_log(path: Path, rows: list[FailureRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            f.write(f"Time:{utc_iso_seconds()}\n")
            f.write(f"Order:{r.order_number}\n")
            f.write(f"Customer:{r.customer_name}\n")
            f.write(f"Process:{r.process_number}\n")
            f.write(f"Error:{r.reason}\n\n")

