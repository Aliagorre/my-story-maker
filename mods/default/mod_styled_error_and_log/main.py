class Mod:
    def on_load(self, core):
        self.core = core
        core.subscribe("LOG_EVENT", self.on_log_event)

    def on_init(self, core): pass
    def on_ready(self, event): pass
    def on_shutdown(self, core): pass

    def on_log_event(self, event):
        payload = event["payload"]
        level = payload["level"]
        source = payload["source"]
        message = payload["message"]

        styled = self.core.get_service("styled_text")

        if styled:
            # styling complet
            if level == "ERROR":
                msg = styled.style(message, color="bright_red", styles=["bold"])
                print(f"[ERROR] [{source}] {msg}")
                return

            if level == "WARNING":
                msg = styled.style(message, color="yellow", styles=["bold"])
                print(f"[WARNING] [{source}] {msg}")
                return

            if level == "CRITICAL":
                framed = styled.frame(
                    styled.style(message, color="bright_red", styles=["bold", "underline"]),
                    style="double"
                )
                print(framed)
                return

            # INFO, DEBUG, LOG
            msg = styled.style(message, color="cyan")
            print(f"[{level}] [{source}] {msg}")
            return

        # fallback si styled_text absent
        print(f"[{level}] [{source}] {message}")


        
