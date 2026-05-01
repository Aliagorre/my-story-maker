# mods/default/mod_styled_error_and_log/main.py

from resources.__handler import Handler

MOD_NAME = "mod_styled_error_and_log"


class Mod:
    def on_load(self, core):
        self.core = core

        # shadow, prio=100 : s'intercale entre log_write_file (prio=900, normal)
        # et log_console_plain (prio=10, shadow).
        #
        # Pipeline LOG_EVENT avec les deux mods actifs :
        #   [log_write_file(900, normal)] → fichier toujours écrit
        #   [log_console_styled(100, shadow)] → affichage stylé, STOP si succès
        #   [log_console_plain(10, shadow)]   → jamais atteint si styled ok
        #
        # Sans ce mod :
        #   [log_write_file(900, normal)] → fichier
        #   [log_console_plain(10, shadow)] → affichage brut, STOP
        core.subscribe(
            "LOG_EVENT",
            Handler(
                self.on_log_console_styled,
                name="log_console_styled",
                priority=100,
                mode="shadow",
                mod_name=MOD_NAME,
            ),
        )

    def on_log_console_styled(self, event):
        p = event["payload"]
        level = p["level"]
        source = p["source"]
        message = p["message"]

        styled = self.core.get_service("styled_text")
        if styled is None:
            # Pas de service styling — lever une exception pour que le shadow
            # laisse passer au fallback (log_console_plain).
            raise RuntimeError("styled_text service unavailable")

        if level == "ERROR":
            msg = styled.style(message, color="bright_red", styles=["bold"])
            print(f"[ERROR] [{source}] {msg}")

        elif level == "WARNING":
            msg = styled.style(message, color="yellow", styles=["bold"])
            print(f"[WARNING] [{source}] {msg}")

        elif level == "CRITICAL":
            framed = styled.frame(
                styled.style(message, color="bright_red", styles=["bold", "underline"]),
                style="double",
            )
            print(framed)

        else:  # INFO, DEBUG, LOG, …
            msg = styled.style(message, color="cyan")
            print(f"[{level}] [{source}] {msg}")

    # ── lifecycle hooks ───────────────────────────────────────────────────

    def on_init(self, core):
        pass

    def on_ready(self, event):
        pass

    def on_shutdown(self, core):
        pass
