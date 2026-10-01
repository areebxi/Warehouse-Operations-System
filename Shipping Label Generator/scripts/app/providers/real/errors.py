from __future__ import annotations

from dataclasses import dataclass


def _parse_retry_after_header(raw: str | None) -> float | None:
    """
    Parse Retry-After per RFC 7231: delay in seconds, or an HTTP-date after which to retry.
    Returns seconds to wait (>= 0), or None if the header is missing or unparsable.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    try:
        sec = float(s)
        if sec >= 0.0:
            return sec
    except ValueError:
        pass
    try:
        from datetime import datetime, timezone

        from email.utils import parsedate_to_datetime

        dt = parsedate_to_datetime(s)
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0.0, (dt - now).total_seconds())
    except Exception:
        return None


@dataclass(frozen=True)
class ProviderHttpError(RuntimeError):
    method: str
    url: str
    status: int
    message: str
    retry_after: float | None = None

    def __str__(self) -> str:
        return (
            f"ProviderHttpError(method={self.method}, url={self.url}, "
            f"status={self.status}, message={self.message})"
        )


@dataclass(frozen=True)
class ProviderParseError(RuntimeError):
    method: str
    url: str
    status: int
    message: str
    body_snippet: str = ""
    expected: str = ""
    non_retryable: bool = True

    def __str__(self) -> str:
        bits = [f"ProviderParseError(method={self.method}, url={self.url}, status={self.status}"]
        if self.expected:
            bits.append(f"expected={self.expected}")
        bits.append(f"message={self.message})")
        return ", ".join(bits)


@dataclass(frozen=True)
class ProviderNonRetryableError(RuntimeError):
    message: str
    non_retryable: bool = True

    def __str__(self) -> str:
        return self.message
