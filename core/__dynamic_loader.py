# core/__dynamic_loader.py

import importlib.util
import inspect
import sys

from core.__mod_storage import ModStorage
from resources.EVENTS import ENGINE_READY, MOD_ERROR, MOD_LOADED
from resources.LOG_LEVELS import DEBUG, ERROR


class DynamicLoader:
    """Import mod entrypoints, instantiate their Mod class, and call on_load."""

    def __init__(self, core, log, emit_error, emit) -> None:
        self.log = log
        self.emit_error = emit_error
        self.emit = emit
        self.core = core

    def run_dynamic_loading(self, mod_storage: ModStorage) -> None:
        """Import and initialise every enabled mod in load_order.

        For each mod the pipeline is:
        1. Import the entrypoint module from disk.
        2. Locate the 'Mod' class and verify it has all required lifecycle hooks.
        3. Instantiate the class.
        4. Call on_load(core).
        5. Subscribe on_ready to ENGINE_READY so it fires at the right lifecycle stage.

        Any failure in steps 1-4 disables the mod and emits MOD_ERROR.
        """

        def disable_mod(mod: str, error_msg: str, payload: dict) -> None:
            """Mark a mod as disabled, log the reason, and emit an error event."""
            mod_storage.states[mod] = "disable"
            mod_storage.instances[mod] = None
            mod_storage.errors.setdefault(mod, []).append(error_msg)
            self.log(ERROR, f"[{mod}] {error_msg}")
            self.emit_error(MOD_ERROR, payload)

        for mod in mod_storage.load_order:
            if mod_storage.states.get(mod) == "disable":
                continue

            entrypoint_path = (
                mod_storage.paths[mod] / mod_storage.manifests[mod]["entrypoint"]
            )

            # 1. Import module
            module = EntrypointLoader.import_from_path(entrypoint_path)
            if module is None:
                disable_mod(mod, "import failed", {"mod": mod})
                continue

            # 2. Locate Mod class
            cls = EntrypointLoader.get_main_class(module)
            if cls is None:
                disable_mod(mod, "main class invalid or missing", {"mod": mod})
                continue

            # 3. Instantiate and verify hooks
            instance = ModInstantiator.instantiate(cls)
            if instance is None:
                disable_mod(mod, "instantiation failed", {"mod": mod})
                continue

            # 4. Call on_load
            success = LoadExecutor.run_on_load(instance, self.core, self.log)
            if not success:
                disable_mod(mod, "on_load failed", {"mod": mod})
                continue

            # 5. Success — store instance, wire on_ready, emit MOD_LOADED
            mod_storage.instances[mod] = instance
            self.core.subscribe(ENGINE_READY, instance.on_ready)  # lifecycle wiring
            self.emit(MOD_LOADED, {"mod": mod})


class EntrypointLoader:
    """Load a Python module from an arbitrary file path."""

    @staticmethod
    def import_from_path(path):
        """Import and return the module at the given Path, or None on any failure."""
        try:
            if not path.exists() or not path.is_file():
                return None
            if path.suffix != ".py":
                return None
            module_name = f"_mod_{path.stem}_{id(path)}"
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            return module
        except Exception:
            return None

    @staticmethod
    def get_main_class(module):
        """Return the 'Mod' class from the module, or None when absent or not a class."""
        try:
            if not hasattr(module, "Mod"):
                return None
            cls = getattr(module, "Mod")
            if not isinstance(cls, type):
                return None
            return cls
        except Exception:
            return None


class ModInstantiator:
    """Instantiate a Mod class and verify all required lifecycle hooks are present."""

    @staticmethod
    def instantiate(clas):
        """Create an instance of clas and validate its lifecycle hook signatures.

        All four hooks (on_load, on_init, on_ready, on_shutdown) must exist,
        be callable, and accept at least one positional argument besides self.
        Returns the instance on success, or None on any failure.
        """
        try:
            instance = clas()
            required = ["on_load", "on_init", "on_ready", "on_shutdown"]
            for method in required:
                if not hasattr(clas, method):
                    return None
                attr = getattr(instance, method)
                if not callable(attr):
                    return None
                sig = inspect.signature(attr)
                if len(sig.parameters) < 1:
                    return None
            return instance
        except Exception:
            return None


class LoadExecutor:
    """Call a mod's on_load hook safely."""

    @staticmethod
    def run_on_load(instance, core, log) -> bool:
        """Call instance.on_load(core) and return True on success, False on exception."""
        try:
            instance.on_load(core)
            return True
        except Exception as e:
            log(DEBUG, f"[on_load error] {e}")
            return False
