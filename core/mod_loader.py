# core/mod_loader.py

import importlib.util
import json
import pathlib
import sys
from typing import Any, Dict, List


class ModLoader:
    def __init__(self):
        self.loaded_mods: Dict[str, Any] = {}
        self.warnings: List[str] = []   # Collecteur de warnings

    def load_mods_from_folder(self, folder: str) -> List[str]:
        folder_path = pathlib.Path(folder)
        if not folder_path.exists():
            return []
        # 1) Lire les métadonnées
        mods_meta = self._scan_mods(folder_path)
        # 2) Résoudre les dépendances
        load_order = self._resolve_dependencies(mods_meta)
        # 3) Charger dans l'ordre
        for mod_info in load_order:
            try:
                self._load_single_mod(mod_info["path"], mod_info["meta"])
            except Exception as e:
                raise EngineError(f"Error while loading mod '{mod_info['name']}': {e}") from e
        return self.warnings

    def load_single_mod_from_dir(self, mod_dir: pathlib.Path) -> List[str]:
        mod_json = mod_dir / "mod.json"
        if not mod_json.exists():
            raise EngineError(f"No mod.json found in '{mod_dir}'")
        try:
            with mod_json.open("r", encoding="utf-8") as f:
                meta = json.load(f)
        except json.JSONDecodeError as e:
            raise EngineError(f"Invalid mod.json in '{mod_dir.name}': {e}")
        depends = meta.get("depends", [])
        if not isinstance(depends, list):
            raise EngineError(f"'depends' must be a list in mod '{meta.get('name', mod_dir.name)}'")
        missing = [dep for dep in depends if dep not in self.loaded_mods]
        if missing:
            self.warnings.append(f"Skipping mod '{meta.get('name')}' : missing dependencies {missing}")
            return self.warnings

        self._load_single_mod(mod_dir, meta)
        """# Démarrer l'engine si présent
        engine = self.context.mod_states.get("engine")
        if engine and self.context.current_node is None:
            engine.start("start")"""
        return self.warnings

    def _load_single_mod(self, mod_dir: pathlib.Path, meta: Dict[str, Any]) -> None:
        mod_name = meta.get("name", mod_dir.name)
        if "name" not in meta:
            self.warnings.append(f"Mod '{mod_dir.name}' has no 'name' field, using folder name")

        mod_py = mod_dir / "mod.py"
        if mod_name in self.loaded_mods:
            raise EngineError(f"Mod name conflict: '{mod_name}' is already loaded")

        module_name = f"mod_{mod_name}"
        spec = importlib.util.spec_from_file_location(module_name, mod_py)
        if spec is None or spec.loader is None:
            raise EngineError(f"Cannot load mod '{mod_name}'")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            del sys.modules[module_name]
            raise EngineError(f"Error while importing mod '{mod_name}': {e}") from e

        if not hasattr(module, "register") or not callable(module.register):
            del sys.modules[module_name]
            raise EngineError(f"Mod '{mod_name}' has no register(context) function")

        # Contexte transactionnel
        reg_ctx = RegistrationContext(self.context)

        # Variables par défaut
        variables = meta.get("variables", {})
        if not isinstance(variables, dict):
            del sys.modules[module_name]
            raise EngineError(f"'variables' must be a dict in mod '{mod_name}'")

        for key, value in variables.items():
            reg_ctx.state.setdefault(key, value)

        # Appel à register()
        try:
            result = module.register(reg_ctx)
            if result is not None:
                del sys.modules[module_name]
                raise EngineError(f"Mod '{mod_name}' register() must return None")

            reg_ctx.mod_states.setdefault("mods_loaded", []).append(mod_name)
            reg_ctx.commit()

            self.loaded_mods[mod_name] = module
            self.context.events.emit_log(f"Mod '{mod_name}' loaded")

        except Exception as e:
            del sys.modules[module_name]
            raise EngineError(f"Error while registering mod '{mod_name}': {e}") from None

    def _scan_mods(self, folder_path: pathlib.Path):
        mods = []
        for mod_dir in folder_path.iterdir():
            if not mod_dir.is_dir():
                continue

            mod_json = mod_dir / "mod.json"
            mod_py   = mod_dir / "mod.py"
            if not mod_json.exists() or not mod_py.exists():
                continue

            try:
                with mod_json.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
            except json.JSONDecodeError as e:
                raise EngineError(f"Invalid mod.json in '{mod_dir.name}': {e}")

            name = meta.get("name", mod_dir.name)
            if "name" not in meta:
                self.warnings.append(f"Mod '{mod_dir.name}' has no 'name' field, using folder name")

            depends = meta.get("depends", [])
            if not isinstance(depends, list):
                raise EngineError(f"'depends' must be a list in mod '{name}'")

            active = meta.get("active", False)
            if active:
                mods.append({
                    "name":    name,
                    "depends": depends,
                    "path":    mod_dir,
                    "meta":    meta,
                })

        return mods

    def _resolve_dependencies(self, mods_meta):
        mods_by_name = {}
        for m in mods_meta:
            if m["name"] in mods_by_name:
                raise EngineError(f"Duplicate mod name: '{m['name']}'")
            mods_by_name[m["name"]] = m
        # Filtrage des mods avec dépendances manquantes
        while True:
            to_remove = []
            for m in list(mods_by_name.values()):
                missing = [dep for dep in m["depends"] if dep not in mods_by_name]
                if missing:
                    self.warnings.append(f"Skipping mod '{m['name']}' : missing dependencies {missing}")
                    to_remove.append(m["name"])
            if not to_remove:
                break
            for name in to_remove:
                del mods_by_name[name]
        # Tri topologique
        resolved = []
        visited  = {}
        def visit(mod):
            name = mod["name"]
            if name in visited:
                if visited[name] == "visiting":
                    raise EngineError(f"Circular dependency detected at mod '{name}'")
                return
            visited[name] = "visiting"
            for dep in mod["depends"]:
                visit(mods_by_name[dep])
            visited[name] = "done"
            resolved.append(mod)
        for mod in mods_by_name.values():
            visit(mod)
        return resolved
        return resolved
