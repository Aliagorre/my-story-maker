# core/core_api.py

from time import time
from typing import Any, Callable


class CoreAPI:
    """Remote control given to each mod to interact with the engine."""

    def __init__(self, event_bus, mod_storage, mod_name: str):
        self._event_bus = event_bus
        self._mod_storage = mod_storage
        self._mod_name = mod_name

    def emit(self, event_name: str, payload: dict):
        """Dispatch a named event into the engine, tagged with this mod as source."""
        self._event_bus.emit(
            {
                "name": event_name,
                "payload": payload,
                "source": self._mod_name,
                "timestamp": time(),
            }
        )

    def log(self, level: str, message: str, **context):
        """Emit a LOG_EVENT. Shorthand for emit() with a structured log payload."""
        self.emit("LOG_EVENT", {"level": level, "message": message, "context": context})

    def subscribe(self, event_name: str, callback: Callable) -> bool:
        """Register a callback to be called when event_name is emitted."""
        return self._event_bus.subscribe(event_name, callback)

    def get_mod(self, name: str) -> Any:
        """Return the live instance of a mod by name."""
        return self._mod_storage.instances.get(name)

    def get_manifest(self, name: str) -> dict | None:
        """Return the manifest of a mod by name."""
        return self._mod_storage.manifests.get(name)

    def get_all_enabled_mods(self) -> list[str]:
        """Return the names of all currently enabled mods."""
        return [m for m, state in self._mod_storage.states.items() if state == "enable"]

    def get_all_mods(self) -> list[str]:
        """Return the names of all known mods, enabled or not."""
        return list(self._mod_storage.states.keys())

    def get_core_version(self) -> str:
        """Return the version string of the core_engine mod."""
        manifest = self._mod_storage.manifests.get("core_engine")
        return str(manifest["version"]) if manifest else "7.0.0"

    def get_event_bus(self):
        """Return the underlying EventBus."""
        return self._event_bus

    def override(self, path: str, new_value):
        """
        Replace an attribute on a mod or this API by dotted path.

        Example: core.override("mod_dice.exports.roll", my_roll)
        """
        parts = path.split(".")
        obj = self
        for p in parts[:-1]:
            obj = getattr(obj, p)
        setattr(obj, parts[-1], new_value)

    def extend(self, path: str, additions: dict):
        """
        Merge new keys into an existing dict attribute, located by dotted path.

        Example: core.extend("mod_dice.exports", {"adv_roll": fn})
        """
        parts = path.split(".")
        obj = self
        for p in parts:
            obj = getattr(obj, p)
        if not isinstance(obj, dict):
            raise TypeError(f"extend() requires a dict target, got {type(obj)}")
        obj.update(additions)
