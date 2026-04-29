# core/__lifecycle.py

from core.__mod_storage import ModStorage
from EVENTS import ENGINE_READY, MOD_ERROR, MOD_INITIALIZED
from LOG_LEVELS import ERROR


class InitExecutor :
    def __init__(self, core, log, emit_error, emit) -> None:
        self.log = log
        self.emit_error = emit_error
        self.emit = emit
        self.core = core

    def run_on_init(self, mod_storage : ModStorage) :
        for mod in mod_storage.load_order :
            instance = mod_storage.instances.get(mod)
            if instance is None :
                continue
            try :
                instance.on_init(self.core)
            except Exception as e:
                mod_storage.instances[mod] = None 
                mod_storage.states[mod] = "disable"
                mod_storage.errors.setdefault(mod, []).append("on_init failed")
                self.log(ERROR, f"[{mod}] on_init failed: {e}")
                self.emit_error(MOD_ERROR, {"mod" : mod})
                continue
            self.emit(MOD_INITIALIZED, {"mod": mod})

class ReadyExecutor :
    @staticmethod
    def run_on_ready(emit) :
        emit(ENGINE_READY, {})

class ShutdownExecutor :
    def __init__(self, core, log) -> None:
        self.core = core 
        self.log = log

    def run_on_shutdown(self, mod_storage : ModStorage) :
        for mod in reversed(mod_storage.load_order):
            if mod_storage.states[mod] == "disable" :
                continue
            instance =  mod_storage.instances.get(mod)
            if instance is None :
                continue
            try:
                instance.on_shutdown(self.core)
            except Exception as e:
                self.log(ERROR, f"[{mod}] on_shutdown error : {e}")
                continue

