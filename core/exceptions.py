"""Custom exceptions for the PR Review Assistant."""

class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass

class ServiceRegistrationError(ServiceError):
    """Raised when service registration fails."""
    pass

class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass

class PluginRegistrationError(PluginError):
    """Raised when plugin registration fails."""
    pass

class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass

class EventError(Exception):
    """Base exception for event-related errors."""
    pass

class DocumentationError(Exception):
    """Base exception for documentation parsing errors."""
    pass
