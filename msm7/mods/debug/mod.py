# mods/debug/mod.py

def register(ctx):
    st = ctx.mod_states.get("styled_text_api")
    if st is None:
        raise RuntimeError("debug requires styled_text to be loaded first")

    # ----------------------------------------------------------------
    # pretty_print stylisée
    # ----------------------------------------------------------------

    # Palette sémantique construite depuis styled_text
    def _key(s):     return st["color"](s, "cyan")
    def _str(s):     return st["color"](s, "green")
    def _number(s):  return st["color"](s, "yellow")
    def _bool(s):    return st["color"](s, "magenta")
    def _none(s):    return st["color"](s, "red")
    def _bracket(s): return st["color"](s, "white")
    def _func(s):    return st["color"](s, "blue")

    def _format_value(val) -> str:
        """Formate une valeur simple en string colorée (sans newline)."""
        if isinstance(val, bool):   return _bool(repr(val))
        if isinstance(val, (int, float)): return _number(repr(val))
        if isinstance(val, str):    return _str(repr(val))
        if val is None:             return _none("None")
        if callable(val):           return _func(f"<fn {getattr(val, '__name__', '?')}>")
        return repr(val)  # fallback : pas de couleur connue

    def _is_simple(val) -> bool:
        """True si la valeur tient sur une ligne (pas de dict/list/tuple imbriqué)."""
        return not isinstance(val, (dict, list, tuple))

    def pretty_print(obj, indent=0, _inline=False):
        """
        Affiche obj avec indentation, alignement des clés et coloration.

        _inline=True : ne préfixe pas avec l'indentation (la clé est déjà sur la ligne).
        """
        space     = "  " * indent
        space_in  = "  " * (indent + 1)

        # --- callable (lambda, fonction) ---
        if callable(obj) and not isinstance(obj, (dict, list, tuple)):
            line = _func(f"<fn {getattr(obj, '__name__', '?')}>")
            print(line if _inline else space + line)
            return

        # --- dictionnaire ---
        if isinstance(obj, dict):
            if not obj:
                line = _bracket("{}")
                print(line if _inline else space + line)
                return

            # Séparer les clés simples (valeur sur une ligne) des clés complexes
            simple  = {k: v for k, v in obj.items() if _is_simple(v)}
            complex_ = {k: v for k, v in obj.items() if not _is_simple(v)}

            max_key_len = max(len(str(k)) for k in obj.keys())

            opening = _bracket("{")
            print(opening if _inline else space + opening)

            # Valeurs simples : alignées sur une seule ligne
            for key in sorted(simple.keys()):
                key_str = _key(str(key).ljust(max_key_len))
                print(space_in + f"{key_str}  {_format_value(simple[key])}")

            # Valeurs complexes : récursion
            for key in sorted(complex_.keys()):
                key_str = _key(str(key).ljust(max_key_len))
                print(space_in + f"{key_str}  ", end="")
                pretty_print(complex_[key], indent + 1, _inline=True)

            print(space + _bracket("}"))
            return

        # --- liste ---
        if isinstance(obj, list):
            if not obj:
                line = _bracket("[]")
                print(line if _inline else space + line)
                return

            opening = _bracket("[")
            print(opening if _inline else space + opening)
            for item in obj:
                if _is_simple(item):
                    print(space_in + _format_value(item))
                else:
                    pretty_print(item, indent + 1)
            print(space + _bracket("]"))
            return

        # --- tuple ---
        if isinstance(obj, tuple):
            if not obj:
                line = _bracket("()")
                print(line if _inline else space + line)
                return

            opening = _bracket("(")
            print(opening if _inline else space + opening)
            for item in obj:
                if _is_simple(item):
                    print(space_in + _format_value(item))
                else:
                    pretty_print(item, indent + 1)
            print(space + _bracket(")"))
            return

        # --- valeur simple ---
        line = _format_value(obj)
        print(line if _inline else space + line)

    # ----------------------------------------------------------------
    # Commandes de debug
    # ----------------------------------------------------------------

    cmd_api = ctx.mod_states.get("cmd_api")
    if cmd_api is None:
        raise RuntimeError("debug requires cmd to be loaded first")

    reg = cmd_api["register_command"]

    def cmd_state(ctx, args):
        print("\n" + st["title"]("State"))
        if ctx.state:
            pretty_print(ctx.state)
        else:
            print(st["color"]("  (vide)", "white"))
        print()

    def cmd_mod_states(ctx, args):
        print("\n" + st["title"]("Mod States"))
        if ctx.mod_states:
            pretty_print(ctx.mod_states)
        else:
            print(st["color"]("  (vide)", "white"))
        print()

    def cmd_events(ctx, args):
        print("\n" + st["title"]("Events enregistrés"))
        events = ctx.events._events
        for name, handlers in sorted(events.items()):
            count   = len(handlers)
            c       = "green" if count > 0 else "white"
            h_label = st["color"](f"({count} handler{'s' if count != 1 else ''})", c)
            print(f"  {st['color'](name, 'cyan')}  {h_label}")
        print()

    def cmd_mods(ctx, args):
        print("\n" + st["title"]("Mods chargés"))
        mods = ctx.mod_states.get("mods_loaded", [])
        if mods:
            for m in mods:
                print(f"  {st['color']('✓', 'green')} {m}")
        else:
            print(st["color"]("  (aucun)", "white"))
        print()

    def cmd_node(ctx, args):
        print("\n" + st["title"]("Node courant"))
        engine = ctx.mod_states.get("engine")
        if engine is None:
            print(st["color"]("  Aucun engine actif.", "red"))
            print()
            return
        node = engine.get_current_node()
        pretty_print(node)
        print()

    def cmd_ctx(ctx, args):
        """Tout en une fois."""
        cmd_state(ctx, args)
        cmd_mod_states(ctx, args)
        cmd_events(ctx, args)
        cmd_mods(ctx, args)
        cmd_node(ctx, args)

    reg("debug.state",      cmd_state,      "Afficher ctx.state")
    reg("debug.mod_states", cmd_mod_states, "Afficher ctx.mod_states")
    reg("debug.events",     cmd_events,     "Lister les events et leurs handlers")
    reg("debug.mods",       cmd_mods,       "Lister les mods chargés")
    reg("debug.node",       cmd_node,       "Afficher le node courant")
    reg("debug.ctx",        cmd_ctx,        "Afficher tout le contexte")

    # ----------------------------------------------------------------
    # API publique
    # ----------------------------------------------------------------

    ctx.mod_states["debug_api"] = {
        "pretty_print": pretty_print,
    }
    