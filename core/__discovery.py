# core/__discovery.py

from pathlib import Path
from typing import Callable

from core.__mod_storage import ModStorage
from EVENTS import MOD_DISCOVERED
from LOG_LEVELS import DEBUG, ERROR, INFO


class ModDiscovery :
    def __init__(self, log:Callable, emit_error:Callable, emit:Callable) -> None:
        self.log = log
        self.emit = emit
        self.emit_error = emit_error

    def discover_mods(self, mod_storage : ModStorage) -> None :
        """
Store mods from canonic folder in mod_storage
Don't store manifest
        """
        paths = (
            Path("core/default_mods"), 
            Path("mods/default"), 
            Path("mods")
            )
        for path in paths :
            if not path.exists():
                self.log(ERROR, f"miss canonic folder : {path}") 
                continue
            if not path.is_dir(): 
                self.log(ERROR, f"canonic {path} isn't folder") 
                continue
            for mod_dir in path.iterdir():
                if not mod_dir.exists() :
                    continue
                if not mod_dir.is_dir():
                    continue
                mod_name = mod_dir.name
                if mod_name[:4] != "mod_" :
                    continue
                mod_manifest = mod_dir / "manifest.json"
                if not mod_manifest.exists() :
                    self.log(DEBUG, f"{mod_name} has no manifest.json")
                    continue
                mod_storage.paths[mod_name] = mod_dir
                mod_storage.states[mod_name] = "discovered"
                mod_storage.errors[mod_name] = []
                mod_storage.dependencies[mod_name] = []
                mod_storage.conflicts[mod_name] = []
                self.emit(MOD_DISCOVERED, {"mod": mod_name, "path": str(mod_dir)})
                self.log(INFO, f"discovered mod {mod_name}")
