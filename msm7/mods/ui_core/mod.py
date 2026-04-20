# mods/ui_core/mod.py
#
# Gestion centralisée des screens et des fenêtres.
#
# CE QUE CE MOD FAIT
# ──────────────────
# - Maintient une pile de screens (ScreenStack)
# - Maintient un WindowManager par screen
# - Expose ui_core_api pour que les autres mods enregistrent
#   leurs screens et fenêtres
# - Route les touches vers le bon WindowManager
# - NE REND RIEN — toolkit-agnostic
#
# CE QUE CE MOD NE FAIT PAS
# ─────────────────────────
# - Pas de pygame, tkinter, Qt…
# - Pas de input()
# - Pas de threading
#
# COMMENT UN MOD ENREGISTRE UNE FENÊTRE
# ──────────────────────────────────────
#
#   def register(ctx):
#       ui = ctx.mod_states.get("ui_core_api")
#
#       # 1. Déclarer le screen si pas déjà fait
#       ui["register_screen"]("game", title="Jeu")
#
#       # 2. Déclarer la fenêtre avec son callback de rendu
#       def render_inventory(ctx, surface, rect):
#           # surface et rect sont fournis par le mod graphique (simple_ui…)
#           # Dessiner l'inventaire ici.
#           pass
#
#       ui["register_window"](
#           screen          = "game",
#           name            = "inventory",
#           title           = "Inventaire",
#           render          = render_inventory,
#           default_visible = False,   # cachée par défaut
#           toggle_key      = "F1",    # F1 pour afficher/cacher
#           z_order         = 10,      # par-dessus la vue principale
#       )
#
#       # 3. Naviguer entre screens depuis n'importe où
#       ui["push_screen"]("pause")    # overlay
#       ui["pop_screen"]()            # retour
#       ui["replace_screen"]("menu")  # sans empilement
#
# COMMENT LE MOD GRAPHIQUE UTILISE UI_CORE
# ─────────────────────────────────────────
#
#   def render_loop(ctx, render_lock):
#       ui = ctx.mod_states["ui_core_api"]
#       while True:
#           # Rendu de toutes les fenêtres visibles du screen courant
#           screen = ui["current_screen"]()
#           if screen:
#               for win in ui["visible_windows"](screen):
#                   win.render(ctx, surface, rect)
#
#           # Routage des touches
#           for event in get_events():
#               if event.is_keydown:
#                   if not ui["handle_key"](screen, event.key):
#                       pass  # touche non consommée → propager
#

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).parent


def _import_local(name: str, filename: str):
    """Importe un fichier depuis le même dossier sans polluer sys.path."""
    path      = _HERE / filename
    full_name = f"ui_core.{name}"
    spec      = importlib.util.spec_from_file_location(full_name, path)
    module    = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


def register(ctx):
    ss_mod = _import_local("screen_stack",   "screen_stack.py")
    wm_mod = _import_local("window_manager", "window_manager.py")

    ScreenStack   = ss_mod.ScreenStack
    WindowManager = wm_mod.WindowManager

    screen_stack = ScreenStack()
    managers: dict[str, WindowManager] = {}   # screen_name → WindowManager

    # ── Helpers internes ─────────────────────────────────────────

    def _wm(screen: str) -> WindowManager:
        if screen not in managers:
            raise KeyError(f"Screen '{screen}' non enregistré.")
        return managers[screen]

    # ── API : screens ─────────────────────────────────────────────

    def register_screen(name: str, title: str = "",
                        default: bool = False) -> None:
        """
        Déclare un screen.
        default=True → poussé automatiquement sur la pile.
        """
        screen_stack.register(name)
        managers[name] = WindowManager()
        ctx.mod_states.setdefault("ui_screens", {})[name] = {"title": title}
        if default:
            screen_stack.push(name)

    def push_screen(name: str) -> None:
        """Passe au screen 'name' en l'empilant (overlay)."""
        screen_stack.push(name)
        ctx.events.emit("on_screen_change", ctx, screen_stack.current)

    def pop_screen() -> str | None:
        """Revient au screen précédent."""
        popped = screen_stack.pop()
        ctx.events.emit("on_screen_change", ctx, screen_stack.current)
        return popped

    def replace_screen(name: str) -> None:
        """Remplace le screen courant sans empilement."""
        screen_stack.replace(name)
        ctx.events.emit("on_screen_change", ctx, screen_stack.current)

    def current_screen() -> str | None:
        return screen_stack.current

    def screen_stack_list() -> list[str]:
        return screen_stack.stack

    # ── API : fenêtres ────────────────────────────────────────────

    def register_window(screen: str, name: str, title: str,
                        render,
                        default_visible: bool = True,
                        toggle_key: str | None = None,
                        z_order: int = 0) -> None:
        _wm(screen).register(name, title, render,
                              default_visible, toggle_key, z_order)

    def visible_windows(screen: str):
        """
        Retourne la liste des Window visibles du screen, triées par z_order.
        Appelé à chaque frame par le mod graphique.
        """
        return _wm(screen).visible_windows()

    def all_windows(screen: str):
        return _wm(screen).all_windows()

    def show_window(screen: str, name: str) -> None:
        _wm(screen).show(name)

    def hide_window(screen: str, name: str) -> None:
        _wm(screen).hide(name)

    def toggle_window(screen: str, name: str) -> bool:
        return _wm(screen).toggle(name)

    def focus_window(screen: str, name: str) -> None:
        _wm(screen).focus(name)

    def get_window(screen: str, name: str):
        return _wm(screen).get(name)

    # ── API : routing des touches ─────────────────────────────────

    def handle_key(screen: str, key: str) -> bool:
        """
        Tente de router 'key' vers le WindowManager du screen.
        Retourne True si la touche a été consommée.

        Appelé par le mod graphique dans sa boucle d'événements.
        La normalisation de la touche (majuscules, nom…) est à la
        charge du mod graphique qui connaît son toolkit.

        Exemple avec pygame :
            key_name = pygame.key.name(event.key).upper()
            # "f1", "tab", "i" → "F1", "TAB", "I"
            consumed = ui["handle_key"](current_screen(), key_name)
        """
        if screen is None:
            return False
        return _wm(screen).handle_key(key)

    def key_map(screen: str) -> dict[str, str]:
        """Retourne le mapping touche → nom de fenêtre du screen."""
        return _wm(screen).key_map()

    # ── Enregistrement des events ─────────────────────────────────

    ctx.events.register_event("on_screen_change")
    # on_screen_change(ctx, new_screen_name | None)
    # Émis par push/pop/replace. Le mod graphique peut s'y abonner
    # pour adapter son layout au nouveau screen.

    # ── Exposition de l'API ───────────────────────────────────────

    ctx.mod_states["ui_core_api"] = {
        # screens
        "register_screen":  register_screen,
        "push_screen":      push_screen,
        "pop_screen":       pop_screen,
        "replace_screen":   replace_screen,
        "current_screen":   current_screen,
        "screen_stack":     screen_stack_list,

        # fenêtres
        "register_window":  register_window,
        "visible_windows":  visible_windows,
        "all_windows":      all_windows,
        "show_window":      show_window,
        "hide_window":      hide_window,
        "toggle_window":    toggle_window,
        "focus_window":     focus_window,
        "get_window":       get_window,

        # routing touches
        "handle_key":       handle_key,
        "key_map":          key_map,
    }