"""Service registry for managing service instances."""

from typing import Dict, Type, Optional
import logging
from .exceptions import ServiceRegistrationError

logger = logging.getLogger(__name__)

class ServiceRegistry:
    """Dynamic service registry with health monitoring."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.services: Dict[str, object] = {}
            self.health_status: Dict[str, bool] = {}
            self.metrics: Dict[str, Dict] = {}
            self.initialized = True

    def register(self, service_name: str, service_instance: object) -> None:
        """Register a service with the registry."""
        try:
            self.services[service_name] = service_instance
            self.health_status[service_name] = True
            self.metrics[service_name] = {}
            logger.info(f"Registered service: {service_name}")
        except Exception as e:
            raise ServiceRegistrationError(f"Failed to register service {service_name}: {str(e)}")

    def get_service(self, service_name: str) -> Optional[object]:
        """Get a service by name."""
        return self.services.get(service_name)

    def check_health(self) -> Dict[str, bool]:
        """Check health of all registered services."""
        for name, service in self.services.items():
            try:
                health_check = getattr(service, 'health_check', None)
                self.health_status[name] = health_check() if health_check else True
            except Exception as e:
                logger.error(f"Health check failed for {name}: {str(e)}")
                self.health_status[name] = False
        return self.health_status

    def update_metrics(self, service_name: str, metrics: Dict) -> None:
        """Update metrics for a service."""
        if service_name in self.services:
            self.metrics[service_name].update(metrics)
