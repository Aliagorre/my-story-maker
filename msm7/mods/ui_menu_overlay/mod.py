# mods/ui_menu_overlay/mod.py
#
# Version pygame du menu_cli.
# Enregistre 3 screens dans ui_core : "pause", "adventures", "saves".
# Chaque screen est un overlay semi-transparent par-dessus le jeu.
#
# NAVIGATION
# ──────────
#   ↑ ↓        naviguer dans la liste
#   Entrée     valider
#   Esc        fermer / annuler
#   Clic       sélectionner / valider
#
# INTÉGRATION
# ───────────
# ui_simple appelle ui["push_screen"]("pause") quand Esc est pressé.
# Ce mod branche le render callback du screen "pause" — ui_simple
# n'a rien à modifier.
#
# Les mêmes commandes cmd que menu_cli sont exposées :
#   menu adventures  /  menu saves  /  menu pause

import json
import os
import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).parent


def _import_renderer(ctx):
    """Charge renderer depuis ui_simple/."""
    path = Path("mods/ui_simple/renderer.py")
    if not path.exists():
        raise RuntimeError("ui_menu_pygame requires mods/ui_simple/renderer.py")
    spec   = importlib.util.spec_from_file_location("ui_simple.renderer", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ui_simple.renderer"] = module
    spec.loader.exec_module(module)
    return module


def register(ctx):
    import pygame
    from core import ModLoader
    from core.errors import EngineError

    ui = ctx.mod_states.get("ui_core_api")
    if ui is None:
        raise RuntimeError("ui_menu_pygame requires ui_core")

    r = _import_renderer(ctx)
    T = r.DEFAULT_THEME

    # ── Polices (réutiliser celles de ui_simple si déjà init) ────
    def _fonts():
        if not pygame.get_init():
            return None
        f = ctx.mod_states.get("_pygame_fonts")
        if f is None:
            f = r.init_fonts()
            ctx.mod_states["_pygame_fonts"] = f
        return f

    # ================================================================
    # COMPOSANT : MenuOverlay
    # Un panneau modal centré, avec titre, liste d'items, actions.
    # ================================================================

    class MenuItem:
        __slots__ = ("label", "sublabel", "action", "destructive")
        def __init__(self, label, sublabel="", action=None, destructive=False):
            self.label       = label
            self.sublabel    = sublabel
            self.action      = action       # callable() → None
            self.destructive = destructive

    class TextInput:
        """Champ de saisie de texte minimal."""
        def __init__(self, placeholder=""):
            self.text        = ""
            self.placeholder = placeholder
            self.active      = False

        def handle_key(self, event) -> bool:
            """Retourne True si la touche a été consommée."""
            if not self.active:
                return False
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.active = False
            elif event.unicode and event.unicode.isprintable():
                self.text += event.unicode
            return True

        def draw(self, surface, font, rect, theme):
            bg  = theme["choice_hover"] if self.active else theme["choice_bg"]
            r.draw_rect(surface, bg, rect, radius=6,
                        border_color=theme["choice_index"] if self.active
                                     else theme["border"])
            txt  = self.text or self.placeholder
            col  = theme["text_fg"] if self.text else theme["key_hint_fg"]
            r.draw_text(surface, font, txt, col,
                        rect.x + 10, rect.y + rect.height // 2 - font.get_height() // 2,
                        max_width=rect.width - 20)
            if self.active:
                # Curseur clignotant
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    cx = rect.x + 10 + font.size(self.text)[0]
                    pygame.draw.line(surface, theme["text_fg"],
                                     (cx, rect.y + 6), (cx, rect.y + rect.height - 6), 1)

    class MenuOverlay:
        """
        Panneau modal centré.
        Rendu par-dessus le contenu existant via un Surface RGBA.
        """
        ITEM_H   = 42
        ITEM_GAP = 5
        PAD      = 20
        BOX_W    = 480

        def __init__(self):
            self.title    = ""
            self.items: list[MenuItem] = []
            self.selected = 0
            self.rects: list[tuple[pygame.Rect, int]] = []
            self._input: TextInput | None = None
            self._input_label: str       = ""
            self._input_cb                = None  # fn(text) → None
            self._confirm_cb              = None  # fn() → None   (confirmation)
            self._confirm_label: str      = ""
            self._message: str            = ""
            self._msg_ttl: int            = 0

        def set_items(self, title: str, items: list[MenuItem]) -> None:
            self.title    = title
            self.items    = items
            self.selected = 0
            self.rects    = []
            self._input   = None
            self._confirm_cb    = None
            self._message = ""

        def request_input(self, label: str, placeholder: str,
                          callback) -> None:
            self._input       = TextInput(placeholder)
            self._input.active = True
            self._input_label  = label
            self._input_cb     = callback

        def request_confirm(self, label: str, callback) -> None:
            self._confirm_cb    = callback
            self._confirm_label = label

        def dismiss_input(self) -> None:
            self._input      = None
            self._input_cb   = None
            self._confirm_cb = None

        def show_message(self, msg: str, ttl_frames: int = 120) -> None:
            self._message = msg
            self._msg_ttl = ttl_frames

        def handle_event(self, event) -> bool:
            """Retourne True si l'événement est consommé."""
            if event.type == pygame.KEYDOWN:
                # Champ de saisie actif
                if self._input and self._input.active:
                    if event.key == pygame.K_RETURN:
                        text = self._input.text.strip()
                        cb   = self._input_cb
                        self.dismiss_input()
                        if cb and text:
                            cb(text)
                    elif event.key == pygame.K_ESCAPE:
                        self.dismiss_input()
                    else:
                        self._input.handle_key(event)
                    return True

                # Confirmation en attente
                if self._confirm_cb:
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER,
                                     pygame.K_y):
                        cb = self._confirm_cb
                        self.dismiss_input()
                        cb()
                    elif event.key in (pygame.K_ESCAPE, pygame.K_n):
                        self.dismiss_input()
                    return True

                if event.key == pygame.K_UP:
                    self.selected = max(0, self.selected - 1)
                elif event.key == pygame.K_DOWN:
                    self.selected = min(len(self.items) - 1, self.selected + 1)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._activate(self.selected)
                elif event.key == pygame.K_ESCAPE:
                    return False   # signal : fermer l'overlay
                return True

            if event.type == pygame.MOUSEMOTION:
                for rect, i in self.rects:
                    if rect.collidepoint(event.pos):
                        self.selected = i
                return True

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                for rect, i in self.rects:
                    if rect.collidepoint(event.pos):
                        self._activate(i)
                        return True
                return False   # clic en dehors → fermer

            return False

        def _activate(self, idx: int) -> None:
            if 0 <= idx < len(self.items):
                item = self.items[idx]
                if item.action:
                    item.action()

        def draw(self, surface: pygame.Surface,
                 fonts: dict) -> None:
            w, h = surface.get_size()
            F    = fonts

            # Overlay semi-transparent
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            # Hauteur de la boîte
            extra_h  = 0
            if self._input:
                extra_h += 70
            if self._confirm_cb:
                extra_h += 60
            if self._message:
                extra_h += 30

            box_h = (self.PAD * 3 + 32            # titre
                     + len(self.items) * (self.ITEM_H + self.ITEM_GAP)
                     + extra_h)
            bx = (w - self.BOX_W) // 2
            by = (h - box_h) // 2

            # Fond de la boîte
            box_rect = pygame.Rect(bx, by, self.BOX_W, box_h)
            r.draw_rect(surface, T["header_bg"], box_rect, radius=10,
                        border_color=T["border"])

            # Titre
            r.draw_text(surface, F["title"], self.title, T["header_fg"],
                        bx + self.PAD,
                        by + self.PAD,
                        max_width=self.BOX_W - self.PAD * 2)
            pygame.draw.line(surface, T["border"],
                             (bx, by + self.PAD + 30),
                             (bx + self.BOX_W, by + self.PAD + 30), 1)

            # Items
            y = by + self.PAD * 2 + 30
            self.rects.clear()
            for i, item in enumerate(self.items):
                rect = pygame.Rect(bx + self.PAD, y,
                                   self.BOX_W - self.PAD * 2, self.ITEM_H)
                bg = T["choice_hover"] if i == self.selected else T["choice_bg"]
                if item.destructive and i == self.selected:
                    bg = (80, 20, 20)
                r.draw_rect(surface, bg, rect, radius=6,
                            border_color=T["border"])

                col = (220, 100, 100) if item.destructive else T["choice_fg"]
                r.draw_text(surface, F["normal"], item.label, col,
                            rect.x + 12,
                            rect.y + self.ITEM_H // 2 - F["normal"].get_height() // 2,
                            max_width=rect.width - 16)

                if item.sublabel:
                    sl = F["small"].render(item.sublabel, True, T["key_hint_fg"])
                    surface.blit(sl, (rect.right - sl.get_width() - 10,
                                      rect.y + self.ITEM_H // 2 - sl.get_height() // 2))

                self.rects.append((rect, i))
                y += self.ITEM_H + self.ITEM_GAP

            # Champ de saisie
            if self._input:
                lbl = F["small"].render(self._input_label, True, T["key_hint_fg"])
                surface.blit(lbl, (bx + self.PAD, y + 6))
                inp_rect = pygame.Rect(bx + self.PAD, y + 24,
                                       self.BOX_W - self.PAD * 2, 34)
                self._input.draw(surface, F["normal"], inp_rect, T)
                y += 70

            # Demande de confirmation
            if self._confirm_cb:
                pygame.draw.line(surface, T["border"],
                                 (bx, y), (bx + self.BOX_W, y), 1)
                msg = F["normal"].render(
                    self._confirm_label + "  [Entrée] Confirmer  [Esc] Annuler",
                    True, (210, 120, 120)
                )
                surface.blit(msg, (bx + self.PAD, y + 10))
                y += 60

            # Message temporaire
            if self._msg_ttl > 0:
                self._msg_ttl -= 1
                is_err = self._message.startswith("✗")
                fg = T["message_err_fg"] if is_err else T["message_ok_fg"]
                ms = F["small"].render(self._message, True, fg)
                surface.blit(ms, (bx + self.PAD, y + 6))
                if self._msg_ttl == 0:
                    self._message = ""

    # ================================================================
    # ÉTAT PAR SCREEN
    # ================================================================

    _overlays: dict[str, MenuOverlay] = {}

    def _overlay(name: str) -> MenuOverlay:
        if name not in _overlays:
            _overlays[name] = MenuOverlay()
        return _overlays[name]

    # ================================================================
    # HELPERS MÉTIER
    # ================================================================

    def _list_saves(adventure_name=None):
        saves_dir = Path("saves")
        if not saves_dir.exists():
            return []
        files = [f for f in saves_dir.iterdir() if f.suffix == ".json"]
        if adventure_name:
            files = [f for f in files if f.stem.startswith(f"{adventure_name}_")]
        return sorted(files)

    def _do_start(folder: str) -> None:
        ctx.reset()
        loader = ModLoader(ctx)
        loader.load_mods_from_folder("mods")
        ctx.mod_states["current_adventure"] = folder
        loader.load_single_mod_from_dir(Path(f"adventures/{folder}"))
        engine = ctx.mod_states.get("engine")
        if engine is None:
            return
        engine.start("start")

    def _do_load(save_path: Path) -> None:
        engine = ctx.mod_states.get("engine")
        if engine is None:
            # Déduire l'aventure depuis le nom du fichier
            parts  = save_path.stem.split("_", 1)
            folder = parts[0] if len(parts) > 1 else None
            if folder and Path(f"adventures/{folder}").exists():
                _do_start(folder)
                engine = ctx.mod_states.get("engine")
            if engine is None:
                return
        try:
            engine.load_game(str(save_path))
        except EngineError:
            pass

    # ================================================================
    # SCREEN : pause
    # ================================================================

    def _build_pause_items() -> list[MenuItem]:
        adventure_name = ctx.mod_states.get("current_adventure", "game")
        ov = _overlay("pause")

        def _resume():
            ui["pop_screen"]()

        def _save():
            ov.request_input(
                "Nom de la sauvegarde", f"{adventure_name}_",
                lambda name: _do_save(name)
            )

        def _do_save(name: str) -> None:
            engine = ctx.mod_states.get("engine")
            if engine is None:
                return
            os.makedirs("saves", exist_ok=True)
            try:
                engine.save_game(f"saves/{name}.json")
                ov.show_message("✓ Sauvegardé")
            except Exception as e:
                ov.show_message(f"✗ {e}")

        def _load():
            ui["pop_screen"]()
            _open_saves()

        def _quit():
            ov.request_confirm(
                "Quitter l'aventure ?",
                lambda: _do_quit()
            )

        def _do_quit():
            ui["pop_screen"]()
            ctx.reset()
            loader = ModLoader(ctx)
            loader.load_mods_from_folder("mods")

        return [
            MenuItem("Reprendre",             action=_resume),
            MenuItem("Sauvegarder",           action=_save),
            MenuItem("Charger une sauvegarde",action=_load),
            MenuItem("Quitter l'aventure",    action=_quit, destructive=True),
        ]

    def _render_pause(ctx, surface, rect):
        fonts = _fonts()
        if fonts is None:
            return
        ov = _overlay("pause")
        if not ov.items:
            ov.set_items("PAUSE", _build_pause_items())
        ov.draw(surface, fonts)

    # ================================================================
    # SCREEN : adventures
    # ================================================================

    def _build_adventure_items() -> list[MenuItem]:
        adv_dir = Path("adventures")
        items   = []
        if adv_dir.exists():
            for d in sorted(adv_dir.iterdir()):
                if not d.is_dir():
                    continue
                mj = d / "mod.json"
                if not mj.exists():
                    continue
                try:
                    meta = json.loads(mj.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                folder = d.name
                name   = meta.get("name", folder)
                desc   = meta.get("description", "")
                items.append(MenuItem(
                    label    = name,
                    sublabel = desc[:40] + "…" if len(desc) > 40 else desc,
                    action   = (lambda f: lambda: _start_and_close(f))(folder),
                ))
        items.append(MenuItem("Annuler", action=lambda: ui["pop_screen"]()))
        return items

    def _start_and_close(folder: str) -> None:
        ui["pop_screen"]()
        _do_start(folder)

    def _render_adventures(ctx, surface, rect):
        fonts = _fonts()
        if fonts is None:
            return
        ov = _overlay("adventures")
        if not ov.items:
            ov.set_items("Aventures disponibles", _build_adventure_items())
        ov.draw(surface, fonts)

    # ================================================================
    # SCREEN : saves
    # ================================================================

    def _build_save_items(saves: list[Path]) -> list[MenuItem]:
        items = []
        for save in saves:
            s = save   # capture
            items.append(MenuItem(
                label  = s.stem,
                action = (lambda p: lambda: _load_and_close(p))(s),
            ))
        items.append(MenuItem("Annuler", action=lambda: ui["pop_screen"]()))
        return items

    def _load_and_close(save_path: Path) -> None:
        ui["pop_screen"]()
        _do_load(save_path)

    def _render_saves(ctx, surface, rect):
        fonts = _fonts()
        if fonts is None:
            return
        ov    = _overlay("saves")
        adv   = ctx.mod_states.get("current_adventure")
        saves = _list_saves(adv)
        label = f"Sauvegardes — {adv}" if adv else "Sauvegardes"
        if not ov.items:
            if saves:
                ov.set_items(label, _build_save_items(saves))
            else:
                ov.set_items(label, [
                    MenuItem("(aucune sauvegarde)"),
                    MenuItem("Annuler", action=lambda: ui["pop_screen"]()),
                ])
        ov.draw(surface, fonts)

    # ================================================================
    # ENREGISTREMENT DES SCREENS DANS ui_core
    # ================================================================

    for screen_name, title, render_fn in [
        ("pause",      "Pause",               _render_pause),
        ("adventures", "Aventures",            _render_adventures),
        ("saves",      "Sauvegardes",          _render_saves),
    ]:
        if not ui["screen_stack"]() or screen_name not in ui["screen_stack"]():
            ui["register_screen"](screen_name, title=title)
        ui["register_window"](
            screen          = screen_name,
            name            = "overlay",
            title           = "",
            render          = render_fn,
            default_visible = True,
            z_order         = 100,
        )

    # ================================================================
    # ROUTING DES ÉVÉNEMENTS pygame vers les overlays
    # ================================================================
    # ui_simple appelle handle_key() pour les touches — mais les clics
    # et la navigation dans les overlays nécessitent un handler
    # d'événements complet.  On s'abonne à on_ui_event si disponible,
    # sinon ui_simple devra appeler handle_menu_event() directement.

    def handle_menu_event(event) -> bool:
        """
        Appelé par ui_simple pour chaque événement pygame quand un
        screen overlay est actif.
        Retourne True si l'événement est consommé.
        """
        screen = ui["current_screen"]()
        if screen not in _overlays:
            return False
        ov = _overlay(screen)
        consumed = ov.handle_event(event)
        if not consumed and event.type == pygame.KEYDOWN \
                and event.key == pygame.K_ESCAPE:
            # Escape non consommé = fermer l'overlay
            _overlays[screen].set_items("", [])   # reset pour la prochaine ouverture
            ui["pop_screen"]()
            return True
        return consumed

    # ================================================================
    # OUVERTURE DES MENUS
    # ================================================================

    def _open_pause() -> None:
        _overlay("pause").set_items("PAUSE", _build_pause_items())
        ui["push_screen"]("pause")

    def _open_adventures() -> None:
        _overlay("adventures").set_items(
            "Aventures disponibles", _build_adventure_items()
        )
        ui["push_screen"]("adventures")

    def _open_saves() -> None:
        adv   = ctx.mod_states.get("current_adventure")
        saves = _list_saves(adv)
        label = f"Sauvegardes — {adv}" if adv else "Sauvegardes"
        _overlay("saves").set_items(
            label, _build_save_items(saves) if saves else [
                MenuItem("(aucune sauvegarde)"),
                MenuItem("Annuler", action=lambda: ui["pop_screen"]()),
            ]
        )
        ui["push_screen"]("saves")

    # ================================================================
    # COMMANDES CMD
    # ================================================================

    cmd_api = ctx.mod_states.get("cmd_api")
    if cmd_api:
        cmd_api["register_command"](
            "menu.adventures", lambda ctx, a: _open_adventures(),
            "Choisir et lancer une aventure"
        )
        cmd_api["register_command"](
            "menu.saves", lambda ctx, a: _open_saves(),
            "Gérer les sauvegardes"
        )
        cmd_api["register_command"](
            "menu.pause", lambda ctx, a: _open_pause(),
            "Menu pause"
        )

    # ================================================================
    # API PUBLIQUE
    # ================================================================

    ctx.mod_states["menu_api"] = {
        "open_pause":      _open_pause,
        "open_adventures": _open_adventures,
        "open_saves":      _open_saves,
        "handle_event":    handle_menu_event,
    }