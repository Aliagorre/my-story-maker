# core/service_registry.py

from typing import Any, Callable

from EVENTS import MOD_ERROR
from LOG_LEVELS import DEBUG, ERROR, INFO


def is_snake_case(string:str) -> bool :
    if not string :
        return False
    else :
        return all("a" <= x <= "z" or "0" <= x <= "9" or x == "_"  for x in string)

class ServiceRegistry :
    """
The ServiceRegistry is a central component of the core.
It allows mods to:

expose reusable services,
access services provided by other mods,
share stable APIs without direct dependencies,
avoid cross-imports between mods.
    """
    def __init__(self, log : Callable, emit_error : Callable) -> None :
        self.service_dict = {} 
        self.log = log 
        self.emit_error = emit_error

    def register(self, name: str, instance: Any) -> bool :
        """
Registers a service.
Return True if service is registered
        """
        if  name in self.service_dict :
            self.log(ERROR, f"service '{name}' already registered") 
            self.emit_error(MOD_ERROR, {"service_name": name, "reason": "duplicate", "expected": "unique"} )
            return False 
        
        elif not is_snake_case(name) :
            self.log(ERROR, f"{name} don't use snake_case convention")    
            self.emit_error(MOD_ERROR, {"service_name": name, "reason": "name_convention", "expected": "snake_case"} )
            return False  
        elif instance is None:
            self.log(ERROR, f"invalid service instance for '{name}'")    
            self.emit_error(MOD_ERROR, {"service_name": name, "reason": "invalid_instance", "expected": "not_NoneType"} ) 
            return False 
        else  :
            self.service_dict[name] = instance
            self.log(INFO, f"registered service '{name}'") 
            return True

    def unregister(self, name) -> bool :
        """
Unregisters a service.
Return True if service is removed.
        """

        if name not in self.service_dict :
            self.log(DEBUG, f"{name} : unknown service")
            return False
        else :
            del self.service_dict[name]
            self.log(INFO, f"Service UNregister : {name}") 
            return True

    def get(self, name: str) -> Any :
        """
Retrieves a service.
        """
        if name not in self.service_dict :
            self.log(DEBUG, f"{name} : service not found")
            return None
        else :
            return self.service_dict[name]
        
    def exists(self, name: str) -> bool :
        """
Checks if a service exists.
        """
        return name in self.service_dict
    
    def list_services(self) -> list[str] :
        """
Returns the list of registered services name.
        """
        return sorted(list(self.service_dict.keys()))
                                                                                                                                                                                                                                                                