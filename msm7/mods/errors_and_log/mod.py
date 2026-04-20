# mods/error_and_log/mod.py

def register(ctx):
    api = ctx.mod_states.get("styled_text_api")
    if api is None:
        raise RuntimeError("error_and_log requires styled_text to be loaded first")

    def handle_warning(msg):
        api["warn"](msg)

    def handle_error(msg):
        api["error"](msg)
        raise RuntimeError(msg)

    def handle_log(msg):
        api["info"](msg)

    ctx.events.on("on_engine_warning", handle_warning)
    ctx.events.on("on_engine_error",   handle_error)
    ctx.events.on("on_engine_log",     handle_log)