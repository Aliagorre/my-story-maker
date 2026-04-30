# core/event_bus.py
import asyncio
import inspect
from typing import Callable

from EVENTS import EVENTS, MOD_ERROR
from LOG_LEVELS import DEBUG, ERROR, INFO


def is_upper_case(string: str) -> bool:
    return bool(string) and all("A" <= x <= "Z" or "0" <= x <= "9" or x == "_" for x in string)

def is_event_structure(event: dict) -> bool:
    return (
        isinstance(event, dict)
        and "name" in event and is_upper_case(event["name"])
        and "source" in event and isinstance(event["source"], str)
        and "payload" in event and isinstance(event["payload"], dict)
        and "timestamp" in event and isinstance(event["timestamp"], int)
    )

class EventBus:
    """
The EventBus is the central communication mechanism between:

the core,
core mods (mods_core),
default mods,
external mods.
    """
    def __init__(self, log: Callable, emit_error: Callable):
        self._events: dict[str, dict[str, list[Callable]]] = {e: {} for e in EVENTS}
        self.log = log
        self.emit_error = emit_error

    def emit(self, event: dict) -> bool:
        if not is_event_structure(event):
            self.log(DEBUG, "event does not follow structure")
            return False
        if event["name"] not in self._events:
            self.log(INFO, f"{event['name']} : unknown event")
            return False
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._emit_async(event))
            return True
        except RuntimeError:
            return self._emit_sync(event)

    def subscribe(self, event_name: str, callback: Callable) -> bool:
        """
Subscribes a handler to an event.
Return True in subscribe success
        """
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        name = callback.__name__
        if not callable(callback):
            self.log(DEBUG, f"callback {name} must be callable")
            return False

        if name not in self._events[event_name]:
            self._events[event_name][name] = []

        # Le plus récent en premier
        self._events[event_name][name].insert(0, callback)

        self.log(INFO, f"{event_name} : new callback : {name}")
        return True

    def unsubscribe(self, event_name: str, callback: Callable) -> bool:
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        name = callback.__name__
        if not callable(callback):
            self.log(DEBUG, f"callback '{name}' must be callable")
            return False
        if name not in self._events[event_name] :
            self.log(DEBUG, f"{name} not in {event_name}")
            return False
        if callback not in self._events[event_name][name]:
            self.log(DEBUG, f"callback not in '{name}'")
            return False

        self._events[event_name][name].remove(callback)
        self.log(INFO, f"{event_name} : remove callback : {name}")
        return True


    def register(self, event_name: str) -> bool:
        """
Register new custom event 
Return True in register success
        """
        if not is_upper_case(event_name):
            self.log(DEBUG, f"{event_name} must be UPPER_CASE")
            return False
        if event_name in self._events:
            return True
        self._events[event_name] = {}
        return True

    def unregister(self, event_name) -> bool :
        """
Unregister new custom event 
Return True in UNregister success
        """
        if event_name not in self._events :
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        del self._events[event_name]
        return True

    def _emit_sync(self, event: dict) -> bool:
        for handler in self._events[event["name"]]:
            try:
                if inspect.iscoroutinefunction(handler):
                    asyncio.run(handler(event))
                else:
                    handler(event)
            except Exception as e:
                self._handler_error(event, handler, e)
        return True

    async def _emit_async(self, event: dict) -> bool:
        sync_handlers = []
        async_handlers = []
        for h in self._events[event["name"]]:
            if inspect.iscoroutinefunction(h):
                async_handlers.append(h)
            else:
                sync_handlers.append(h)
        for h in sync_handlers:
            try:
                h(event)
            except Exception as e:
                self._handler_error(event, h, e)
        for h in async_handlers:
            try:
                await h(event)
            except Exception as e:
                self._handler_error(event, h, e)
        return True

    def _handler_error(self, event, handler, exception):
        self.log(ERROR, f"{event['name']} : Exception in handler {handler.__name__} : {exception}")
        self.emit_error(
            MOD_ERROR,
            {
                "event_name": event["name"],
                "handler": handler.__name__,
                "exception": str(exception),
            }
        )
     