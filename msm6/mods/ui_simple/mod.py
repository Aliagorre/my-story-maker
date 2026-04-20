# mods/simple_ui/mod.py
#
# Adaptateur pygame pour ui_core.
# Gère la fenêtre, les événements, le layout.
# Ne contient aucune logique de jeu.
#
# CONTRAT RENDER CALLBACK (pour les mods qui ajoutent des fenêtres)
# ──────────────────────────────────────────────────────────────────
# fn(ctx, surface, rect) → None
#   surface : pygame.Surface de la fenêtre principale
#   rect    : pygame.Rect alloué à cette fenêtre
#
# Pour du texte simple, écrire dans win.data["content"] suffit —
# simple_ui le lit et le passe à WindowPanel.
# Pour un rendu custom (carte, inventaire graphique…), dessiner
# directement sur surface dans le rect fourni.
#
# Exemple minimal :
#   def render_inventory(ctx, surface, rect):
#       win = ui["get_window"]("game", "inventory")
#       win.data["content"] = "\n".join(ctx.state.get("inventory", []))

import importlib.util
import sys
from contextlib import nullcontext
from pathlib import Path

_HERE = Path(__file__).parent


def _import_local(name: str, filename: str):
    path      = _HERE / filename
    full_name = f"simple_ui.{name}"
    spec      = importlib.util.spec_from_file_location(full_name, path)
    module    = importlib.util.module_from_spec(spec)
    sys.modules[full_name] = module
    spec.loader.exec_module(module)
    return module


def register(ctx):
    # ── Dépendances ───────────────────────────────────────────────
    try:
        import pygame
    except ImportError:
        raise RuntimeError(
            "simple_ui: pygame non installé — pip install pygame"
        )

    ui = ctx.mod_states.get("ui_core_api")
    if ui is None:
        raise RuntimeError("simple_ui requires ui_core")

    # ── Charger les primitives ────────────────────────────────────
    r_mod   = _import_local("renderer", "renderer.py")

    # ── État d'affichage ─────────────────────────────────────────
    display = {
        "adventure_name": "",
        "node_text":      "",
        "choices":        [],
        "selected":       -1,
        "message":        None,
        "_msg_ttl":       0,
        "_image":         None,   # pygame.Surface | None (image du nœud)
    }

    # ── Screen "game" par défaut ──────────────────────────────────
    if not ui["screen_stack"]():
        ui["register_screen"]("game", title="Jeu", default=True)

    def render_main(ctx, surface, rect):
        """
        Render callback de la fenêtre principale.
        Écrit dans win.data pour que la boucle puisse le lire.
        Pour un rendu custom, dessiner sur surface dans rect.
        """
        win = ui["get_window"]("game", "main")
        if win is None:
            return
        win.data["content"] = display["node_text"]
        win.data["image"]   = display.get("_image")

    if not ui["all_windows"]("game"):
        ui["register_window"](
            screen="game", name="main", title="",
            render=render_main,
            default_visible=True, z_order=0,
        )

    # ── Handlers engine ──────────────────────────────────────────

    def _resolve_text(raw) -> str:
        if isinstance(raw, str):
            return raw
        if isinstance(raw, list):
            for entry in raw:
                cond  = entry.get("conditions")
                value = entry.get("value", "")
                if cond is None or ctx.condition_engine.evaluate(cond):
                    return value
        return ""

    def on_game_start(ctx):
        meta = ctx.mod_states.get("current_adventure_meta", {})
        display["adventure_name"] = meta.get("name", "")
        display["selected"]       = -1

    def on_node_enter(ctx, node):
        engine = ctx.mod_states.get("engine")
        display["node_text"] = _resolve_text(node.get("text", ""))
        display["choices"]   = engine.get_current_choices() if engine else []
        display["selected"]  = -1
        display["_image"]    = None   # un futur mod image peut le setter

        # Reset scroll de la fenêtre principale
        panels = ctx.mod_states.get("_ui_panels", {})
        if "main" in panels:
            panels["main"].reset_scroll()

    def on_choice_selected(ctx, choice):
        display["selected"] = -1

    def on_save(ctx):
        display["message"]  = "✓ Sauvegardé"
        display["_msg_ttl"] = 120

    ctx.events.on("on_game_start",      on_game_start)
    ctx.events.on("on_node_enter",      on_node_enter)
    ctx.events.on("on_choice_selected", on_choice_selected)
    ctx.events.on("on_save",            on_save)

    # ── Boucle principale ─────────────────────────────────────────

    def ui_run(ctx, render_lock=None):
        lock = render_lock if render_lock is not None else nullcontext()

        pygame.init()
        screen_surf = pygame.display.set_mode((960, 640), pygame.RESIZABLE)
        pygame.display.set_caption(display["adventure_name"] or "Adventure")
        clock = pygame.time.Clock()

        theme   = r_mod.DEFAULT_THEME
        fonts   = r_mod.init_fonts()

        # Composants UI
        header   = r_mod.HeaderBar(theme, fonts)
        status   = r_mod.StatusBar(theme, fonts)
        choices  = r_mod.ChoiceBar(theme, fonts)

        # Un WindowPanel par fenêtre enregistrée (créés à la demande)
        panels: dict[str, r_mod.WindowPanel] = {}
        ctx.mod_states["_ui_panels"] = panels

        def _get_panel(name: str) -> r_mod.WindowPanel:
            if name not in panels:
                panels[name] = r_mod.WindowPanel(theme, fonts)
            return panels[name]

        running = True
        while running:
            w, h = screen_surf.get_size()

            # ── Layout ───────────────────────────────────────────
            HEADER_H = header.height
            STATUS_H = status.height
            n_ch     = len(display["choices"])
            CHOICE_H = choices.height(n_ch)

            content_top = HEADER_H
            content_bot = h - STATUS_H
            text_bot    = content_bot - CHOICE_H
            text_h      = text_bot - content_top

            current_screen = ui["current_screen"]()

            # ── Appel des render callbacks ────────────────────────
            if current_screen:
                with lock:
                    for win in ui["visible_windows"](current_screen):
                        win.render(ctx, screen_surf, None)

            # ── Rendu ─────────────────────────────────────────────
            screen_surf.fill(theme["bg"])

            if current_screen:
                visible = ui["visible_windows"](current_screen)
                all_w   = ui["all_windows"](current_screen)

                # Header
                header.draw(screen_surf,
                            pygame.Rect(0, 0, w, HEADER_H),
                            display["adventure_name"],
                            current_screen,
                            all_w)

                # Fenêtres visibles — layout
                if len(visible) == 1:
                    # Plein écran
                    win = visible[0]
                    p   = _get_panel(win.name)
                    p.draw(screen_surf,
                           pygame.Rect(0, content_top, w, text_h),
                           win.title,
                           win.data.get("content", ""),
                           win.data.get("image"))
                else:
                    # Split : principale à gauche (62%), secondaires à droite
                    SPLIT   = int(w * 0.62)
                    SIDE_W  = w - SPLIT - 1
                    side_n  = len(visible) - 1
                    side_h  = text_h // max(side_n, 1)

                    # Fenêtre principale
                    win = visible[0]
                    p   = _get_panel(win.name)
                    p.draw(screen_surf,
                           pygame.Rect(0, content_top, SPLIT, text_h),
                           win.title,
                           win.data.get("content", ""),
                           win.data.get("image"))

                    # Séparateur vertical
                    pygame.draw.line(screen_surf, theme["border"],
                                     (SPLIT, content_top),
                                     (SPLIT, text_bot), 1)

                    # Fenêtres secondaires
                    for i, win in enumerate(visible[1:]):
                        sy = content_top + i * side_h
                        sh = min(side_h, text_bot - sy)
                        if sh <= 0:
                            break
                        p = _get_panel(win.name)
                        p.draw(screen_surf,
                               pygame.Rect(SPLIT + 1, sy, SIDE_W, sh),
                               win.title,
                               win.data.get("content", ""),
                               win.data.get("image"))
                        if i < side_n - 1:
                            pygame.draw.line(screen_surf, theme["border"],
                                             (SPLIT + 1, sy + sh),
                                             (w, sy + sh), 1)

                # Choix
                if n_ch:
                    choices.draw(screen_surf,
                                 pygame.Rect(0, text_bot, w, CHOICE_H),
                                 display["choices"],
                                 selected=display["selected"])

                # Hints
                km     = ui["key_map"](current_screen)
                hints  = [f"{k}:{ui['get_window'](current_screen, v).title}"
                          for k, v in km.items()
                          if ui["get_window"](current_screen, v)]
                hints += ["F5 save", "Esc pause"]

                # Status bar
                msg = display["message"] if display["_msg_ttl"] > 0 else None
                status.draw(screen_surf,
                            pygame.Rect(0, h - STATUS_H, w, STATUS_H),
                            msg or "",
                            hints)

            pygame.display.flip()

            # ── Tick message ──────────────────────────────────────
            if display["_msg_ttl"] > 0:
                display["_msg_ttl"] -= 1

            # ── Événements ────────────────────────────────────────
            for event in pygame.event.get():
                running = _handle_event(
                    event, current_screen, panels,
                    choices, lock, ctx, pygame
                )
                if not running:
                    break

            clock.tick(60)

        # ── Sortie ────────────────────────────────────────────────
        ctx.mod_states.pop("_ui_panels", None)
        pygame.quit()

    # ── Gestion des événements ────────────────────────────────────

    def _handle_event(event, current_screen, panels,
                      choice_bar, lock, ctx, pygame) -> bool:
        from core.errors import EngineError
        menu_api = ctx.mod_states.get("menu_api")
        if menu_api and ui["current_screen"]() in ("pause", "adventures", "saves"):
            if menu_api["handle_event"](event):
                return True   # événement consommé par le menu

        if event.type == pygame.QUIT:
            return False

        # ── Souris ────────────────────────────────────────────────
        if event.type == pygame.MOUSEMOTION:
            choice_bar.update_hover(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                choice_bar.set_active(event.pos)
            elif event.button == 4:   # molette haut
                _scroll_main(panels, -3)
            elif event.button == 5:   # molette bas
                _scroll_main(panels, 3)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            idx = choice_bar.get_clicked(event.pos)
            if idx is not None:
                with lock:
                    _choose(idx, ctx)

        # ── Clavier ───────────────────────────────────────────────
        elif event.type == pygame.KEYDOWN:
            key = event.key

            # Chiffres → choix direct
            if pygame.K_1 <= key <= pygame.K_9:
                idx = key - pygame.K_1
                if idx < len(display["choices"]):
                    with lock:
                        _choose(idx, ctx)

            # Flèches → navigation choix ou scroll
            elif key == pygame.K_UP:
                if display["choices"]:
                    n = len(display["choices"])
                    display["selected"] = (display["selected"] - 1) % n \
                        if display["selected"] > 0 else n - 1
                else:
                    _scroll_main(panels, -3)

            elif key == pygame.K_DOWN:
                if display["choices"]:
                    display["selected"] = (
                        (display["selected"] + 1) % len(display["choices"])
                    )
                else:
                    _scroll_main(panels, 3)

            elif key == pygame.K_PAGEUP:
                _scroll_main(panels, -10)

            elif key == pygame.K_PAGEDOWN:
                _scroll_main(panels, 10)

            # Entrée → valider le choix surligné
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                sel = display["selected"]
                if 0 <= sel < len(display["choices"]):
                    with lock:
                        _choose(sel, ctx)

            # Escape → pause
            elif key == pygame.K_ESCAPE:
                menu_api = ctx.mod_states.get("menu_api")
                if menu_api:
                    menu_api["open_pause"]()
                with lock:
                    try:
                        ctx.events.emit("on_cli_input", ctx, "pause")
                    except (SystemExit, EngineError):
                        pass

            # F5 → sauvegarde rapide
            elif key == pygame.K_F5:
                with lock:
                    _quick_save(ctx)

            # Touches de fenêtres → ui_core
            elif current_screen:
                key_name = _pygame_key_name(key, pygame)
                if key_name:
                    ui["handle_key"](current_screen, key_name)

        # ── Redimensionnement ─────────────────────────────────────
        elif event.type == pygame.VIDEORESIZE:
            pass   # pygame.RESIZABLE gère tout seul

        return True

    def _pygame_key_name(key: int, pygame) -> str | None:
        """Convertit un keycode pygame en nom normalisé pour ui_core."""
        fn_keys = {
            pygame.K_F1:  "F1",  pygame.K_F2:  "F2",
            pygame.K_F3:  "F3",  pygame.K_F4:  "F4",
            pygame.K_F6:  "F6",  pygame.K_F7:  "F7",
            pygame.K_F8:  "F8",  pygame.K_F9:  "F9",
            pygame.K_F10: "F10", pygame.K_F11: "F11",
            pygame.K_TAB: "TAB",
        }
        if key in fn_keys:
            return fn_keys[key]
        if 32 <= key <= 126:
            return chr(key).upper()
        return None

    def _scroll_main(panels: dict, delta: int) -> None:
        if "main" in panels:
            panels["main"].scroll(delta)

    def _choose(idx: int, ctx) -> None:
        from core.errors import EngineError
        try:
            ctx.events.emit("on_cli_input", ctx, str(idx))
        except SystemExit:
            pass
        except EngineError as e:
            display["message"]  = f"✗ {e}"
            display["_msg_ttl"] = 180

    def _quick_save(ctx) -> None:
        engine = ctx.mod_states.get("engine")
        if engine is None:
            return
        import os
        os.makedirs("saves", exist_ok=True)
        name = ctx.mod_states.get("current_adventure", "game")
        try:
            engine.save_game(f"saves/{name}_quicksave.json")
        except Exception as e:
            display["message"]  = f"✗ {e}"
            display["_msg_ttl"] = 180

    # ── API et ui_run ─────────────────────────────────────────────
    ctx.mod_states["ui_run"]        = ui_run
    ctx.mod_states["simple_ui_api"] = {
        "display":       display,
        "set_image":     lambda surf: display.__setitem__("_image", surf),
        "clear_image":   lambda: display.__setitem__("_image", None),
    }