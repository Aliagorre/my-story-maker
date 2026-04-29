from LOG_LEVELS import CRITICAL, DEBUG, ERROR, INFO, WARNING


class Mod:
    def on_load(self, core):
        self.core = core
        core.register_service("logger", self)

        core.subscribe("ENGINE_BOOT", self.on_engine_event)
        core.subscribe("ENGINE_INIT", self.on_engine_event)
        core.subscribe("ENGINE_READY", self.on_engine_event)
        core.subscribe("ENGINE_SHUTDOWN", self.on_engine_event)
        core.subscribe("ENGINE_ERROR", self.on_engine_error)
        core.subscribe("ENGINE_FATAL_ERROR", self.on_engine_error)

        core.subscribe("MOD_DISCOVERED", self.on_mod_event)
        core.subscribe("MOD_LOADED", self.on_mod_event)
        core.subscribe("MOD_INITIALIZED", self.on_mod_event)
        core.subscribe("MOD_ERROR", self.on_mod_error)

        core.subscribe("LOG_EVENT", self.on_log_event)

    # --- service logger ---
    def log(self, level, source, message):
        # tout passe par LOG_EVENT
        self.core.emit("LOG_EVENT", {
            "level": level,
            "source": source,
            "message": message
        })

    # --- handlers : ils utilisent le service, pas print() ---
    def on_engine_event(self, event):
        self.log(INFO, "core", event["name"])

    def on_mod_event(self, event):
        payload = event["payload"]
        mod = payload.get("mod", "?")
        self.log(INFO, "mod_error_and_log", f"{event['name']} {mod}")

    def on_engine_error(self, event):
        self.log(ERROR, "core", f"ENGINE_ERROR: {event['payload']}")

    def on_mod_error(self, event):
        payload = event["payload"]
        mod = payload.get("mod", "?")
        self.log(ERROR, "mod_error_and_log", f"MOD_ERROR in {mod}")

    def on_log_event(self, event):
        payload = event["payload"]
        level = payload["level"]
        source = payload["source"]
        message = payload["message"]

        with open("engine.log", "a", encoding="utf-8") as f:
            f.write(f"[{level}] [{source}] {message}\n")


    def on_init(self, core): pass
    def on_ready(self, event): pass
    def on_shutdown(self, core): pass
