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

    def load_all(self):
        self.emit(ENGINE_BOOT, {})
        self.log(INFO, "[ModLoader] ENGINE_BOOT")
        # 1. Discovery sur les chemins canoniques (définis en dur dans ModDiscovery)
        self.discovery.discover_mods(self.mod_storage)
        # 2. Manifests : lecture + validation + stockage
        self.manifest_loader.run_manifest_pipeline(self.mod_storage)
        # 3. Résolution des dépendances
        self.dependency_module.run(self.mod_storage)
        # 4. Chargement dynamique (on_load)
        self.dynamic_loader.run_dynamic_loading(self.mod_storage)
        # 5. ENGINE_INIT + on_init
        self.emit(ENGINE_INIT, {})
        self.init_executor.run_on_init(self.mod_storage)
        # 6. ENGINE_READY (on_ready via EventBus)
        self.ready_executor.run_on_ready(self.emit)

    def shutdown(self):
        try:
            self.shutdown_executor.run_on_shutdown(self.mod_storage)
        except Exception as e:
            self.log(ERROR, f"[ModLoader] shutdown error: {e}")
