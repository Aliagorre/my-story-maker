# core/__manifest_reader.py

import json
from pathlib import Path
from typing import Callable

from core.__mod_storage import ModStorage
from EVENTS import MOD_MANIFEST_ERROR
from LOG_LEVELS import DEBUG


def reader(mod_storage : ModStorage, log : Callable, emit_error : Callable) -> None :
    for mod in mod_storage.states :
        if mod_storage.states[mod] == "discovered" :
            manifest_dict = manifest_reader(mod_storage.paths[mod])
            if len(manifest_dict) == 0 :
                mod_storage.states[mod] = "disable"
                emit_error(MOD_MANIFEST_ERROR, {})
                log(DEBUG, "message to define")
                continue

        errors = ManifestValidator().validate(manifest_dict)
        if errors:
            mod_storage.states[mod] = "disable"
            mod_storage.errors[mod] = errors
            emit_error(MOD_MANIFEST_ERROR, {})
            log(DEBUG, "message to define")
            continue

        ManifestProcessor().store(manifest_dict, mod_storage)


def manifest_reader(mod_path : Path) -> dict :
    manifest_path = mod_path / "manifest.json"
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
            if not isinstance(manifest, dict) :
                return {}
            return manifest
    except json.JSONDecodeError as e:
        return {}

class ManifestValidator :
    def validate(self, manifest_dict) -> list :
        pass

class ManifestProcessor :
    def store(self, manifest_dict : dict, mod_storage : ModStorage) -> None :
        pass

# We don't need class, no ?