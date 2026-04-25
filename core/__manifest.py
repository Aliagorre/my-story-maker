# core/__manifest.py

import json
from pathlib import Path
from typing import Callable

from core.__mod_storage import ModStorage
from core.__version import ConstraintParser, Version
from EVENTS import MOD_MANIFEST_ERROR
from LOG_LEVELS import DEBUG


class ManifestModule :
    def __init__(self, log : Callable, emit_error : Callable ) -> None:
        self.log = log
        self.emit_error = emit_error

    def run_manifest_pipeline(self, mod_storage : ModStorage) -> None :
        for mod in mod_storage.states :
            if mod_storage.states[mod] == "discovered" :
                mod_dir = mod_storage.paths[mod]
                manifest_dict = ManifestReader.read(mod_dir)
                if len(manifest_dict) == 0 :
                    mod_storage.states[mod] = "disable"
                    self.emit_error(MOD_MANIFEST_ERROR, {})
                    self.log(DEBUG, "message to define")
                    continue
            errors = ManifestValidator.validate(manifest_dict, mod_dir)
            ManifestProcessor.store(mod, manifest_dict, mod_storage, errors)

class ManifestReader :
    @staticmethod
    def read(mod_path : Path) -> dict :
        manifest_path = mod_path / "manifest.json" # It is a file, not a directory, no ?
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
                if not isinstance(manifest, dict) :
                    return {}
                return manifest
        except json.JSONDecodeError :
            return {}

class ManifestValidator :
    @staticmethod
    def rule_name_format(manifest : dict) -> None|str:
        if "name" not in manifest :
            return "miss name"
        name = manifest["name"]
        if not isinstance(name, str) :
            return "name isn't str"
        if name[:4] != "mod_" :
            return "name isn't mod's name"
        
    @staticmethod
    def rule_version_semver(manifest : dict) -> None|str:
        if "version" not in manifest :
            return "miss version"
        version = manifest["version"]
        if not isinstance(version, str) :
            return "version isn't str"
    
    @staticmethod
    def rule_entrypoint_exists(manifest : dict, mod_dir : Path) -> None|str:
        if "entrypoint" not in manifest :
            return "miss entrypoint"
        entrypoint = mod_dir / Path(manifest["entrypoint"])
        if not entrypoint.exists() :
            return f"{entrypoint} don't exist"
    
    @staticmethod
    def rule_type_valid(manifest : dict) -> None|str:
        if "type" not in manifest :
            return "miss type"
        type = manifest["type"]
        if type not in {"core_engine", "core_default", "default", "extension", "experimental"} :
            return f"{type} type don't exist"
    
    @staticmethod
    def rule_priority_int(manifest : dict) -> None|str:
        if "priority" not in manifest :
            return "miss priority"
        priority = manifest["priority"]
        if not isinstance(priority, int) :
            return "priority isn't int"
        
    @staticmethod
    def rule_requires_dict(manifest : dict) -> None|str:
        if "requires" not in manifest :
            return "miss requires "
        requires = manifest["requires"]
        if not isinstance(requires, dict) :
            return "requires isn't dict"
        # for i, j in requires.items() :
        #     if not isinstance(i, str) :
        #         return "requires's key isn't str"
        
    @staticmethod
    def rule_conflicts_dict(manifest : dict) -> None|str:
        if "conflicts" not in manifest :
            return "miss conflicts"
        conflicts = manifest["conflicts"]
        if not isinstance(conflicts , dict) :
            return "conflicts isn't dict"
        
    @staticmethod
    def rule_permissions_list(manifest : dict)  -> None|str:
        if "permissions" not in manifest :
            return "miss permissions"
        permissions = manifest["permissions"]
        if not isinstance(permissions , list) :
            return "permissions isn't list"

    @staticmethod
    def validate(manifest : dict, mod_dir : Path) -> list :
        errors = [
        ManifestValidator.rule_name_format(manifest),
        ManifestValidator.rule_version_semver(manifest),
        ManifestValidator.rule_entrypoint_exists(manifest, mod_dir),
        ManifestValidator.rule_type_valid(manifest),
        ManifestValidator.rule_priority_int(manifest),
        ManifestValidator.rule_requires_dict(manifest),
        ManifestValidator.rule_conflicts_dict(manifest),
        ManifestValidator.rule_permissions_list(manifest)
        ]
        return [error for error in errors if error is not None]

class ManifestProcessor :
    @staticmethod
    def store(mod_name : str, manifest : dict, mod_storage : ModStorage, errors : list) -> None :
        if errors :
            mod_storage.states[mod_name] = "disable"
        elif "active" in manifest :
            if isinstance(manifest["active"], bool) :
                mod_storage.states[mod_name] = "enable" if manifest["active"] else "disable"
            elif isinstance(manifest["active"], str) :
                if manifest["active"] in {"inactive", "off", "disable"} :
                    mod_storage.states[mod_name] = "disable"
                else :
                    mod_storage.states[mod_name] = "enable"
        else :
            mod_storage.states[mod_name] = "enable"
        mod_storage.errors[mod_name] = errors
        parsed_version = Version.parse(manifest["version"])
        manifest["version"] = parsed_version
        for dep, constraint in manifest["requires"].items():
            manifest["requires"][dep] = ConstraintParser.parse(constraint)
        for dep, constraint in manifest["conflicts"].items():
            manifest["conflicts"][dep] = ConstraintParser.parse(constraint)
        mod_storage.manifests[mod_name] = manifest
