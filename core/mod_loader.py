# core/mod_loader.py

from pathlib import Path

from core.__dependency import DependencyModule  # Modules 4 + 5
from core.__discovery import ModDiscovery  # Module 2
from core.__dynamic_loader import DynamicLoader  # Module 6
from core.__lifecycle import InitExecutor, ReadyExecutor, ShutdownExecutor  # Module 7
from core.__manifest import ManifestLoader, ManifestProcessor  # Module 3
from core.__mod_storage import ModStorage
from EVENTS import ENGINE_BOOT, ENGINE_INIT, MOD_DISCOVERED
from LOG_LEVELS import ERROR, INFO


class ModLoader:
    def __init__(self, core, log, emit, emit_error):
        """
        core  : Core API (emit, log, services, etc.)
        log   : fonction (level, message)
        emit  : fonction (event_name, payload)
        emit_error : fonction (event_name, payload) pour erreurs
        """
        self.core = core
        self.log = log
        self.emit = emit
        self.emit_error = emit_error

        self.mod_storage = ModStorage()

        # sous-modules
        self.discovery = ModDiscovery(log, emit, emit_error)
        self.manifest_loader = ManifestLoader(log, emit_error)
        self.manifest_processor = ManifestProcessor
        self.dependency_module = DependencyModule(emit_error, log)
        self.dynamic_loader = DynamicLoader(core, log, emit_error, emit)
        self.init_executor = InitExecutor(core, log, emit_error, emit)
        self.ready_executor = ReadyExecutor
        self.shutdown_executor = ShutdownExecutor(core, log)

    def load_all(self, search_paths: list[Path]):
        """
        Pipeline complet du Mod Loader :
        1. Discovery
        2. Manifest reading + validation
        3. Dependency resolution
        4. Dynamic loading (on_load)
        5. Initialization (on_init)
        6. ENGINE_READY (on_ready via events)
        """

        self.emit(ENGINE_BOOT, {})
        self.log(INFO, "[ModLoader] ENGINE_BOOT")

        for base_path in search_paths:
            self.discovery.scan_folder(base_path, self.mod_storage)

        for mod, path in self.mod_storage.paths.items():
            manifest, errors = self.manifest_loader.load_manifest(path)
            self.manifest_processor.store(
                mod_name=mod,
                manifest=manifest,
                mod_storage=self.mod_storage,
                errors=errors
            )
        self.dependency_module.run(self.mod_storage)
        self.dynamic_loader.run_dynamic_loading(self.mod_storage)
        self.emit(ENGINE_INIT, {})
        self.init_executor.run_on_init(self.mod_storage)
        self.ready_executor.run_on_ready(self.emit)

    def shutdown(self):
        """
        Appelé lors de l’arrêt du moteur :
        - ENGINE_SHUTDOWN est émis ailleurs (EventBus / Core)
        - on_shutdown est appelé en ordre inverse
        """
        try:
            self.shutdown_executor.run_on_shutdown(self.mod_storage)
        except Exception as e:
            self.log(ERROR, f"[ModLoader] shutdown error: {e}")
