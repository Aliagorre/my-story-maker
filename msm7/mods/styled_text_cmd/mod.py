# mods/styled_text_cmd/mod.py
def register(ctx):
    st      = ctx.mod_states["styled_text_api"]
    cmd_api = ctx.mod_states["cmd_api"]
    THEMES  = ["default", "dark", "retro", "cyberpunk"]

    def cmd_theme(ctx, args):
        if not args:
            current = ctx.mod_states.get("styled_text_theme", "default")
            print(f"Thème actuel : {st['bold'](current)}")
            print(f"Disponibles  : {', '.join(THEMES)}")
            return
        st["set_theme"](args[0])
        print(st["color"](f"Thème → {args[0]}", "green"))

    make_completer = cmd_api["make_completer"]

    cmd_api["register_command"](
        "theme", cmd_theme, "Changer le thème d'affichage",
        completer=make_completer(lambda ctx: ctx.mod_states.get("styled_text_api", {}).get("themes", []))
    )