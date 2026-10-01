"""Default/global DIContainer locator (lazy import avoids circular façade)."""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .di_container import DIContainer

_default_container: Optional["DIContainer"] = None


def get_default_container() -> "DIContainer":
    """Get the default global DI container instance."""
    global _default_container
    from .di_container import DIContainer

    if _default_container is None:
        _default_container = DIContainer()
    return _default_container


def reset_default_container() -> None:
    """Reset the default global container (useful for testing)."""
    global _default_container
    _default_container = None
