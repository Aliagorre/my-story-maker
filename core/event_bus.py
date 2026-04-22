# core/event.py
from typing import Callable, Dict, List

Handler = Callable[..., None]

class EventBus:
    def __init__(self):
        self._events: Dict[str, List[Handler]] = {
            "on_engine_warning": [],
            "on_engine_error":   [],
            "on_engine_log":     [],
        }

    def register_event(self, event_name: str) -> None:
        if event_name not in self._events:
            self._events[event_name] = []

    def emit_error(self, msg: str) -> None:
        handlers = self._events.get("on_engine_error", [])
        if not handlers:
            raise EngineError(msg)          # correct : erreur fatale si personne n'écoute
        for h in handlers:
            try:
                h(msg)
            except Exception as e:
                raise EngineError(f"Error in error-handler: {e}")

    def emit_warning(self, msg: str) -> None:
        handlers = self._events.get("on_engine_warning", [])
        for h in handlers:                  # FIX : silencieux si aucun handler
            try:
                h(msg)
            except Exception as e:
                raise EngineError(f"Error in warning-handler: {e}")

    def emit_log(self, msg: str) -> None:
        handlers = self._events.get("on_engine_log", [])
        for h in handlers:                  # FIX : silencieux si aucun handler
            try:
                h(msg)
            except Exception as e:
                raise EngineError(f"Error in log-handler: {e}")

    def on(self, event_name: str, handler: Handler) -> None:
        if not callable(handler):
            raise EngineError(             # FIX : raise direct, pas via emit_error
                f"Handler for event '{event_name}' must be callable"
            )
        if event_name not in self._events:
            raise EngineError(
                f"Unknown event '{event_name}'. Call register_event() first."
            )
        self._events[event_name].append(handler)

    def emit(self, event_name: str, *args, **kwargs) -> None:
        if event_name not in self._events:
            self.emit_warning(
                f"emit() called with unregistered event '{event_name}'. "
                f"Did you forget to call register_event('{event_name}')?"
            )
            return
        handlers = self._events[event_name]
        if not handlers:
            return
        for h in handlers:
            try:
                h(*args, **kwargs)
            except Exception as e:
                self.emit_error(f"Error in handler for event '{event_name}': {e}")

    def has_event(self, event_name: str) -> bool:
        return event_name in self._events
        