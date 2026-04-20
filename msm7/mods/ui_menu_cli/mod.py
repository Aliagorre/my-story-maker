# mods/ui_menu_cli/mod.py
import os
import json
from pathlib import Path
from core.errors import EngineError


def register(ctx):
    st = ctx.mod_states.get("styled_text_api")
    if st is None:
        raise RuntimeError("menu_cli requires styled_text to be loaded first")

    # ----------------------------------------------------------------
    # Helpers d'affichage
    # ----------------------------------------------------------------

    def _header(text):
        print("\n" + st["title"](text))

    def _print_options(options, label_fn=None):
        for i, opt in enumerate(options):
            label = label_fn(opt) if label_fn else str(opt)
            index = st["color"](f"  {i}.", "cyan")
            print(f"{index} {label}")
        print(st["color"]("  q.", "cyan") + " Annuler")
        print()

    def _prompt(text):
        return input(st["bold"](f"{text} > ")).strip()

    def _ok(msg):
        print(st["color"]("  ✓ " + msg, "green"))

    def _err(msg):
        print(st["color"]("  ✗ " + msg, "red"))

    def _neutral(msg):
        print(st["color"]("  · " + msg, "white"))

    # ----------------------------------------------------------------
    # Helpers internes
    # ----------------------------------------------------------------

    def _get_engine(ctx):
        return ctx.mod_states.get("engine")

    def _get_adventure_name(ctx):
        return ctx.mod_states.get("current_adventure")

    def _list_saves(adventure_name=None):
        saves_dir = Path("saves")
        if not saves_dir.exists():
            return []
        files = [f for f in saves_dir.iterdir() if f.suffix == ".json"]
        if adventure_name:
            files = [f for f in files if f.stem.startswith(f"{adventure_name}_")]
        return sorted(files)

    def _pick(raw, options):
        raw = raw.strip().lower()
        try:
            idx = int(raw)
            if 0 <= idx < len(options):
                return options[idx]
            return None
        except ValueError:
            pass
        for opt in options:
            if str(opt).lower() == raw or Path(opt).stem.lower() == raw:
                return opt
        return None

    # ----------------------------------------------------------------
    # Démarrage d'aventure
    # ----------------------------------------------------------------

    def _do_start(ctx, folder):
        ctx.reset()
        from core import ModLoader
        mods = ModLoader(ctx)
        mods.load_mods_from_folder("mods")
        ctx.mod_states["current_adventure"] = folder
        mods.load_single_mod_from_dir(Path(f"adventures/{folder}"))
        engine = ctx.mod_states.get("engine")
        if engine is None:
            _err("L'aventure n'a pas créé d'engine.")
            return
        engine.start("start")

    # ----------------------------------------------------------------
    # Menu aventures
    # ----------------------------------------------------------------

    def menu_adventures(ctx, args):
        adv_dir = Path("adventures")
        if not adv_dir.exists():
            _err("Aucun dossier 'adventures' trouvé.")
            return

        adventures = []
        for d in adv_dir.iterdir():
            meta_path = d / "mod.json"
            if d.is_dir() and meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text(encoding="utf-8"))
                    adventures.append((d.name, meta))
                except json.JSONDecodeError:
                    pass

        if not adventures:
            _neutral("Aucune aventure disponible.")
            return

        _header("Aventures disponibles")
        for i, (folder, meta) in enumerate(adventures):
            index = st["color"](f"  {i}.", "cyan")
            name  = st["bold"](meta.get("name", folder))
            desc  = st["color"](meta.get("description", ""), "white")
            print(f"{index} {name:<25} {desc}")
        print(st["color"]("  q.", "cyan") + " Annuler\n")

        raw = _prompt("Choix")
        if raw.lower() == "q":
            return

        selection = None
        try:
            idx = int(raw)
            if 0 <= idx < len(adventures):
                selection = adventures[idx]
        except ValueError:
            for folder, meta in adventures:
                if raw.lower() in (folder.lower(), meta.get("name", "").lower()):
                    selection = (folder, meta)
                    break

        if selection is None:
            _err("Sélection invalide.")
            return

        folder, meta = selection
        _do_start(ctx, folder)

    # ----------------------------------------------------------------
    # Menu sauvegardes
    # ----------------------------------------------------------------

    def menu_saves(ctx, args):
        adventure_name = _get_adventure_name(ctx)
        saves = _list_saves(adventure_name)

        if not saves:
            _neutral("Aucune sauvegarde trouvée.")
            return

        label = f"'{adventure_name}'" if adventure_name else "toutes aventures"
        _header(f"Sauvegardes ({label})")
        _print_options(saves, label_fn=lambda f: f.stem)

        raw = _prompt("Choix")
        if raw.lower() == "q":
            return

        save_file = _pick(raw, saves)
        if save_file is None:
            _err("Sélection invalide.")
            return

        _save_actions(ctx, save_file)

    def _save_actions(ctx, save_file):
        _header(save_file.stem)
        print(st["color"]("  0.", "cyan") + " Charger")
        print(st["color"]("  1.", "cyan") + " Renommer")
        print(st["color"]("  2.", "cyan") + " Supprimer")
        print(st["color"]("  q.", "cyan") + " Annuler\n")

        raw = _prompt("Action").lower()

        if raw in ("0", "charger", "load"):
            _do_load(ctx, save_file)

        elif raw in ("1", "renommer", "rename"):
            new_name = _prompt("Nouveau nom")
            if not new_name:
                _err("Nom invalide.")
                return
            new_path = save_file.parent / f"{new_name}.json"
            if new_path.exists():
                _err(f"Une sauvegarde '{new_name}' existe déjà.")
                return
            save_file.rename(new_path)
            _ok(f"Renommée → {new_name}")

        elif raw in ("2", "supprimer", "delete"):
            confirm = _prompt(
                st["color"](f"Supprimer '{save_file.stem}' ? (o/n)", "red")
            ).lower()
            if confirm == "o":
                save_file.unlink()
                _ok(f"'{save_file.stem}' supprimée.")
            else:
                _neutral("Annulé.")

        elif raw == "q":
            return

        else:
            _err("Action invalide.")

    def _do_load(ctx, save_file):
        engine = _get_engine(ctx)
        if engine is None:
            parts  = save_file.stem.split("_", 1)
            folder = parts[0] if len(parts) > 1 else None
            if folder and Path(f"adventures/{folder}").exists():
                _do_start(ctx, folder)
                engine = _get_engine(ctx)
            else:
                _err("Impossible de déduire l'aventure depuis la sauvegarde.")
                _neutral("Utilisez 'start' d'abord.")
                return
        try:
            engine.load_game(str(save_file))
            _ok(f"Chargé ← {save_file.stem}")
        except EngineError as e:
            _err(f"Erreur au chargement : {e}")

    # ----------------------------------------------------------------
    # Menu pause
    # ----------------------------------------------------------------

    def menu_pause(ctx, args):
        engine = _get_engine(ctx)
        if engine is None:
            _err("Aucune aventure en cours.")
            return

        adventure_name = _get_adventure_name(ctx)

        while True:
            _header("PAUSE")
            print(st["color"]("  0.", "cyan") + " Reprendre")
            print(st["color"]("  1.", "cyan") + " Sauvegarder")
            print(st["color"]("  2.", "cyan") + " Charger une sauvegarde")
            print(st["color"]("  3.", "cyan") + " Quitter l'aventure\n")

            raw = _prompt("Choix").lower()

            if raw in ("0", "reprendre", "resume"):
                break

            elif raw in ("1", "sauvegarder", "save"):
                name = _prompt("Nom de la sauvegarde")
                if not name:
                    _err("Nom invalide.")
                    continue
                prefix = f"{adventure_name}_" if adventure_name else ""
                path   = f"saves/{prefix}{name}.json"
                os.makedirs("saves", exist_ok=True)
                try:
                    engine.save_game(path)
                    _ok(f"Sauvegardé → {path}")
                except Exception as e:
                    _err(f"Erreur : {e}")

            elif raw in ("2", "charger", "load"):
                saves = _list_saves(adventure_name)
                if not saves:
                    _neutral("Aucune sauvegarde disponible.")
                    continue
                print()
                _print_options(saves, label_fn=lambda f: f.stem)
                raw2 = _prompt("Choix").lower()
                if raw2 == "q":
                    continue
                save_file = _pick(raw2, saves)
                if save_file is None:
                    _err("Sélection invalide.")
                    continue
                _do_load(ctx, save_file)
                break

            elif raw in ("3", "quitter", "quit"):
                confirm = _prompt(
                    st["color"]("Quitter l'aventure ? (o/n)", "red")
                ).lower()
                if confirm == "o":
                    ctx.reset()
                    from core import ModLoader
                    mods = ModLoader(ctx)
                    mods.load_mods_from_folder("mods")
                    _ok("Aventure quittée.")
                    break

            else:
                _err("Option invalide.")

    # ----------------------------------------------------------------
    # Enregistrement
    # ----------------------------------------------------------------

    cmd_api = ctx.mod_states.get("cmd_api")
    if cmd_api is None:
        raise RuntimeError("menu_cli requires cmd to be loaded first")

    cmd_api["register_command"]("menu.adventures", menu_adventures, "Choisir et lancer une aventure")
    cmd_api["register_command"]("menu.saves",      menu_saves,      "Gérer les sauvegardes")
    cmd_api["register_command"]("menu.pause",      menu_pause,      "Menu pause")
    # Version future : "menu saves slot1" charge directement slot1
    #cmd_api["register_command"]("menu.saves", menu_saves, "Gérer les sauvegardes",
    #    completer=make_completer(Path("saves/*.json")))

    ctx.mod_states["menu_api"] = {
        "menu_adventures": menu_adventures,
        "saves":           menu_saves,
        "pause":           menu_pause,
    }