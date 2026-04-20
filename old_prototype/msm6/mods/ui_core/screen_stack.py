# mods/ui_core/screen_stack.py
#
# Gestion de la pile de screens.
#
# Un "screen" est un contexte d'affichage de haut niveau :
#   - "game"    : vue principale pendant une partie
#   - "editor"  : éditeur d'aventure
#   - "pause"   : overlay pause (par-dessus "game")
#   - "menu"    : menu principal
#
# La pile permet les overlays : push("pause") affiche le menu pause
# par-dessus le jeu, pop() revient au jeu.
#
# Chaque screen a son propre WindowManager (géré dans mod.py).


class ScreenStack:
    def __init__(self):
        self._stack: list[str] = []        # pile de noms de screens
        self._registered: set[str] = set() # screens déclarés

    # ── Enregistrement ────────────────────────────────────────────

    def register(self, name: str) -> None:
        """Déclare un screen. Doit être fait avant push()."""
        self._registered.add(name)

    def is_registered(self, name: str) -> bool:
        return name in self._registered

    # ── Navigation ────────────────────────────────────────────────

    def push(self, name: str) -> None:
        """
        Active un screen en le poussant sur la pile.
        Si le screen est déjà au sommet, ne fait rien.
        """
        if name not in self._registered:
            raise ValueError(f"Screen '{name}' non enregistré.")
        if self._stack and self._stack[-1] == name:
            return
        self._stack.append(name)

    def pop(self) -> str | None:
        """
        Dépile le screen courant et revient au précédent.
        Retourne le nom du screen dépilé, ou None si la pile était vide.
        """
        if not self._stack:
            return None
        return self._stack.pop()

    def replace(self, name: str) -> None:
        """Remplace le screen courant (pop + push) sans overlay."""
        if name not in self._registered:
            raise ValueError(f"Screen '{name}' non enregistré.")
        if self._stack:
            self._stack.pop()
        self._stack.append(name)

    # ── Lecture ───────────────────────────────────────────────────

    @property
    def current(self) -> str | None:
        """Nom du screen au sommet de la pile, ou None."""
        return self._stack[-1] if self._stack else None

    @property
    def stack(self) -> list[str]:
        """Copie de la pile (bas → sommet)."""
        return list(self._stack)

    def __len__(self) -> int:
        return len(self._stack)