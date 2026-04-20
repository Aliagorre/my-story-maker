# mods/ui_core/window_manager.py
#
# Gestion des fenêtres d'un screen.
#
# Une "fenêtre" est une zone de rendu nommée avec :
#   - un callback render(ctx, surface, rect)    ← fourni par le mod
#   - un état visible / caché
#   - un raccourci clavier optionnel pour la toggler
#   - un ordre d'affichage (z-order)
#
# Le WindowManager ne rend rien.  Il stocke l'état et répond aux
# questions "quelles fenêtres sont visibles ?" et "que faire si
# l'utilisateur appuie sur F1 ?".  C'est le mod graphique (simple_ui)
# qui itère les fenêtres visibles et appelle leurs render callbacks.
#
# RENDER CALLBACK
# ───────────────
# fn(ctx, surface, rect) → None
#   ctx     : Context courant
#   surface : objet surface du toolkit (pygame.Surface, tkinter.Canvas…)
#             Peut être None si le toolkit ne l'utilise pas.
#   rect    : zone allouée à la fenêtre — tuple (x, y, w, h) ou objet
#             toolkit-specific.  Peut être None si la fenêtre gère
#             elle-même sa position.


from typing import Callable, Any


RenderFn = Callable[..., None]   # fn(ctx, surface, rect) → None


class Window:
    __slots__ = ("name", "title", "render", "visible",
                 "toggle_key", "z_order", "data")

    def __init__(self, name: str, title: str, render: RenderFn,
                 default_visible: bool, toggle_key: str | None,
                 z_order: int):
        self.name       = name
        self.title      = title
        self.render     = render
        self.visible    = default_visible
        self.toggle_key = toggle_key    # ex: "F1", "Tab", "i"
        self.z_order    = z_order
        self.data: dict = {}            # stockage libre pour le mod propriétaire


class WindowManager:
    def __init__(self):
        self._windows: dict[str, Window] = {}
        self._key_map: dict[str, str]    = {}   # key → window name
        self._focused: str | None        = None

    # ── Enregistrement ────────────────────────────────────────────

    def register(self, name: str, title: str, render: RenderFn,
                 default_visible: bool = True,
                 toggle_key: str | None = None,
                 z_order: int = 0) -> None:
        """
        Enregistre une fenêtre.

        name            : identifiant unique dans ce screen ("main", "inventory"…)
        title           : label affiché dans la barre de navigation
        render          : fn(ctx, surface, rect) → None
        default_visible : affichée dès l'entrée dans le screen ?
        toggle_key      : raccourci pour show/hide ("F1", "i", "Tab"…)
        z_order         : ordre de rendu (plus grand = par-dessus)

        Exemple depuis un mod :
            ui_api["register_window"](
                screen  = "game",
                name    = "inventory",
                title   = "Inventaire",
                render  = render_inventory,
                default_visible = False,
                toggle_key      = "F1",
            )
        """
        if name in self._windows:
            raise ValueError(f"Fenêtre '{name}' déjà enregistrée dans ce screen.")

        win = Window(name, title, render, default_visible, toggle_key, z_order)
        self._windows[name] = win

        if toggle_key:
            if toggle_key in self._key_map:
                raise ValueError(
                    f"Raccourci '{toggle_key}' déjà utilisé par "
                    f"'{self._key_map[toggle_key]}'."
                )
            self._key_map[toggle_key] = name

    # ── Contrôle de visibilité ────────────────────────────────────

    def show(self, name: str) -> None:
        self._get(name).visible = True

    def hide(self, name: str) -> None:
        self._get(name).visible = False

    def toggle(self, name: str) -> bool:
        """Retourne le nouvel état visible."""
        win = self._get(name)
        win.visible = not win.visible
        return win.visible

    def set_visible(self, name: str, visible: bool) -> None:
        self._get(name).visible = visible

    # ── Focus ─────────────────────────────────────────────────────

    def focus(self, name: str) -> None:
        """Met le focus sur une fenêtre (la rend visible si besoin)."""
        win = self._get(name)
        win.visible  = True
        self._focused = name

    @property
    def focused(self) -> str | None:
        return self._focused

    # ── Gestion des touches ───────────────────────────────────────

    def handle_key(self, key: str) -> bool:
        """
        Appelé par le mod graphique quand une touche est pressée.
        Retourne True si la touche a été consommée.

        Exemple dans simple_ui :
            if event.type == pg.KEYDOWN:
                key = pg.key.name(event.key).upper()   # "F1", "TAB"…
                if ui_core_api["handle_key"](screen, key):
                    continue   # touche consommée, ne pas propager
        """
        if key not in self._key_map:
            return False
        self.toggle(self._key_map[key])
        return True

    # ── Lecture ───────────────────────────────────────────────────

    def visible_windows(self) -> list[Window]:
        """
        Retourne les fenêtres visibles triées par z_order.
        C'est cette liste que le mod graphique itère pour rendre.

        Exemple dans simple_ui :
            for win in ui_core_api["visible_windows"](screen):
                win.render(ctx, surface, rect)
        """
        return sorted(
            (w for w in self._windows.values() if w.visible),
            key=lambda w: w.z_order
        )

    def all_windows(self) -> list[Window]:
        """Toutes les fenêtres (visibles et cachées), triées par z_order."""
        return sorted(self._windows.values(), key=lambda w: w.z_order)

    def get(self, name: str) -> Window | None:
        return self._windows.get(name)

    def key_map(self) -> dict[str, str]:
        """Copie du mapping touche → nom de fenêtre."""
        return dict(self._key_map)

    # ── Interne ───────────────────────────────────────────────────

    def _get(self, name: str) -> Window:
        if name not in self._windows:
            raise KeyError(f"Fenêtre '{name}' introuvable.")
        return self._windows[name]