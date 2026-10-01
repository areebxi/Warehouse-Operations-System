from __future__ import annotations
import csv
from pathlib import Path
import sys
from typing import Any, Callable
from pipeline_runtime.runner_utils import (
    _sanitize_process_for_filename,
    _shift_subdir_name,
)
from .client import ShipStationClient, ShipStationError
from .credentials import load_shipstation_credentials
from shared import paths as wh  # noqa: E402

def fetch_tag_orders_to_csv(
    *,
    tag_id: int,
    tag_name: str,
    date_dd_mm_yyyy: str,
    shift_label: str,
    process_number: str,
    input_root: str | Path | None = None,
    client: ShipStationClient | None = None,
    log: LogFn | None = None,
) -> Path:
    """
    Fetch awaiting_shipment orders for tag, write Input/{date}/{shift} Shift/{process}.csv.

    Orders with the ``post-order-designs`` tag are excluded.

    Raises ShipStationError / ValueError / FileNotFoundError on failure.
    Raises ShipStationError if zero line-item rows are produced.
    """
    log_fn = log or (lambda _m: None)
    ss = client or ShipStationClient(load_shipstation_credentials(), log=log_fn)

    # Prefer a full tag map so Tags column includes all order tags (e.g. Prime).
    tag_id_to_name: dict[int, str] = {}
    try:
        for t in ss.list_tags():
            tag_id_to_name[int(t["tagId"])] = str(t.get("name") or "")
    except ShipStationError:
        tag_id_to_name[int(tag_id)] = (tag_name or "").strip()

    if int(tag_id) not in tag_id_to_name and (tag_name or "").strip():
        tag_id_to_name[int(tag_id)] = tag_name.strip()

    display = (tag_name or tag_id_to_name.get(int(tag_id)) or str(tag_id)).strip()
    log_fn(f"Fetching ShipStation orders for tag '{display}' (awaiting_shipment)…")
    orders = ss.list_orders_by_tag(int(tag_id), order_status="awaiting_shipment")
    skipped = sum(
        1 for o in orders if _order_has_excluded_tag(o.get("tagIds"), tag_id_to_name)
    )
    if skipped:
        log_fn(
            f"Skipping {skipped} order(s) tagged '{EXCLUDE_TAG_NAME}'."
        )
    rows = orders_to_rows(orders, tag_id_to_name)
    if not rows:
        raise ShipStationError(
            f"No awaiting-shipment line items found for tag '{display}' "
            f"(after excluding '{EXCLUDE_TAG_NAME}')."
        )

    out_path = input_csv_path_for_batch(
        date_dd_mm_yyyy, shift_label, process_number, input_root=input_root
    )
    write_orders_csv(rows, out_path)
    kept_orders = len(orders) - skipped
    log_fn(
        f"Wrote {len(rows)} row(s) from {kept_orders} order(s) "
        f"({skipped} excluded) to {out_path}"
    )
    return out_path
def input_csv_path_for_batch(
    date_dd_mm_yyyy: str,
    shift_label: str,
    process_number: str,
    *,
    input_root: str | Path | None = None,
) -> Path:
    """Return Input/{date}/{shift} Shift/{process}.csv."""
    root = Path(input_root) if input_root else DEFAULT_INPUT_ROOT
    process = _sanitize_process_for_filename((process_number or "").strip())
    shift_part = _shift_subdir_name((shift_label or "").strip())
    return root / date_dd_mm_yyyy.strip() / shift_part / f"{process}.csv"
