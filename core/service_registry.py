# core/service_registry.py

from typing import Any


def is_snake_case(string:str) -> bool :
    if not string :
        return False
    else :
        return all(x in "aeiouy_bcdfghjklmnopqrstuvwxz" for x in string)

class ServiceRegistry :
    """
The ServiceRegistry is a central component of the core.
It allows mods to:

expose reusable services,
access services provided by other mods,
share stable APIs without direct dependencies,
avoid cross-imports between mods.
    """
    def __init__(self, core_api : Any) -> None :
        self.service_dict = {"core_api" : core_api} # I don't know for the name

    def register(self, name: str, instance: Any) -> None :
        """
Registers a service.
        """
        if ( name in self.service_dict 
        or not is_snake_case(name) 
        or instance is None ):
            self.service_dict["core_api"]["log"](ERROR) # we don't need EventBus for it ?
            self.service_dict["core_api"]["emit"](MOD_ERROR) # are they other wayn?
        else  :
            self.service_dict[name] = instance
            self.service_dict["core_api"]["log"](INFO)
            self.service_dict["core_api"]["emit"](MOD_REGISTER) # I think we don't need this

    def get(self, name: str) -> Any :
        """
Retrieves a service.
        """
        if name not in self.service_dict :
            self.service_dict["core_api"]["log"](WARNING)
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
Returns the list of registered services.
        """
        return sorted(list(self.service_dict.keys())) # After we should sort by loading order I think.
        