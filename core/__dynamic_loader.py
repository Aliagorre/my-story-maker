# core/__dynamic_loader.py

import importlib.util
import inspect
import sys

from core.__mod_storage import ModStorage
from EVENTS import MOD_ERROR, MOD_LOADED
from LOG_LEVELS import DEBUG, ERROR


class DynamicLoader:
    def __init__(self, core, log, emit_error, emit) -> None:
        self.log = log
        self.emit_error = emit_error
        self.emit = emit
        self.core = core

    def run_dynamic_loading(self, mod_storage: ModStorage):
        def disable_mod(mod, error_msg, payload):
            mod_storage.states[mod] = "disable"
            mod_storage.instances[mod] = None
            if mod not in mod_storage.errors:
                mod_storage.errors[mod] = []
            mod_storage.errors[mod].append(error_msg)
            self.log(ERROR, f"[{mod}] {error_msg}")
            self.emit_error(MOD_ERROR, payload)

        for mod in mod_storage.load_order:
            if mod_storage.states.get(mod) == "disable":
                continue
            entrypoint_path = (
                mod_storage.paths[mod]
                / mod_storage.manifests[mod]["entrypoint"]
            )
            # 1. import module
            module = EntrypointLoader.import_from_path(entrypoint_path)
            if module is None:
                disable_mod(mod, "import failed", {"mod": mod})
                continue
            # 2. get class
            cls = EntrypointLoader.get_main_class(module)
            if cls is None:
                disable_mod(mod, "main class invalid or missing", {"mod": mod})
                continue
            # 3. instantiate
            instance = ModInstantiator.instantiate(cls)
            if instance is None:
                disable_mod(mod, "instantiation failed", {"mod": mod})
                continue
            # 4. run on_load
            success = LoadExecutor.run_on_load(instance, self.core, self.log)
            if not success:
                disable_mod(mod, "on_load failed", {"mod": mod})
                continue
            # 5. success
            mod_storage.instances[mod] = instance
            self.emit(MOD_LOADED, {"mod": mod})

class EntrypointLoader:
    @staticmethod
    def import_from_path(path):
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
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None

    @staticmethod
    def get_main_class(module):
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
    @staticmethod
    def instantiate(clas):
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
    @staticmethod
    def run_on_load(instance, core, log):
        try:
            instance.on_load(core)
            return True
        except Exception as e:
            log(DEBUG, f"[on_load error] {e}")
            return False
        