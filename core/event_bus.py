# core/event_bus.py
import asyncio
import inspect
from typing import Callable

from resources.__handler import Handler
from resources.EVENTS import EVENTS, MOD_ERROR
from resources.LOG_LEVELS import DEBUG, ERROR, INFO


def is_upper_case(string: str) -> bool:
    return bool(string) and all(
        "A" <= x <= "Z" or "0" <= x <= "9" or x == "_" for x in string
    )


def is_event_structure(event: dict) -> bool:
    return (
        isinstance(event, dict)
        and "name" in event
        and is_upper_case(event["name"])
        and "source" in event
        and isinstance(event["source"], str)
        and "payload" in event
        and isinstance(event["payload"], dict)
        and "timestamp" in event
        and isinstance(event["timestamp"], int)
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
        self._events: dict[str, dict[str, list[Handler]]] = {e: {} for e in EVENTS}
        # { EVENT : {handler_name : [handler_list] }}
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

    def subscribe(self, event_name: str, callback: Handler) -> bool:
        """
        Subscribes a handler to an event.
        Return True in subscribe success
        """
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        name = callback.name
        if not callable(callback):
            self.log(DEBUG, f"callback {name} must be callable")
            return False
        if name not in self._events[event_name]:
            self._events[event_name][name] = []

        # Le plus récent en premier
        self._events[event_name][name].append(callback)
        self._events[event_name][name] = sorted(
            self._events[event_name][name], key=lambda h: h.priority, reverse=True
        )

        self.log(INFO, f"{event_name} : new callback : {name}")
        return True

    def unsubscribe(self, event_name: str, callback: Handler) -> bool:
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        name = callback.name
        if not callable(callback):
            self.log(DEBUG, f"callback '{name}' must be callable")
            return False
        if name not in self._events[event_name]:
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

    def unregister(self, event_name) -> bool:
        """
        Unregister new custom event
        Return True in UNregister success
        """
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        del self._events[event_name]
        return True

    def _emit_sync(self, event: dict) -> bool:
        for name, handlers in self._events[event["name"]].items():
            handlers = sorted(handlers, key=lambda h: h.priority, reverse=True)
            shadow_handlers = [h for h in handlers if getattr(h, "shadow", False)]
            # --- CAS 1 : pas de shadow → comportement actuel ---
            if not shadow_handlers:
                for h in handlers:
                    try:
                        if inspect.iscoroutinefunction(h.func):
                            asyncio.run(h(event))
                        else:
                            h(event)
                    except Exception as e:
                        self._handler_error(event, h, e)
                continue
            # --- CAS 2 : shadow actif → fallback ---
            for h in handlers:
                try:
                    if inspect.iscoroutinefunction(h.func):
                        asyncio.run(h(event))
                    else:
                        h(event)
                    # succès → on stop la chaîne
                    break
                except Exception as e:
                    self._handler_error(event, h, e)
                    # fallback automatique vers le suivant
        return True

    async def _emit_async(self, event: dict) -> bool:
        for name, handlers in self._events[event["name"]].items():
            handlers = sorted(handlers, key=lambda h: h.priority, reverse=True)
            pipeline = self.build_pipeline(handlers)
            await pipeline(event)
        return True

    @staticmethod
    def build_pipeline(handlers):

        async def terminal(event):
            return

        next_fn = terminal

        for h in reversed(handlers):

            def wrap(handler, nxt):

                async def wrapped(event):
                    try:
                        if inspect.iscoroutinefunction(handler.func):
                            await handler.func(event, nxt)
                        else:
                            handler.func(event, nxt)
                    except Exception as e:
                        await nxt(event)

                return wrapped

            next_fn = wrap(h, next_fn)

        return next_fn

    def _handler_error(self, event, handler: Handler, exception):
        self.log(
            ERROR,
            f"{event['name']} : Exception in handler {handler.name} : {exception}",
        )
        self.emit_error(
            MOD_ERROR,
            {
                "event_name": event["name"],
                "handler": handler.name,
                "exception": str(exception),
            },
        )
