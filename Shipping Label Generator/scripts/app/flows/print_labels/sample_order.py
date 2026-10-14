from __future__ import annotations

from pathlib import Path

from scripts.app.flows.print_labels.process_order import OrderResult
from scripts.app.flows.print_labels.sample_pdf import sample_label_pdf_bytes
from scripts.app.logging.jsonl import JsonlLogger


def process_sample_order(
    *,
    log: JsonlLogger,
    process_number: str,
    order_number: str,
    customer_name: str,
    labels_dir: Path,
) -> OrderResult:
    """Write one local SAMPLE page. Does not call ShipStation."""
    labels_dir.mkdir(parents=True, exist_ok=True)
    out_path = labels_dir / f"{order_number}.pdf"
    out_path.write_bytes(
        sample_label_pdf_bytes(
            process_number=process_number,
            order_number=order_number,
            customer_name=customer_name,
        )
    )
    log.info(
        "sample_label_written",
        extra={
            "order_number": order_number,
            "process_number": process_number,
            "label_pdf": str(out_path),
            "sample": True,
        },
    )
    return OrderResult(
        order_number=order_number,
        process_number=process_number,
        label_pdf_path=out_path,
        failure=None,
        ship_from=None,
    )
