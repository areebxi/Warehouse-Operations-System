"""ShipStation order helpers for Purchase Order Generator — stable façade."""

from __future__ import annotations

import sys
from pathlib import Path

_WAREHOUSE = Path(__file__).resolve().parents[2]
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))

from shared.shipstation import (  # noqa: E402
    ShipStationClient,
    ShipStationCredentials,
    ShipStationError,
    load_shipstation_credentials,
)
from shipstation_orders_export import export_orders_to_csv, export_orders_to_json  # noqa: E402
from shipstation_orders_impl import ShipStationAPI  # noqa: E402
from shipstation_orders_item import _empty_item_csv_fields, item_fields_for_csv  # noqa: E402

__all__ = [
    "ShipStationAPI",
    "ShipStationClient",
    "ShipStationCredentials",
    "ShipStationError",
    "load_shipstation_credentials",
    "export_orders_to_csv",
    "export_orders_to_json",
    "_empty_item_csv_fields",
    "item_fields_for_csv",
]
