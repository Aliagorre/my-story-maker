# core/event_bus.py
from typing import Callable

from EVENTS import EVENTS, MOD_ERROR
from LOG_LEVELS import DEBUG, INFO


def is_upper_case(string : str) -> bool :
    if not string :
        return False
    else :
        return all("A" <= x <= "Z" or "0" <= x <= "9" or x == "_"  for x in string)

def is_event_structure(event : dict) -> bool :
    if "name" not in event :
        return False
    elif not is_upper_case(event["name"]) :
        return False
    elif "source" not in event :
        return False
    elif not isinstance(event["source"], str) :
        return False
    elif "payload" not in event :
        return False
    elif not isinstance(event["payload"], dict) :
        return False
    elif "timestamp" not in event :
        return False
    elif not isinstance(event["timestamp"], int) :
        return False
    else :
        return True
class EventBus:
    """
The EventBus is the central communication mechanism between:

the core,
core mods (mods_core),
default mods,
external mods.
    """
    def __init__(self, log:Callable, emit_error:Callable ):
        self._events: dict[str, list[Callable]] = { e : [] for e in EVENTS }
        self.log = log
        self.emit_error= emit_error

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
            self.log(DEBUG, "event not follow the structure")
            return False
        if event["name"] not in self._events :
            self.log(DEBUG, f"{event['name']} : unknown event") 
            return False
        else :
            handlers = self._events[event["name"]]
            for h in handlers:
                try:
                    h(event)
                except Exception as e:
                    self.log(DEBUG, f"{event['name']} : Exception in handler {h.__name__} : {e}")
                    self.emit_error(MOD_ERROR, {"event_name" : event["name"], "handler" : h.__name__, "exception" : e}  ) 
            return True
        
    def subscribe(self, event_name: str, callback: Callable) -> bool :
        """
Subscribes a handler to an event.
Return True in subscribe success
        """
        if event_name not in self._events :
            self.log(DEBUG, f"{event_name} : unknown event")
            return False
        elif not callable(callback) : 
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
        elif not isinstance(callback, Callable) : 
            self.log(DEBUG, "callback must be callable")
            return False
        elif callback not in self._events[event_name] :
            self.log(DEBUG, f"no {callback.__name__} in {event_name}")
            return False
        else :
            self.log(INFO, f"{event_name} : remove callback : {callback.__name__}")
            try :
                self._events[event_name].remove(callback)
                return True
            except Exception as e :
                self.log(INFO, f"{event_name} : remove callback : {callback.__name__}")
                self.emit_error(MOD_ERROR, {"event_name" : event_name, "exception" : e} )
                return False
        