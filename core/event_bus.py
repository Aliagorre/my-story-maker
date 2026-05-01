# core/event_bus.py

import asyncio
from typing import Callable

from core.__pipeline import HandlerPipeline
from resources.__handler import Handler
from resources.EVENTS import EVENTS, MOD_ERROR
from resources.LOG_LEVELS import DEBUG, ERROR, INFO


def _is_upper_case(s: str) -> bool:
    return bool(s) and all("A" <= c <= "Z" or "0" <= c <= "9" or c == "_" for c in s)


def _is_valid_event(event: dict) -> bool:
    return (
        isinstance(event, dict)
        and isinstance(event.get("name"), str)
        and _is_upper_case(event["name"])
        and isinstance(event.get("source"), str)
        and isinstance(event.get("payload"), dict)
        and isinstance(event.get("timestamp"), int)
    )


def _wrap(callback) -> Handler:
    """Auto-wrappe un callable brut pour la rétro-compatibilité."""
    if isinstance(callback, Handler):
        return callback
    if callable(callback):
        return Handler(callback)  # mode="normal", priority=0
    raise TypeError(f"{callback!r} n'est pas callable")


class EventBus:
    """
    Bus de communication central.

    Stockage : liste plate de Handler par event, triée par priorité.
    Chaque emit() construit un HandlerPipeline et l'exécute.
    """

    def __init__(self, log: Callable, emit_error: Callable):
        self._events: dict[str, list[Handler]] = {e: [] for e in EVENTS}
        self.log = log
        self.emit_error = emit_error

    # ------------------------------------------------------------------ emit

    def emit(self, event: dict) -> bool:
        if not _is_valid_event(event):
            self.log(DEBUG, "event invalide ou mal structuré")
            return False
        name = event["name"]
        if name not in self._events:
            self.log(INFO, f"{name} : événement inconnu")
            return False

        pipeline = HandlerPipeline(
            handlers=self._events[name],
            on_error=lambda h, e: self._handler_error(event, h, e),
        )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(pipeline.run(event))
        except RuntimeError:
            pipeline.run_sync(event)

        return True

    # ------------------------------------------------------------ subscribe

    def subscribe(self, event_name: str, callback) -> bool:
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : événement inconnu")
            return False
        try:
            handler = _wrap(callback)
        except TypeError as e:
            self.log(DEBUG, str(e))
            return False

        handlers = self._events[event_name]
        handlers.append(handler)
        handlers.sort(key=lambda h: h.priority, reverse=True)

        self.log(
            INFO,
            f"{event_name} : +{handler.name} [mode={handler.mode}, prio={handler.priority}]",
        )
        return True

    # ---------------------------------------------------------- unsubscribe

    def unsubscribe(self, event_name: str, callback) -> bool:
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : événement inconnu")
            return False
        try:
            handler = _wrap(callback)
        except TypeError:
            return False

        handlers = self._events[event_name]
        # Recherche par identité (même objet) ou par func si auto-wrappé
        target = next(
            (h for h in handlers if h is handler or h.func is handler.func),
            None,
        )
        if target is None:
            self.log(DEBUG, f"{handler.name} non abonné à {event_name}")
            return False

        handlers.remove(target)
        self.log(INFO, f"{event_name} : -{target.name}")
        return True

    # ------------------------------------------------------- register/unregister

    def register(self, event_name: str) -> bool:
        if not _is_upper_case(event_name):
            self.log(DEBUG, f"{event_name} doit être UPPER_CASE")
            return False
        if event_name not in self._events:
            self._events[event_name] = []
        return True

    def unregister(self, event_name: str) -> bool:
        if event_name not in self._events:
            self.log(DEBUG, f"{event_name} : événement inconnu")
            return False
        del self._events[event_name]
        return True

    # --------------------------------------------------------------- internal

    def _handler_error(self, event: dict, handler: Handler, exc: Exception):
        self.log(ERROR, f"{event['name']} : exception dans {handler.name} : {exc}")
        self.emit_error(
            MOD_ERROR,
            {
                "event_name": event["name"],
                "handler": handler.name,
                "exception": str(exc),
            },
        )
