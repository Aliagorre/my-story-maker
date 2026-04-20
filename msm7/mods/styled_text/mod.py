# mods/styled_text/mod.py

def register(ctx):
    BASE_COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "italic": "\033[3m",
        "underline": "\033[4m",

        "black": "\033[30m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "orange": "\033[38;5;208m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
    }
    THEMES = {
        "default": {
            "info": "blue",
            "warn": "orange",
            "error": "red",
            "debug": "cyan",
            "title": "magenta",
            "frame": "white"
        },
        "dark": {
            "info": "cyan",
            "warn": "yellow",
            "error": "red",
            "debug": "magenta",
            "title": "white",
            "frame": "blue"
        },
        "retro": {
            "info": "green",
            "warn": "yellow",
            "error": "red",
            "debug": "cyan",
            "title": "yellow",
            "frame": "green"
        },
        "cyberpunk": {
            "info": "magenta",
            "warn": "yellow",
            "error": "red",
            "debug": "cyan",
            "title": "magenta",
            "frame": "cyan"
        }
    }

    ctx.mod_states["styled_text_theme"] = "default"

    def color(text, c):
        code = BASE_COLORS.get(c, "")
        return f"{code}{text}{BASE_COLORS['reset']}"

    def bold(text): 
        """retourne un texte en gras"""
        return f"{BASE_COLORS['bold']}{text}{BASE_COLORS['reset']}"

    def italic(text):
        """retourne un texte en italic"""
        return f"{BASE_COLORS['italic']}{text}{BASE_COLORS['reset']}"

    def underline(text):
        """retourne un texte souligné"""
        return f"{BASE_COLORS['underline']}{text}{BASE_COLORS['reset']}"

    def title(text):
        theme = THEMES[ctx.mod_states["styled_text_theme"]]
        c = theme["title"]
        return bold(color(f"== {text} ==", c))

    def frame(text):
        theme = THEMES[ctx.mod_states["styled_text_theme"]]  # FIX : bonne clé
        c = theme["frame"]
        lines = text.split("\n")
        width = max(len(l) for l in lines)
        top    = color("┌" + "─" * (width + 2) + "┐", c)
        bottom = color("└" + "─" * (width + 2) + "┘", c)
        middle = "\n".join(
            color("│ ", c) + l.ljust(width) + color(" │", c)
            for l in lines
        )
        return f"{top}\n{middle}\n{bottom}"

    def log(level, msg):
        theme = THEMES[ctx.mod_states["styled_text_theme"]]
        c = theme[level]
        print(color(f"[{level.upper()}] ", c) + msg)

    def set_theme(name):
        if name not in THEMES:
            ctx.events.emit_warning(f"styled_text: unknown theme '{name}'")
            return
        ctx.mod_states["styled_text_theme"] = name

    # ? A METTRE DANS UN MOD DE GESTION D'ERREUR ?
    def info(msg):  log("info", msg)
    def warn(msg):  log("warn", msg)
    def error(msg): log("error", msg)
    def debug(msg): log("debug", msg)

    # ============================
    #  API PUBLIQUE
    # ============================

    ctx.mod_states["styled_text_api"] = {
        "color": color,
        "bold": bold,
        "italic": italic,
        "underline": underline,
        "title": title,
        "frame": frame,

        "info": info,
        "warn": warn,
        "error": error,
        "debug": debug,

        "set_theme": set_theme
    }
