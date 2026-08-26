"""Load ShipStation API credentials from config/Packing/API KEY.txt."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_WAREHOUSE = PROJECT_ROOT.parent
if str(_WAREHOUSE) not in sys.path:
    sys.path.insert(0, str(_WAREHOUSE))
from shared import paths as wh  # noqa: E402

DEFAULT_CREDENTIALS_PATH = wh.packing_api_key_path()


@dataclass(frozen=True)
class ShipStationCredentials:
    base_url: str
    api_key: str
    api_secret: str


def load_shipstation_credentials(
    path: str | Path | None = None,
) -> ShipStationCredentials:
    """Parse KEY=value lines from API KEY.txt (REAL_API_* keys)."""
    cred_path = Path(path) if path else DEFAULT_CREDENTIALS_PATH
    if not cred_path.is_file():
        raise FileNotFoundError(f"ShipStation credentials file not found: {cred_path}")

    values: dict[str, str] = {}
    for raw in cred_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip()

    base_url = (values.get("REAL_API_BASE_URL") or "").rstrip("/")
    api_key = values.get("REAL_API_KEY") or ""
    api_secret = values.get("REAL_API_SECRET") or ""
    missing = [
        name
        for name, val in (
            ("REAL_API_BASE_URL", base_url),
            ("REAL_API_KEY", api_key),
            ("REAL_API_SECRET", api_secret),
        )
        if not val
    ]
    if missing:
        raise ValueError(
            f"Missing or empty keys in {cred_path.name}: {', '.join(missing)}"
        )
    return ShipStationCredentials(base_url=base_url, api_key=api_key, api_secret=api_secret)
