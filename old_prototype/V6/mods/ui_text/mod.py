def register(ctx):
    st = ctx.mod_states.get("styled_text_api")
    if st is None:
        raise RuntimeError("text_UI requires styled_text to be loaded first")
 
    def resolve_text(ctx, text):
        """
        text peut être :
        - une string simple → retournée directement
        - une liste de { "conditions": ..., "value": ... } → premier qui passe
        """
        if isinstance(text, str):
            return text
        if isinstance(text, list):
            for entry in text:
                cond  = entry.get("conditions")
                value = entry.get("value", "")
                if cond is None or ctx.condition_engine.evaluate(cond):
                    return value
        return ""
 
    def print_node(ctx, node, choices):
        # Titre du nœud
        node_title = node.get("title", "")
        if node_title:
            print("\n" + st["title"](node_title))
        else:
            print()
 
        # Texte principal
        text = resolve_text(ctx, node.get("text", ""))
        if text:
            print(st["frame"](text))
 
        # Choix
        if choices:
            print("\n" + st["color"]("Que faire ?", "white"))
            for i, c in enumerate(choices):
                index  = st["color"](f"  {i}.", "cyan")
                label  = c.get("text", "")
                print(f"{index} {label}")
        else:
            print("\n" + st["color"]("(Aucun choix disponible)", "yellow"))
 
    ctx.mod_states["text_ui_api"] = {
        "print_node":    print_node,
        "resolve_text":  resolve_text,
    }
 
    def on_game_start(ctx):
        print(st["color"]("\n✦ Jeu démarré ✦", "green"))
 
    def on_node_enter(ctx, node):
        engine  = ctx.mod_states.get("engine")
        choices = engine.get_current_choices() if engine else []
        print_node(ctx, node, choices)
 
    def on_choice_selected(ctx, choice):
        label = choice.get("text", "")
        print(st["color"](f"\n  ➜ {label}", "cyan"))
 
    ctx.events.on("on_game_start",      on_game_start)
    ctx.events.on("on_node_enter",      on_node_enter)
    ctx.events.on("on_choice_selected", on_choice_selected)
