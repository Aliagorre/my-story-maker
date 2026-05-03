# core/mod_loader.py

import asyncio
import importlib
import importlib.util
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.core_api import CoreAPI


@dataclass
class ModRecord:
    """Internal loader view of a mod. Not exposed to mods themselves."""

    name: str
    path: Path
    manifest: dict
    module: Any | None = None
    instance: Any | None = None
    exports: dict = field(default_factory=dict)
    state: str = "disabled"  # "disabled" | "loaded" | "error"


@dataclass
class ModStorage:
    """Public read-only view of loaded mods, shared with CoreAPI."""

    manifests: Dict[str, dict] = field(default_factory=dict)
    instances: Dict[str, Any] = field(default_factory=dict)
    states: Dict[str, str] = field(default_factory=dict)
    exports: Dict[str, dict] = field(default_factory=dict)


class ModLoader:
    """Discovers, resolves, orders, and loads mods. Manages their full lifecycle."""

    def __init__(self, mods_root: Path, event_bus, mod_storage: ModStorage):
        self._mods_root = mods_root
        self._event_bus = event_bus
        self._storage = mod_storage
        self._mods: Dict[str, ModRecord] = {}
        self._load_order: List[str] = []

    # --- Discovery ---

    def discover_mods(self) -> None:
        """Scan mods_root for subdirectories containing a valid manifest.json."""
        if not self._mods_root.exists():
            return
        for child in self._mods_root.iterdir():
            if not child.is_dir():
                continue
            manifest = self._load_manifest(child / "manifest.json")
            if not manifest:
                continue
            name = manifest.get("name")
            if not name:
                continue
            self._mods[name] = ModRecord(name=name, path=child, manifest=manifest)
            self._storage.manifests[name] = manifest
            self._storage.states[name] = "disabled"

    def _load_manifest(self, path: Path) -> Optional[dict]:
        """Parse and validate a manifest.json. Returns None on failure."""
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            return None
        if "name" not in manifest or "entrypoint" not in manifest:
            return None
        manifest.setdefault("version", "1.0.0")
        manifest.setdefault("type", "extension")
        manifest.setdefault("priority", 0)
        manifest.setdefault("requires", {})
        manifest.setdefault("conflicts", {})
        manifest.setdefault("permissions", [])
        return manifest

    # --- Dependency resolution ---

    def _resolve_dependencies(self) -> None:
        """Mark mods as errored if any declared dependency is missing."""
        for rec in self._mods.values():
            for dep in rec.manifest.get("requires", {}):
                if dep not in self._mods:
                    rec.state = "error"

    def _check_conflicts(self) -> None:
        """Mark mods as errored if a declared conflict is present."""
        for rec in self._mods.values():
            for conflict in rec.manifest.get("conflicts", {}):
                if conflict in self._mods:
                    rec.state = "error"

    # --- Load ordering ---

    def _compute_load_order(self) -> None:
        """
        Topological sort on the dependency graph, with priority as tiebreaker.
        Higher priority value = loaded earlier.
        """
        deps: Dict[str, List[str]] = {
            name: list(rec.manifest.get("requires", {}).keys())
            for name, rec in self._mods.items()
            if rec.state != "error"
        }
        priorities: Dict[str, int] = {
            name: int(rec.manifest.get("priority", 0))
            for name, rec in self._mods.items()
        }

        remaining = set(deps.keys())
        order: List[str] = []

        while remaining:
            ready = [n for n in remaining if all(d in order for d in deps[n])]
            if not ready:
                ready = list(remaining)  # break cycles: load remainder as-is
            ready.sort(key=lambda n: priorities.get(n, 0), reverse=True)
            for name in ready:
                order.append(name)
                remaining.remove(name)

        self._load_order = order

    # --- Main pipeline ---

    async def load_all(self) -> None:
        """Run the full load pipeline: discover → resolve → order → load → on_ready."""
        self.discover_mods()
        self._resolve_dependencies()
        self._check_conflicts()
        self._compute_load_order()

        for name in self._load_order:
            rec = self._mods[name]
            if rec.state != "error":
                await self._load_mod(rec)

        for name in self._load_order:
            rec = self._mods[name]
            if rec.state == "loaded":
                await self._call_lifecycle(rec, "on_ready")

    # --- Single mod loading ---

    async def _load_mod(self, rec: ModRecord) -> None:
        """
        Dynamically import a mod, inject CoreAPI, run on_load/on_init, collect exports.
        Accepts a top-level Mod class or bare module as the instance.
        """
        module_path = rec.path / rec.manifest.get("entrypoint", "main.py")
        if not module_path.is_file():
            rec.state = "error"
            return

        try:
            spec = importlib.util.spec_from_file_location(
                f"mods.{rec.name}", module_path
            )
            if spec is None or spec.loader is None:
                rec.state = "error"
                return
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception:
            rec.state = "error"
            return

        rec.module = module
        rec.instance = getattr(module, "Mod", module)  # Mod class or bare module

        core = CoreAPI(self._event_bus, self._storage, rec.name)
        setattr(rec.instance, "core", core)

        await self._call_lifecycle(rec, "on_load")
        await self._call_lifecycle(rec, "on_init")

        exports = getattr(module, "exports", {})
        if isinstance(exports, dict):
            rec.exports = exports
            self._storage.exports[rec.name] = exports

        rec.state = "loaded"
        self._storage.instances[rec.name] = rec.instance
        self._storage.states[rec.name] = "enable"

    # --- Lifecycle ---

    async def _call_lifecycle(self, rec: ModRecord, hook: str) -> None:
        """Call a lifecycle hook (on_load, on_init, on_ready, on_shutdown) if it exists. Supports sync and async."""
        if rec.instance is None:
            return
        func = getattr(rec.instance, hook, None)
        if func is None:
            return
        core = getattr(rec.instance, "core", None)
        if asyncio.iscoroutinefunction(func):
            await func(core)
        else:
            func(core)

    async def shutdown_all(self) -> None:
        """Call on_shutdown on all loaded mods in reverse load order."""
        for name in reversed(self._load_order):
            rec = self._mods[name]
            if rec.state != "loaded":
                continue
            await self._call_lifecycle(rec, "on_shutdown")
            rec.state = "disabled"
            self._storage.states[rec.name] = "disabled"

    # --- Hot reload (partial) ---

    async def reload_mod(self, name: str) -> None:
        """
        Hot-reload a single mod: shutdown → purge → re-import → on_ready.
        Note: does not rewire existing subscribers or dependents.
        """
        rec = self._mods.get(name)
        if not rec or rec.state != "loaded":
            return

        await self._call_lifecycle(rec, "on_shutdown")

        module_name = getattr(rec.module, "__name__", None)
        if module_name and module_name in importlib.sys.modules:
            del importlib.sys.modules[module_name]

        rec.module = None
        rec.instance = None
        rec.exports = {}
        rec.state = "disabled"
        self._storage.instances.pop(name, None)
        self._storage.exports.pop(name, None)
        self._storage.states[name] = "disabled"

        await self._load_mod(rec)
        await self._call_lifecycle(rec, "on_ready")

    # --- Public API ---

    def get_mod(self, name: str) -> Any | None:
        """Return the live instance of a mod, or None."""
        rec = self._mods.get(name)
        return rec.instance if rec else None

    def get_manifest(self, name: str) -> dict | None:
        """Return the manifest of a mod, or None."""
        rec = self._mods.get(name)
        return rec.manifest if rec else None

    def get_exports(self, name: str) -> dict | None:
        """Return the exports dict of a mod, or None."""
        rec = self._mods.get(name)
        return rec.exports if rec else None
