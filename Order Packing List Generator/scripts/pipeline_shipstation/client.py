"""ShipStation V1 API client — re-export shared sync client."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))

from shared.shipstation import (  # noqa: E402
    ShipStationClient,
    ShipStationError,
)

__all__ = ["ShipStationClient", "ShipStationError"]
