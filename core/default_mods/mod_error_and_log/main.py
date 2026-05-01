# core/default_mods/mod_error_and_log/main.py

from resources.__handler import Handler
from resources.LOG_LEVELS import ERROR, INFO


class Mod:
    MOD_NAME = "mod_error_and_log"

    def on_load(self, core):
        self.core = core
        core.register_service("logger", self)

        # ── engine lifecycle ──────────────────────────────────────────────
        # normal : toujours notifié, pas de raison de bloquer les autres
        for event in ("ENGINE_BOOT", "ENGINE_INIT", "ENGINE_READY", "ENGINE_SHUTDOWN"):
            core.subscribe(
                event,
                Handler(
                    self._make_engine_handler(event),
                    name=f"log_engine_{event.lower()}",
                    priority=900,
                    mode="normal",
                    mod_name=self.MOD_NAME,
                ),
            )

        for event in ("ENGINE_ERROR", "ENGINE_FATAL_ERROR"):
            core.subscribe(
                event,
                Handler(
                    self._make_engine_error_handler(event),
                    name=f"log_engine_error_{event.lower()}",
                    priority=900,
                    mode="normal",
                    mod_name=self.MOD_NAME,
                ),
            )

        # ── mod lifecycle ─────────────────────────────────────────────────
        for event in ("MOD_DISCOVERED", "MOD_LOADED", "MOD_INITIALIZED"):
            core.subscribe(
                event,
                Handler(
                    self._make_mod_handler(event),
                    name=f"log_mod_{event.lower()}",
                    priority=900,
                    mode="normal",
                    mod_name=self.MOD_NAME,
                ),
            )

        core.subscribe(
            "MOD_ERROR",
            Handler(
                self.on_mod_error,
                name="log_mod_error",
                priority=900,
                mode="normal",
                mod_name=self.MOD_NAME,
            ),
        )

        # ── LOG_EVENT : deux handlers distincts ───────────────────────────
        #
        # 1. Écriture fichier — normal, prio haute : s'exécute toujours
        #    avant qu'un shadow plus bas ne coupe le pipeline.
        core.subscribe(
            "LOG_EVENT",
            Handler(
                self.on_log_write_file,
                name="log_write_file",
                priority=900,
                mode="normal",
                mod_name=self.MOD_NAME,
            ),
        )

        # 2. Affichage console basique — shadow, prio basse : shadowed par
        #    mod_styled_error_and_log (prio 100) si ce mod est présent.
        core.subscribe(
            "LOG_EVENT",
            Handler(
                self.on_log_console_plain,
                name="log_console_plain",
                priority=10,
                mode="shadow",
                mod_name=self.MOD_NAME,
            ),
        )

    # ── service logger ────────────────────────────────────────────────────

    def log(self, level, source, message):
        self.core.emit(
            "LOG_EVENT",
            {
                "level": level,
                "source": source,
                "message": message,
            },
        )

    # ── handlers engine ───────────────────────────────────────────────────

    def _make_engine_handler(self, event_name):
        def handler(event):
            self.log(INFO, "core", event_name)

        handler.__name__ = f"on_{event_name.lower()}"
        return handler

    def _make_engine_error_handler(self, event_name):
        def handler(event):
            self.log(ERROR, "core", f"{event_name}: {event['payload']}")

        handler.__name__ = f"on_{event_name.lower()}"
        return handler

    # ── handlers mod ─────────────────────────────────────────────────────

    def _make_mod_handler(self, event_name):
        def handler(event):
            mod = event["payload"].get("mod", "?")
            self.log(INFO, self.MOD_NAME, f"{event_name} {mod}")

        handler.__name__ = f"on_{event_name.lower()}"
        return handler

    def on_mod_error(self, event):
        mod = event["payload"].get("mod", "?")
        self.log(ERROR, self.MOD_NAME, f"MOD_ERROR in {mod}")

    # ── handlers LOG_EVENT ────────────────────────────────────────────────

    def on_log_write_file(self, event):
        p = event["payload"]
        with open("engine.log", "a", encoding="utf-8") as f:
            f.write(f"[{p['level']}] [{p['source']}] {p['message']}\n")

    def on_log_console_plain(self, event):
        p = event["payload"]
        print(f"[{p['level']}] [{p['source']}] {p['message']}")

    # ── lifecycle hooks ───────────────────────────────────────────────────

    def on_init(self, core):
        pass

    def on_ready(self, event):
        pass

    def on_shutdown(self, core):
        pass
