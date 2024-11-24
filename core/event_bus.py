"""Event bus for service communication."""

from typing import Dict, List, Callable, Any
import asyncio
import logging
from .exceptions import EventError

logger = logging.getLogger(__name__)

class EventBus:
    """Event bus implementation for asynchronous event handling."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.subscribers: Dict[str, List[Callable]] = {}
            self.event_history: List[Dict] = []
            self.max_history = 1000
            self.initialized = True

    async def publish(self, event_name: str, data: Any) -> None:
        """Publish an event to all subscribers."""
        if event_name in self.subscribers:
            event_data = {'name': event_name, 'data': data}
            self.event_history.append(event_data)
            
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
            
            for subscriber in self.subscribers[event_name]:
                try:
                    if asyncio.iscoroutinefunction(subscriber):
                        await subscriber(data)
                    else:
                        subscriber(data)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {str(e)}")
                    raise EventError(f"Event handler failed: {str(e)}")

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to an event."""
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(callback)
        logger.debug(f"Added subscriber for event: {event_name}")

    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """Unsubscribe from an event."""
        if event_name in self.subscribers and callback in self.subscribers[event_name]:
            self.subscribers[event_name].remove(callback)
            logger.debug(f"Removed subscriber for event: {event_name}")
