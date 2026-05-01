# core/core_api.py

import time
from typing import Any


class CoreAPI:
    """Public API exposed to mods.

    Mods receive a CoreAPI instance in every lifecycle hook and must use it
    instead of importing engine internals directly.
    """

    def __init__(self, event_bus, service_registry, mod_storage, log):
        self._event_bus = event_bus
        self._service_registry = service_registry
        self._mod_storage = mod_storage
        self._log = log

    def emit(
        self,
        event_name: str,
        payload: dict | None = None,  # was `dict = {}` — mutable default argument
        source: str = "core",
    ) -> bool:
        """Build and emit a named event on the event bus.

        Returns True when the event was dispatched successfully.
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

    def subscribe(self, event_name: str, callback) -> bool:
        """Subscribe a callback to a named event.

        Returns True on success.
        """
        return self._event_bus.subscribe(event_name, callback)

    def register_service(self, name: str, instance: Any) -> bool:
        """Register a named service in the service registry.

        Returns True when the service was stored successfully.
        """
        return self._service_registry.register(name, instance)

    def get_service(self, name: str) -> Any:
        """Retrieve a registered service by name. Returns None when not found."""
        return self._service_registry.get(name)

    def get_mod(self, name: str) -> Any:
        """Return the live instance of a loaded mod, or None when absent."""
        return self._mod_storage.instances.get(name)

    def get_manifest(self, name: str) -> dict | None:
        """Return the stored manifest dict for a mod, or None when absent."""
        return self._mod_storage.manifests.get(name)

    def get_all_mods(self) -> list[str]:
        """Return the names of all currently enabled mods."""
        return [m for m, state in self._mod_storage.states.items() if state == "enable"]

    def log(self, level: str, message: str) -> None:
        """Forward a log message through the engine's logging callable."""
        self._log(level, message)

    def get_core_version(self) -> str:
        """Return the engine version string from the core_engine manifest.

        Falls back to '7.0.0' when the manifest is unavailable.
        """
        manifest = self._mod_storage.manifests.get("core_engine")
        if manifest:
            return str(manifest["version"])
        return "7.0.0"

    def get_event_bus(self):
        """Return the underlying EventBus instance."""
        return self._event_bus

    def get_service_registry(self):
        """Return the underlying ServiceRegistry instance."""
        return self._service_registry
