# core/core_api.py

# core/core_api.py

import time
from typing import Any


class CoreAPI:
    """
    public API for mods
    """

    def __init__(self, event_bus, service_registry, mod_storage, log):
        self._event_bus = event_bus
        self._service_registry = service_registry
        self._mod_storage = mod_storage
        self._log = log

    def emit(self, event_name: str, payload: dict = {}, source= "core") -> bool:
        """
emit the event
        """
        if payload is None:
            payload = {}

        event = {
            "name": event_name,
            "source": source,
            "payload": payload,
            "timestamp": int(time.time()),
        }

        return self._event_bus.emit(event)

    def subscribe(self, event_name: str, callback):
        return self._event_bus.subscribe(event_name, callback)

    def register_service(self, name: str, instance: Any) -> bool:
        return self._service_registry.register(name, instance)

    def get_service(self, name: str) -> Any:
        return self._service_registry.get(name)

    def get_mod(self, name: str):
        """
return mod instance. None if don't exist
        """
        return self._mod_storage.instances.get(name)

    def get_manifest(self, name: str):
        """
return mod manifest
        """
        return self._mod_storage.manifests.get(name)

    def get_all_mods(self):
        """
return enable mods
        """
        return [
            m for m, state in self._mod_storage.states.items()
            if state == "enable"
        ]

    def log(self, level: str, message: str):
        self._log(level, message)

    def get_core_version(self) -> str:
        """
return core version
        """
        manifest = self._mod_storage.manifests.get("core_engine")
        if manifest:
            return str(manifest["version"])
        return "0.0.0"

    def get_event_bus(self):
        return self._event_bus

    def get_service_registry(self):
        return self._service_registry
