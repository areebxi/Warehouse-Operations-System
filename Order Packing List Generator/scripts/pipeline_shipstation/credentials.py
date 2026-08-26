"""Load ShipStation credentials — re-export shared loader."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))

from shared.paths import shipstation_env_path  # noqa: E402
from shared.shipstation.credentials import (  # noqa: E402
    ShipStationCredentials,
    load_shipstation_credentials as _load,
)

DEFAULT_CREDENTIALS_PATH = shipstation_env_path()


def load_shipstation_credentials(
    path: str | Path | None = None,
) -> ShipStationCredentials:
    return _load(path)
