# core/__manifest.py

import json
from copy import deepcopy
from pathlib import Path
from typing import Callable

from core.__mod_storage import ModStorage
from core.__version import ConstraintParser, Version
from resources.EVENTS import MOD_MANIFEST_ERROR
from resources.LOG_LEVELS import DEBUG
from resources.MOD_TYPES import MOD_TYPES


def is_snake_case(string: str) -> bool:
    """Return True when the string uses only lowercase letters, digits, and underscores."""
    if not string:
        return False
    return all("a" <= x <= "z" or "0" <= x <= "9" or x == "_" for x in string)


class ManifestLoader:
    """Read, validate, and store manifests for all discovered mods."""

    def __init__(self, log: Callable, emit_error: Callable) -> None:
        self.log = log
        self.emit_error = emit_error

    def run_manifest_pipeline(self, mod_storage: ModStorage) -> None:
        """Process every discovered mod: read its manifest, validate it, and store the result.

        Mods whose manifest cannot be read or that fail validation are disabled.
        Valid version strings and constraint expressions are parsed into their
        respective objects before storage.
        """
        for mod in mod_storage.states:
            if mod_storage.states[mod] != "discovered":
                continue
            mod_dir = mod_storage.paths[mod]
            manifest_dict = ManifestReader.read(mod_dir)
            if not manifest_dict:
                mod_storage.states[mod] = "disable"
                self.emit_error(MOD_MANIFEST_ERROR, {"mod": mod})
                self.log(DEBUG, f"incorrect manifest for {mod}")  # was missing f-prefix
                continue
            errors = ManifestValidator.validate(manifest_dict, mod_dir)
            for error in errors:
                self.log(DEBUG, error)
            ManifestProcessor.store(mod, manifest_dict, mod_storage, errors)


class ManifestReader:
    """Read a manifest.json file from a mod directory."""

    @staticmethod
    def read(mod_path: Path) -> dict:
        """Return the parsed JSON dict from manifest.json inside mod_path.

        Returns an empty dict when the file is missing, unreadable, or not a JSON object.
        """
        manifest_path = mod_path / "manifest.json"
        try:
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = json.load(f)
                if not isinstance(manifest, dict):
                    return {}
                return manifest
        except (json.JSONDecodeError, FileNotFoundError):
            return {}


class ManifestValidator:
    """Validate a manifest dict against the engine's requirements."""

    @staticmethod
    def rule_name_format(manifest: dict) -> str | None:
        """Return an error string when the 'name' field is missing or malformed, else None."""
        if "name" not in manifest:
            return "miss name"
        name = manifest["name"]
        if not isinstance(name, str):
            return "name isn't str"
        if not name.startswith("mod_"):
            return f"{name} isn't mod's name"
        if not is_snake_case(name):
            return f"{name} isn't snake case"
        return None

    @staticmethod
    def rule_version_semver(manifest: dict) -> str | None:
        """Return an error string when 'version' is missing or not a valid SemVer, else None."""
        if "version" not in manifest:
            return "miss version"
        version = manifest["version"]
        if not isinstance(version, str):
            return "version isn't str"
        if Version.parse(version) is None:
            return "version isn't semVer"
        return None

    @staticmethod
    def rule_entrypoint_exists(manifest: dict, mod_dir: Path) -> str | None:
        """Return an error string when the entrypoint file is missing or not declared, else None."""
        if "entrypoint" not in manifest:
            return "miss entrypoint"
        entrypoint = mod_dir / Path(manifest["entrypoint"])
        if not entrypoint.exists():
            return f"{entrypoint} don't exist"
        return None

    @staticmethod
    def rule_type_valid(manifest: dict) -> str | None:
        """Return an error string when 'type' is missing or not a known mod type, else None."""
        if "type" not in manifest:
            return "miss type"
        mod_type = manifest["type"]  # renamed from 'type' which shadowed the builtin
        if mod_type not in MOD_TYPES:
            return f"{mod_type} type don't exist"
        return None

    @staticmethod
    def rule_priority_int(manifest: dict) -> str | None:
        """Return an error string when 'priority' is missing or not an integer, else None."""
        if "priority" not in manifest:
            return "miss priority"
        priority = manifest["priority"]
        if not isinstance(priority, int):
            return "priority isn't int"
        return None

    @staticmethod
    def rule_requires_dict(manifest: dict) -> str | None:
        """Return an error string when 'requires' is missing or not a dict, else None."""
        if "requires" not in manifest:
            return "miss requires"
        requires = manifest["requires"]
        if not isinstance(requires, dict):
            return "requires isn't dict"
        return None

    @staticmethod
    def rule_conflicts_dict(manifest: dict) -> str | None:
        """Return an error string when 'conflicts' is missing or not a dict, else None."""
        if "conflicts" not in manifest:
            return "miss conflicts"
        conflicts = manifest["conflicts"]
        if not isinstance(conflicts, dict):
            return "conflicts isn't dict"
        return None

    @staticmethod
    def rule_permissions_list(manifest: dict) -> str | None:
        """Return an error string when 'permissions' is present but not a list, else None."""
        if "permissions" not in manifest:
            return None
        permissions = manifest["permissions"]
        if not isinstance(permissions, list):
            return "permissions isn't list"
        return None

    @staticmethod
    def validate(manifest: dict, mod_dir: Path) -> list:
        """Run all validation rules and return a list of error strings.

        An empty list means the manifest is valid.
        """
        checks = [
            ManifestValidator.rule_name_format(manifest),
            ManifestValidator.rule_version_semver(manifest),
            ManifestValidator.rule_entrypoint_exists(manifest, mod_dir),
            ManifestValidator.rule_type_valid(manifest),
            ManifestValidator.rule_priority_int(manifest),
            ManifestValidator.rule_requires_dict(manifest),
            ManifestValidator.rule_conflicts_dict(manifest),
            ManifestValidator.rule_permissions_list(manifest),
        ]
        return [error for error in checks if error is not None]


class ManifestProcessor:
    """Store a validated manifest into ModStorage, converting version and constraint strings."""

    @staticmethod
    def store(
        mod_name: str,
        manifest: dict,
        mod_storage: ModStorage,
        errors: list,
    ) -> None:
        """Write the manifest to mod_storage and set the mod state accordingly.

        Mods with validation errors are disabled.
        The 'active' key (bool or string) overrides the default enabled state.
        Version strings are parsed into Version objects.
        Constraint strings in 'requires' and 'conflicts' are parsed into Condition lists.
        """
        if errors:
            mod_storage.states[mod_name] = "disable"
            mod_storage.errors[mod_name] = errors
            return

        if "active" in manifest:
            active = manifest["active"]
            if isinstance(active, bool):
                mod_storage.states[mod_name] = "enable" if active else "disable"
            elif isinstance(active, str):
                if active in {"inactive", "off", "disable"}:
                    mod_storage.states[mod_name] = "disable"
                else:
                    mod_storage.states[mod_name] = "enable"
        else:
            mod_storage.states[mod_name] = "enable"

        mod_storage.errors[mod_name] = errors

        parsed_version = Version.parse(manifest["version"])
        manifest["version"] = parsed_version

        for dep, constraint in manifest["requires"].items():
            parsed = ConstraintParser.parse(constraint)
            if parsed is not None:
                manifest["requires"][dep] = parsed

        for dep, constraint in manifest["conflicts"].items():
            parsed = ConstraintParser.parse(constraint)
            if parsed is not None:
                manifest["conflicts"][dep] = parsed

        mod_storage.manifests[mod_name] = deepcopy(manifest)
