"""
Load ShipStation Classic V1 credentials from config/ShipStation/.env (REAL_API_*).

Also accepts REAL_API_* already set in the process environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, MutableMapping, Optional

from shared import paths as wh

DEFAULT_BASE_URL = "https://ssapi.shipstation.com"


@dataclass(frozen=True)
class ShipStationCredentials:
    base_url: str
    api_key: str
    api_secret: str


def _parse_key_value_text(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        values[key.strip()] = val.strip().strip('"').strip("'")
    return values


def _parse_key_value_file(path: Path) -> dict[str, str]:
    return _parse_key_value_text(path.read_text(encoding="utf-8"))


def _creds_from_mapping(values: Mapping[str, str]) -> Optional[ShipStationCredentials]:
    base = (values.get("REAL_API_BASE_URL") or "").strip().rstrip("/")
    key = (values.get("REAL_API_KEY") or "").strip()
    secret = (values.get("REAL_API_SECRET") or "").strip()
    if not key or not secret:
        return None
    if not base:
        base = DEFAULT_BASE_URL
    return ShipStationCredentials(base_url=base, api_key=key, api_secret=secret)


def apply_credentials_to_environ(
    creds: ShipStationCredentials,
    *,
    environ: Optional[MutableMapping[str, str]] = None,
    override: bool = False,
) -> None:
    """Export REAL_API_* into environ for Shipping RealProvider and similar."""
    env = environ if environ is not None else os.environ
    mapping = {
        "REAL_API_BASE_URL": creds.base_url,
        "REAL_API_KEY": creds.api_key,
        "REAL_API_SECRET": creds.api_secret,
    }
    for k, v in mapping.items():
        if override or not (env.get(k) or "").strip():
            env[k] = v


def ensure_shipstation_env(
    *,
    from_path: object | None = None,
    override: bool = False,
) -> Optional[ShipStationCredentials]:
    """
    Load config/ShipStation/.env into os.environ when REAL_API_* are missing.

    Returns credentials if found, else None (does not raise).
    """
    existing = _creds_from_mapping(os.environ)
    if existing is not None and not override:
        return existing

    path = wh.shipstation_env_path(from_path)
    if not path.is_file():
        return existing
    try:
        creds = _creds_from_mapping(_parse_key_value_file(path))
    except OSError:
        return existing
    if creds is None:
        return existing
    apply_credentials_to_environ(creds, override=override)
    return creds


def load_shipstation_credentials(
    path: str | Path | None = None,
    *,
    from_path: object | None = None,
) -> ShipStationCredentials:
    """Return credentials or raise FileNotFoundError / ValueError."""
    if path is not None:
        cred_path = Path(path)
        if not cred_path.is_file():
            raise FileNotFoundError(f"ShipStation credentials file not found: {cred_path}")
        creds = _creds_from_mapping(_parse_key_value_file(cred_path))
        if creds is None:
            raise ValueError(f"Missing REAL_API_KEY / REAL_API_SECRET in {cred_path}")
        return creds

    env_creds = _creds_from_mapping(os.environ)
    if env_creds is not None:
        return env_creds

    env_path = wh.shipstation_env_path(from_path)
    if env_path.is_file():
        creds = _creds_from_mapping(_parse_key_value_file(env_path))
        if creds is not None:
            return creds
        raise ValueError(f"Missing REAL_API_KEY / REAL_API_SECRET in {env_path}")

    raise FileNotFoundError(
        "ShipStation credentials not found. Create config/ShipStation/.env "
        "with REAL_API_BASE_URL, REAL_API_KEY, and REAL_API_SECRET."
    )


# ponytail: tiny parse helper for unit tests / dotenv-free callers
def parse_credentials_text(text: str) -> ShipStationCredentials:
    creds = _creds_from_mapping(_parse_key_value_text(text))
    if creds is None:
        raise ValueError("Missing REAL_API_KEY / REAL_API_SECRET in credentials text")
    return creds
