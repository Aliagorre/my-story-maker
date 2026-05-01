# core/mod_loader.py

from core.__dependency import DependencyModule
from core.__discovery import ModDiscovery
from core.__dynamic_loader import DynamicLoader
from core.__lifecycle import InitExecutor, ReadyExecutor, ShutdownExecutor
from core.__manifest import ManifestLoader, ManifestProcessor
from core.__mod_storage import ModStorage
from resources.EVENTS import ENGINE_BOOT, ENGINE_INIT, ENGINE_SHUTDOWN
from resources.LOG_LEVELS import ERROR, INFO


class ModLoader:
    """Orchestrates the full mod lifecycle: discovery, validation, loading, init, and shutdown."""

    def __init__(self, core, log, emit, emit_error):
        """Set up the loader and all pipeline sub-modules.

        Args:
            core: CoreAPI instance exposed to mods.
            log: Callable(level, message) used for internal logging.
            emit: Callable(event_name, payload) for normal events.
            emit_error: Callable(event_name, payload) for error events.
        """
        self.core = core
        self.log = log
        self.emit = emit
        self.emit_error = emit_error

        self.mod_storage = ModStorage()

        # Fixed: ModDiscovery expects (log, emit_error, emit) — they were swapped.
        self.discovery = ModDiscovery(log, emit_error, emit)
        self.manifest_loader = ManifestLoader(log, emit_error)
        self.manifest_processor = ManifestProcessor
        self.dependency_module = DependencyModule(log, emit_error)
        self.dynamic_loader = DynamicLoader(core, log, emit_error, emit)
        self.init_executor = InitExecutor(core, log, emit_error, emit)
        self.ready_executor = ReadyExecutor
        self.shutdown_executor = ShutdownExecutor(core, log)

    def load_all(self) -> None:
        """Run the complete loading pipeline and bring the engine to the READY state.

        Stages in order:
        1. ENGINE_BOOT event
        2. Mod discovery (scan canonical directories)
        3. Manifest reading, validation and storage
        4. Dependency resolution and load-order calculation
        5. Dynamic import and on_load execution
        6. ENGINE_INIT event + on_init execution
        7. ENGINE_READY event (triggers subscribed on_ready handlers)
        """
        self.emit(ENGINE_BOOT, {})
        self.log(INFO, "[ModLoader] ENGINE_BOOT")
        self.discovery.discover_mods(self.mod_storage)
        self.manifest_loader.run_manifest_pipeline(self.mod_storage)
        self.dependency_module.run(self.mod_storage)
        self.dynamic_loader.run_dynamic_loading(self.mod_storage)
        self.emit(ENGINE_INIT, {})
        self.init_executor.run_on_init(self.mod_storage)
        self.ready_executor.run_on_ready(self.emit)

    def shutdown(self) -> None:
        """Emit ENGINE_SHUTDOWN, then call on_shutdown on all loaded mods in reverse order."""
        try:
            self.emit(ENGINE_SHUTDOWN, {})
            self.shutdown_executor.run_on_shutdown(self.mod_storage)
        except Exception as e:
            self.log(ERROR, f"[ModLoader] shutdown error: {e}")
