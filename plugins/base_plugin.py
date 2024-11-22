"""Base plugin interface for the PR Review Assistant."""

from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePlugin(ABC):
    """Abstract base class for plugins."""
    
    _is_plugin = True  # Class marker for plugin detection
    
    @abstractmethod
    def initialize(self) -> None:
        """Initialize plugin resources."""
        pass
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin functionality."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get plugin name."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Get plugin version."""
        pass
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return {}
