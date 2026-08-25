"""
Service factory for setting up and configuring services with DI container.

This module provides factory functions to configure the DI container with
all necessary services for the Queue App application.
"""
from src.system.di_container import DIContainer
from src.system.settings_manager import SettingsManager
from src.system.interfaces import ISettingsManager


def configure_services(container: DIContainer = None) -> DIContainer:
    """Configure and register all services in the DI container.
    
    Args:
        container: Optional DI container instance. If None, creates a new one.
        
    Returns:
        Configured DI container with all services registered.
        
    Example:
        >>> container = configure_services()
        >>> settings = container.resolve('settings_manager')
    """
    if container is None:
        container = DIContainer()
    
    # Register SettingsManager as singleton
    container.register_singleton(
        'settings_manager',
        service_class=SettingsManager
    )
    
    return container


def create_settings_manager(container: DIContainer = None) -> ISettingsManager:
    """Create or resolve SettingsManager from DI container.
    
    Args:
        container: Optional DI container. If None, configures a default container.
            If provided but services are not configured, configures them first.
        
    Returns:
        ISettingsManager instance (SettingsManager implementation)
        
    Example:
        >>> settings = create_settings_manager()
        >>> settings.load_settings()
    """
    if container is None:
        container = configure_services()
    elif not container.is_registered('settings_manager'):
        # Configure services in provided container if not already configured
        configure_services(container)
    
    return container.resolve('settings_manager')

