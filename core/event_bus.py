# core/event_bus.py

from time import time
from typing import Callable, Dict, List


class EventBus:
    """Central message broker. Mods emit and subscribe; the bus just routes."""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def register(self, event_name: str):
        """Declare a new event. Must be called before any subscription is accepted."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []

    def subscribe(self, event_name: str, callback: Callable) -> bool:
        """Attach a callback to an event. Returns False if event is undeclared or callback invalid."""
        if event_name not in self._handlers or not callable(callback):
            return False
        self._handlers[event_name].append(callback)
        return True

    def unsubscribe(self, event_name: str, callback: Callable) -> bool:
        """Detach a callback from an event. Returns False if not found."""
        if event_name not in self._handlers:
            return False
        try:
            self._handlers[event_name].remove(callback)
            return True
        except ValueError:
            return False

    def emit(self, event: dict) -> bool:
        """
        Forward a structured event to all registered handlers.

        Handler exceptions are caught and re-emitted as ERROR_EVENT,
        keeping the bus decoupled from any logging system.
        """
        name = event.get("name")
        if name not in self._handlers:
            return False
        for callback in list(
            self._handlers[name]
        ):  # copy: safe against mid-iteration unsubscribe
            try:
                callback(event)
            except Exception as e:
                self.emit(
                    {
                        "name": "ERROR_EVENT",
                        "payload": {
                            "exception": str(e),
                            "handler": callback.__name__,
                            "source": event.get("source"),
                        },
                        "source": "event_bus",
                        "timestamp": time(),
                    }
                )
        return True
