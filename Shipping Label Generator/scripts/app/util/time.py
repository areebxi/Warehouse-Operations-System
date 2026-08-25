from __future__ import annotations

from datetime import datetime, timezone


def utc_iso_seconds() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def utc_compact_timestamp() -> str:
    # YYYYMMDD_HHMMSS (UTC)
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def local_date_ymd() -> str:
    # YYYY-MM-DD (local)
    return datetime.now().strftime("%Y-%m-%d")


def local_compact_timestamp() -> str:
    # YYYYMMDD_HHMMSS (local) — used for unique report filenames
    return datetime.now().strftime("%Y%m%d_%H%M%S")

