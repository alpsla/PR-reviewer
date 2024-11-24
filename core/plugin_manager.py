"""Plugin manager for extensible functionality."""

from typing import Dict, Type, Any, Optional
import importlib.util
import inspect
from pathlib import Path
import logging
from .exceptions import PluginError, PluginRegistrationError

logger = logging.getLogger(__name__)

class PluginManager:
    """Plugin system for extensibility."""
    
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Any] = {}
        self.plugin_configs: Dict[str, Dict] = {}
        self._ensure_plugin_directory()

    def _ensure_plugin_directory(self) -> None:
        """Ensure plugin directory exists."""
        try:
            self.plugin_dir.mkdir(exist_ok=True)
            logger.info(f"Plugin directory ensured at: {self.plugin_dir}")
        except Exception as e:
            logger.error(f"Failed to create plugin directory: {str(e)}")
            raise PluginError(f"Plugin directory creation failed: {str(e)}")

    def load_plugins(self) -> None:
        """Load all plugins from plugin directory."""
        if not self.plugin_dir.exists():
            logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return

        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.stem.startswith("__"):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, str(plugin_file)
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for plugin class
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            hasattr(obj, '_is_plugin') and 
                            obj._is_plugin):
                            self.register_plugin(name, obj)
                            
            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_file.name}: {str(e)}")
                raise PluginError(f"Plugin loading failed: {str(e)}")

    def register_plugin(self, name: str, plugin_class: Type) -> None:
        """Register a new plugin."""
        try:
            plugin_instance = plugin_class()
            self.plugins[name] = plugin_instance
            self.plugin_configs[name] = getattr(plugin_instance, 'config', {})
            logger.info(f"Registered plugin: {name}")
        except Exception as e:
            raise PluginRegistrationError(f"Failed to register plugin {name}: {str(e)}")

    def get_plugin(self, name: str) -> Optional[Any]:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def get_all_plugins(self) -> Dict[str, Any]:
        """Get all registered plugins."""
        return self.plugins.copy()
