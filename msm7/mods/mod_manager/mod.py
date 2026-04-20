# mods/mod_manager/mod.py
import json
from pathlib import Path


def register(ctx):
    st      = ctx.mod_states.get("styled_text_api")
    cmd_api = ctx.mod_states.get("cmd_api")
    if st is None:
        raise RuntimeError("mod_manager requires styled_text to be loaded first")
    if cmd_api is None:
        raise RuntimeError("mod_manager requires cmd to be loaded first")

    MODS_FOLDER = Path("mods")

    # ----------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------

    def _read_meta(mod_dir: Path) -> dict | None:
        meta_path = mod_dir / "mod.json"
        if not meta_path.exists():
            return None
        try:
            return json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _write_meta(mod_dir: Path, meta: dict) -> bool:
        try:
            (mod_dir / "mod.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            return True
        except OSError as e:
            print(st["color"](f"  ✗ Impossible d'écrire mod.json : {e}", "red"))
            return False

    def _scan_all() -> list[dict]:
        """Retourne tous les mods du dossier avec leur meta et statut."""
        if not MODS_FOLDER.exists():
            return []
        results = []
        for mod_dir in sorted(MODS_FOLDER.iterdir()):
            if not mod_dir.is_dir():
                continue
            if not (mod_dir / "mod.py").exists():
                continue
            meta = _read_meta(mod_dir)
            if meta is None:
                continue
            results.append({
                "dir":    mod_dir,
                "name":   meta.get("name", mod_dir.name),
                "meta":   meta,
                "active": meta.get("active", False),
                "loaded": meta.get("name", mod_dir.name) in ctx.mod_states.get("mods_loaded", []),
            })
        return results

    # ----------------------------------------------------------------
    # cmd : mods — liste tous les mods
    # ----------------------------------------------------------------

    def cmd_mods(ctx, args):
        mods = _scan_all()
        if not mods:
            print(st["color"]("  Aucun mod trouvé dans 'mods/'.", "white"))
            return

        print("\n" + st["title"]("Mods disponibles"))

        max_name = max(len(m["name"]) for m in mods)

        for m in mods:
            # Statut visuel
            if m["loaded"]:
                status = st["color"]("● chargé  ", "green")
            elif m["active"]:
                status = st["color"]("○ actif   ", "yellow")
            else:
                status = st["color"]("✗ inactif ", "red")

            name    = st["bold"](m["name"].ljust(max_name))
            version = st["color"](m["meta"].get("version", ""), "white")
            desc    = m["meta"].get("description", "")
            depends = m["meta"].get("depends", [])
            dep_str = st["color"](f"  [{', '.join(depends)}]", "cyan") if depends else ""

            print(f"  {status}  {name}  {version}  {desc}{dep_str}")

        loaded_count = sum(1 for m in mods if m["loaded"])
        active_count = sum(1 for m in mods if m["active"])
        print(
            f"\n  {st['color'](str(loaded_count), 'green')} chargé(s)  "
            f"{st['color'](str(active_count), 'yellow')} actif(s)  "
            f"{st['color'](str(len(mods)), 'white')} total"
        )
        print()

    # ----------------------------------------------------------------
    # cmd : enable / disable
    # ----------------------------------------------------------------

    def _set_active(mod_name: str, value: bool) -> None:
        mods = _scan_all()
        match = next((m for m in mods if m["name"] == mod_name), None)

        if match is None:
            print(st["color"](f"  ✗ Mod '{mod_name}' introuvable.", "red"))
            return

        if match["active"] == value:
            state = "déjà actif" if value else "déjà inactif"
            print(st["color"](f"  · '{mod_name}' est {state}.", "white"))
            return

        meta = match["meta"]
        meta["active"] = value
        if _write_meta(match["dir"], meta):
            verb = st["color"]("activé", "green") if value else st["color"]("désactivé", "red")
            print(f"  ✓ '{mod_name}' {verb}. Faites 'refresh' pour appliquer.")

    def cmd_enable(ctx, args):
        if not args:
            print("Usage: enable <nom_mod>")
            return
        _set_active(args[0], True)

    def cmd_disable(ctx, args):
        if not args:
            print("Usage: disable <nom_mod>")
            return
        _set_active(args[0], False)

    # ----------------------------------------------------------------
    # cmd : refresh — recharge tous les mods proprement
    # ----------------------------------------------------------------

    def cmd_refresh(ctx, args):
        """
        Recharge tous les mods depuis le disque sans relancer le programme.

        Problème fondamental : après ctx.reset(), ctx.events est un nouvel
        objet. La boucle principale du programme tient une référence à
        l'ANCIEN EventBus pour écouter on_cli_input. Cette référence est
        caduque après le reset.

        Solution : on ne remplace pas ctx lui-même, on réinitialise son
        contenu via ctx.reset() (qui appelle __init__ en place), puis on
        recharge les mods. La boucle principale doit écouter
        ctx.events dynamiquement à chaque itération, pas le stocker dans
        une variable locale.

        Si l'aventure était en cours, elle est perdue (comportement attendu :
        refresh = retour au menu principal).
        """
        print(st["color"]("\n  ↻ Rechargement des mods...", "cyan"))

        adventure_was_running = ctx.mod_states.get("engine") is not None
        if adventure_was_running:
            print(st["color"]("  · Aventure en cours interrompue.", "yellow"))

        ctx.reset()

        from core import ModLoader
        loader = ModLoader(ctx)
        warnings = loader.load_mods_from_folder(str(MODS_FOLDER))

        loaded = ctx.mod_states.get("mods_loaded", [])
        print(st["color"](f"\n  ✓ {len(loaded)} mod(s) rechargé(s) : {', '.join(loaded)}", "green"))

        if warnings:
            for w in warnings:
                print(st["color"](f"  ⚠ {w}", "yellow"))
        print()

    # ----------------------------------------------------------------
    # cmd : mod_info — détail d'un mod
    # ----------------------------------------------------------------

    def cmd_mod_info(ctx, args):
        if not args:
            print("Usage: mod_info <nom_mod>")
            return

        mods  = _scan_all()
        match = next((m for m in mods if m["name"] == args[0]), None)

        if match is None:
            print(st["color"](f"  ✗ Mod '{args[0]}' introuvable.", "red"))
            return

        meta = match["meta"]
        print("\n" + st["title"](meta.get("name", args[0])))

        fields = [
            ("version",     meta.get("version", "—")),
            ("description", meta.get("description", "—")),
            ("type",        meta.get("type", "—")),
            ("active",      str(meta.get("active", False))),
            ("chargé",      str(match["loaded"])),
            ("depends",     ", ".join(meta.get("depends", [])) or "aucune"),
        ]
        max_f = max(len(f) for f, _ in fields)
        for field, value in fields:
            print(f"  {st['color'](field.ljust(max_f), 'cyan')}  {value}")
        print()

    # ----------------------------------------------------------------
    # Enregistrement
    # ----------------------------------------------------------------

    reg = cmd_api["register_command"]
    make_completer = cmd_api["make_completer"]

    # enable/disable : tous les dossiers dans mods/ (y compris les inactifs)
    # info           : idem, on peut inspecter n'importe quel mod

    reg("mods.list",    cmd_mods,    "Lister tous les mods et leur statut")
    reg("mods.enable",  cmd_enable,  "Activer un mod (modifie mod.json)",
        completer=make_completer(Path("mods")))
    reg("mods.disable", cmd_disable, "Désactiver un mod (modifie mod.json)",
        completer=make_completer(Path("mods")))
    reg("mods.info",    cmd_mod_info,"Afficher le détail d'un mod",
        completer=make_completer(Path("mods")))
    reg("refresh",      cmd_refresh, "Recharger tous les mods depuis le disque")