# core/event_bus.py
from typing import Callable

from event import (
    DEBUG,
    ENGINE_BOOT,
    ENGINE_ERROR,
    ENGINE_FATAL_ERROR,
    ENGINE_INIT,
    ENGINE_READY,
    ENGINE_SHUTDOWN,
    ENGINE_TICK,
    INFO,
    MOD_CONFLICT,
    MOD_DEPENDENCY_ERROR,
    MOD_DISCOVERED,
    MOD_ERROR,
    MOD_INITIALIZED,
    MOD_LOADED,
    MOD_MANIFEST_ERROR,
    event_scheme,
    is_event_structure,
)

""" Event
{
  "name": "ENGINE_READY",
  "source": "core",
  "payload": {},
  "timestamp": 1234567890
}
"""
# No idea what put in payload and timestamp
# rename MOD_ERROR to MOD_ERROR : must update the docs

class EventBus:
    """
The EventBus is the central communication mechanism between:

the core,
core mods (mods_core),
default mods,
external mods.
    """
    def __init__(self):
        self._events: dict[str, list[Callable]] = {
            ENGINE_BOOT  : [],
            ENGINE_INIT  : [],
            ENGINE_READY : [],
            ENGINE_TICK  : [],
            ENGINE_SHUTDOWN : [],
            ENGINE_ERROR    : [],
            ENGINE_FATAL_ERROR : [],
            MOD_DISCOVERED : [],
            MOD_LOADED     : [],
            MOD_INITIALIZED: [],
            MOD_ERROR      : [],
            MOD_MANIFEST_ERROR  : [],
            MOD_DEPENDENCY_ERROR: [],
            MOD_CONFLICT        : [],
        }

    def emit(self, event: dict) -> bool :
        """
The EventBus validates the event structure.

All subscribed handlers are called.

Errors in a handler:
 - are caught,
 - are logged,
 - do not stop propagation.
        """
        if not is_event_structure(event) :
            self.log(DEBUG, "event not follow the structure") # we need only log, no emit Warning
            return False
        if event["name"] not in self._events :
            self.log(DEBUG, f"{event["name"]} : unknown event") # Where are log come from ?
            return False
        else :
            handlers = self._events[event["name"]]
            for h in handlers:
                try:
                    h(event)
                except Exception as e:
                    self.log(DEBUG, f"{event["name"]} : Exception in handler {h.__name__} : {e}")
                    self.emit( event_scheme(MOD_ERROR,"core", {}, 0) ) # No idea what put in payload and timestamp
            return True
        
    def subscribe(self, event_name: str, callback: Callable) -> bool :
        """
Subscribes a handler to an event.
Return True in subscribe success
        """
        if event_name not in self._events :
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        elif not isinstance(callback, Callable) : # Can't be None
            self.log(DEBUG, "callback must be callable")
            return False
        else :
            self.log(INFO, f"{event_name} : new callback : {callback.__name__}")
            self._events[event_name].append(callback)
            return True
        
    def unsubscribe(self, event_name: str, callback: Callable) -> bool:
        """
Unsubscribes a handler from an event.
Return True in unsubscribe success
        """
        if event_name not in self._events :
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        elif not isinstance(callback, Callable) : # Can't be None
            self.log(DEBUG, "callback must be callable")
            return False
        elif callback not in self._events[event_name] :
            self.log(DEBUG, f"no {callback.__name__} in {event_name}")
            return False
        else :
            self.log(INFO, f"{event_name} : remove callback : {callback.__name__}")
            try :
                self._events[event_name].remove(callback)
            except Exception as e :
                self.log(INFO, f"{event_name} : remove callback : {callback.__name__}")
                self.emit( event_scheme(ENGINE_ERROR, "core", {}, 0) ) # No idea what put in payload and timestamp
            return True

# How do Sync/Async mods ?                                                                                  