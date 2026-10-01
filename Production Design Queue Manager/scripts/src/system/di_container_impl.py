from __future__ import annotations
from typing import Dict, Any, Callable, Optional, TypeVar, Type
from enum import Enum

class DIContainer:
    """Simple dependency injection container.
    
    Manages service registration and resolution. Supports both singleton
    and transient service lifetimes.
    
    Example:
        >>> container = DIContainer()
        >>> container.register_singleton('settings', SettingsManager)
        >>> settings = container.resolve('settings')
    """
    
    def __init__(self):
        """Initialize the DI container."""
        self._services: Dict[str, Dict[str, Any]] = {}
        self._singleton_instances: Dict[str, Any] = {}
    
    def register_singleton(
        self,
        service_name: str,
        service_class: Type[T] = None,
        instance: T = None,
        factory: Callable[[], T] = None
    ) -> None:
        """Register a service as a singleton.
        
        Args:
            service_name: Name/key for the service
            service_class: Class to instantiate (will be called with no args)
            instance: Pre-created instance to use
            factory: Factory function that returns an instance
            
        Note:
            Only one of service_class, instance, or factory should be provided.
            If instance is provided, it will be used directly.
            If factory is provided, it will be called once and the result cached.
            If service_class is provided, it will be instantiated once.
            
        Example:
            >>> container.register_singleton('settings', SettingsManager)
            >>> # or
            >>> container.register_singleton('settings', instance=SettingsManager())
            >>> # or
            >>> container.register_singleton('settings', factory=lambda: SettingsManager())
        """
        if sum(x is not None for x in [service_class, instance, factory]) != 1:
            raise ValueError("Exactly one of service_class, instance, or factory must be provided")
        
        self._services[service_name] = {
            'lifetime': ServiceLifetime.SINGLETON,
            'class': service_class,
            'instance': instance,
            'factory': factory
        }
        
        # If instance provided, cache it immediately
        if instance is not None:
            self._singleton_instances[service_name] = instance
    
    def register_transient(
        self,
        service_name: str,
        service_class: Type[T] = None,
        factory: Callable[[], T] = None
    ) -> None:
        """Register a service as transient (new instance each time).
        
        Args:
            service_name: Name/key for the service
            service_class: Class to instantiate (will be called with no args)
            factory: Factory function that returns an instance
            
        Note:
            Exactly one of service_class or factory must be provided.
            
        Example:
            >>> container.register_transient('logger', Logger)
            >>> # or
            >>> container.register_transient('logger', factory=lambda: create_logger())
        """
        if sum(x is not None for x in [service_class, factory]) != 1:
            raise ValueError("Exactly one of service_class or factory must be provided")
        
        self._services[service_name] = {
            'lifetime': ServiceLifetime.TRANSIENT,
            'class': service_class,
            'factory': factory
        }
    
    def resolve(self, service_name: str) -> Any:
        """Resolve a service instance.
        
        Args:
            service_name: Name/key of the service to resolve
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If service is not registered
            
        Example:
            >>> settings = container.resolve('settings')
        """
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' is not registered")
        
        service_config = self._services[service_name]
        
        # Singleton: return cached instance or create and cache
        if service_config['lifetime'] == ServiceLifetime.SINGLETON:
            if service_name in self._singleton_instances:
                return self._singleton_instances[service_name]
            
            # Create instance
            instance = self._create_instance(service_config)
            self._singleton_instances[service_name] = instance
            return instance
        
        # Transient: create new instance each time
        return self._create_instance(service_config)
    
    def _create_instance(self, service_config: Dict[str, Any]) -> Any:
        """Create a service instance from configuration.
        
        Args:
            service_config: Service configuration dictionary
            
        Returns:
            Service instance
        """
        if service_config.get('instance') is not None:
            return service_config['instance']
        
        if service_config.get('factory') is not None:
            return service_config['factory']()
        
        if service_config.get('class') is not None:
            return service_config['class']()
        
        raise ValueError("Service configuration must have instance, factory, or class")
    
    def is_registered(self, service_name: str) -> bool:
        """Check if a service is registered.
        
        Args:
            service_name: Name/key of the service
            
        Returns:
            True if service is registered, False otherwise
        """
        return service_name in self._services
    
    def clear(self) -> None:
        """Clear all registered services and singleton instances."""
        self._services.clear()
        self._singleton_instances.clear()
class ServiceLifetime(Enum):
    """Service lifetime options."""
    SINGLETON = "singleton"  # Single instance shared across all requests
    TRANSIENT = "transient"  # New instance created for each request
