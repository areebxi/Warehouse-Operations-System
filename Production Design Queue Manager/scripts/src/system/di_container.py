"""
Simple Dependency Injection Container for Queue App.

This module provides a lightweight DI container for managing service dependencies,
following the Dependency Inversion Principle (DIP) from SOLID principles.

The container allows:
- Registering service instances or factories
- Resolving dependencies
- Managing service lifetimes (singleton vs transient)
- Easy testing with mock replacements

Note: This is a simple implementation suitable for the current codebase.
For larger applications, consider using a more feature-rich DI library.
"""
from typing import Dict, Any, Callable, Optional, TypeVar, Type
from enum import Enum
from src.system.di_container_impl import DIContainer, ServiceLifetime


T = TypeVar('T')


# Global container instance (optional, can be used as a service locator)
_default_container: Optional[DIContainer] = None


def get_default_container() -> DIContainer:
    """Get the default global DI container instance.
    
    Returns:
        Default DIContainer instance
    
    Note:
        Creates a new instance on first call. This is a simple service locator
        pattern. For better testability, prefer passing container instances
        explicitly rather than using the global container.
    """
    global _default_container
    if _default_container is None:
        _default_container = DIContainer()
    return _default_container


def reset_default_container() -> None:
    """Reset the default global container (useful for testing)."""
    global _default_container
    _default_container = None

