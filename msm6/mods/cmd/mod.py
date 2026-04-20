# mods/cmd/mod.py
#
# SYSTÈME DE COMMANDES HIÉRARCHIQUES
# ════════════════════════════════════════════════════════════════════
#
# ENREGISTREMENT D'UNE COMMANDE
# ─────────────────────────────
#   register_command(path, func, help_text, completer=None)
#
#   path      : chemin pointé par des points  "adventure.start"
#   func      : callable(ctx, args) → None
#   help_text : string affichée dans 'help'
#   completer : fn(text, all_args, ctx) → list[str]  ← OPTIONNEL
#               Si fourni, readline appellera cette fonction quand
#               l'utilisateur appuie sur Tab après la commande.
#               text     = fragment du mot courant à compléter
#               all_args = tous les mots déjà tapés après la commande
#               ctx      = contexte courant
#
# EXEMPLE — commande sans autocomplétion :
#   register_command("debug.ctx", cmd_ctx, "Afficher le contexte")
#
# EXEMPLE — commande avec autocomplétion sur le 1er argument :
#   def _complete_theme(text, all_args, ctx):
#       themes = ["default", "dark", "retro"]
#       return [t for t in themes if t.startswith(text)]
#
#   register_command("theme", cmd_theme, "Changer le thème",
#                    completer=_complete_theme)
#
# SAISIE CLI
# ──────────
#   Les niveaux sont séparés par des ESPACES :
#     "adventure start demo"  →  dossier "adventure", cmd "start", arg "demo"
#     "help adventure"        →  cmd "help", arg "adventure"
#
# ════════════════════════════════════════════════════════════════════

import os
import json
from pathlib import Path
from core.context import Context
from core.errors import EngineError


def register(ctx: Context):
    commands = {}   # arbre : {"adventure": {"start": {is_command, func, ...}, ...}}

    def make_completer(source):
        """
        Génère une fonction de complétion depuis différentes sources.

        source peut être :

        - une liste fixe
            make_completer(["default", "dark", "retro"])

        - un callable(ctx) → list[str]   (évalué à chaque Tab, donc toujours frais)
            make_completer(lambda ctx: list(ctx.state.keys()))

        - un Path (ou string) vers un dossier → noms des sous-dossiers
            make_completer(Path("adventures"))

        - un Path avec suffix → stems des fichiers correspondants
            make_completer(Path("saves/*.json"))

        - un dict-key : clé dans mod_states dont la valeur est une liste
            make_completer("mod_states:mods_loaded")
        """
        from pathlib import Path

        # ── liste statique ───────────────────────────────────────────
        if isinstance(source, list):
            def _completer(text, all_args, ctx):
                return [s for s in source if s.startswith(text)]
            return _completer

        # ── callable(ctx) → list ─────────────────────────────────────
        if callable(source):
            def _completer(text, all_args, ctx):
                try:
                    items = source(ctx)
                    return [s for s in items if str(s).startswith(text)]
                except Exception:
                    return []
            return _completer

        # ── Path avec glob ("saves/*.json") ──────────────────────────
        if isinstance(source, (str, Path)):
            p = Path(source)
            if "*" in p.name:
                folder, pattern = p.parent, p.name
                suffix = pattern.lstrip("*")
                def _completer(text, all_args, ctx):
                    if not folder.exists():
                        return []
                    return [f.stem for f in folder.iterdir()
                            if f.suffix == suffix and f.stem.startswith(text)]
                return _completer
            else:
                # Dossier simple → noms des sous-dossiers
                def _completer(text, all_args, ctx):
                    if not p.exists():
                        return []
                    return [d.name for d in p.iterdir()
                            if d.is_dir() and d.name.startswith(text)]
                return _completer

        raise ValueError(f"make_completer: source non supportée : {source!r}")

    def _ensure_path(path: str):
        """Navigue/crée les nœuds intermédiaires depuis "a.b.c".
        Retourne (nœud_parent, nom_feuille)."""
        parts = path.split(".")
        node = commands
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        return node, parts[-1]

    def resolve_path(path: str):
        """Résout "adventure.start" → nœud dict, ou None."""
        node = commands
        for p in path.replace("/", ".").split("."):
            if not isinstance(node, dict) or p not in node:
                return None
            node = node[p]
        return node

    def register_command(path: str, func, help_text: str = "", completer=None):
        """
        Enregistre une commande dans l'arbre.

        completer (optionnel) : fn(text, all_args, ctx) → list[str]
            Fourni directement par le code qui crée la commande.
            C'est lui qui sait ce qu'il attend comme arguments.
            Si None, Tab ne proposera rien après la commande.

        Exemple d'utilisation depuis un autre mod :
            def _complete_save_name(text, all_args, ctx):
                saves = Path("saves")
                if not saves.exists(): return []
                return [f.stem for f in saves.iterdir()
                        if f.suffix == ".json" and f.stem.startswith(text)]

            cmd_api["register_command"](
                "adventure.load",
                cmd_load,
                "Charger une sauvegarde",
                completer=_complete_save_name   # ← déclaré ici, pas dans autocomplete
            )
        """
        node, name = _ensure_path(path)
        node[name] = {
            "func":       func,
            "help":       help_text,
            "is_command": True,
            "completer":  completer,
        }

    def _resolve_command(parts: list):
        """Descend l'arbre mot par mot.
        Retourne (nœud_commande, nb_mots_consommés) ou (None, 0)."""
        node = commands
        for i, p in enumerate(parts):
            if not isinstance(node, dict) or p not in node:
                return None, 0
            node = node[p]
            if isinstance(node, dict) and node.get("is_command"):
                return node, i + 1
        return None, 0

    def run_command(ctx, raw: str):
        parts = raw.strip().split()
        if not parts:
            return False
        cmd_node, consumed = _resolve_command(parts)
        if cmd_node:
            cmd_node["func"](ctx, parts[consumed:])
            return True
        return False

    def list_commands(ctx):
        return commands

    ctx.mod_states["cmd_api"] = {
        "register_command": register_command,
        "run_command":      run_command,
        "list_commands":    list_commands,
        "resolve_path":     resolve_path,
        "make_completer":   make_completer,
    }

    def _print_tree(node: dict, prefix: str = ""):
        folders = {k: v for k, v in node.items()
                   if isinstance(v, dict) and not v.get("is_command")}
        cmds    = {k: v for k, v in node.items()
                   if isinstance(v, dict) and v.get("is_command")}
        for name, cmd in sorted(cmds.items()):
            print(f"{prefix}{name:<18} {cmd['help']}")
        for name, subtree in sorted(folders.items()):
            print(f"{prefix}{name}/")
            # _print_tree(subtree, prefix + "  ")

    def _complete_help(text, all_args, ctx):
        """
        Complète l'argument de 'help', qui est lui-même un chemin
        dans l'arbre ("adventure", "adventure.start"…).
        """
        tree = list_commands(ctx)

        # Pas encore de séparateur → compléter à la racine
        if "." not in text and "/" not in text:
            return [k for k in tree.keys() if k.startswith(text)]

        # Naviguer jusqu'au dernier segment
        sep    = "/" if "/" in text else "."
        parts  = text.replace("/", ".").split(".")
        node   = tree
        for p in parts[:-1]:
            if not isinstance(node, dict) or p not in node:
                return []
            node = node[p]

        prefix = parts[-1]
        return [sep.join(parts[:-1] + [k])
                for k in node.keys() if k.startswith(prefix)]

    def cmd_help(ctx, args):
        if not args:
            print("\n[Commandes disponibles]")
            _print_tree(commands)
            print()
            return
        node = resolve_path(args[0])
        if node is None:
            print(f"[CMD] Inconnu : '{args[0]}'")
            return
        if isinstance(node, dict) and node.get("is_command"):
            print(f"\n{args[0]} — {node['help']}\n")
        else:
            print(f"\n{args[0]}/")
            _print_tree(node, "  ")
            print()

    def cmd_ctx(ctx, args):
        print("\n=== CONTEXTE ===")
        print("\n[State]")
        print(ctx.state or "(vide)")
        print("\n[Mod States keys]")
        print(list(ctx.mod_states.keys()))
        print("\n[Mods chargés]")
        for m in ctx.mod_states.get("mods_loaded", []):
            print(f"  - {m}")
        print("\n[Engine]")
        engine = ctx.mod_states.get("engine")
        print(f"  Node : {engine.context.current_node}" if engine else "  Aucun engine")
        print("\n[Events]")
        for ev in ctx.events._events.keys():
            print(f"  - {ev}")
        print("=================\n")

    def cmd_adventures(ctx, args):
        adv_path = Path("adventures")
        if not adv_path.exists():
            print("[CMD] Dossier 'adventures' introuvable.")
            return
        for d in adv_path.iterdir():
            meta_file = d / "mod.json"
            if meta_file.exists():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    print(f"  - {meta.get('name', d.name)} : {meta.get('description', '')}")
                except Exception:
                    print(f"  - {d.name} : (mod.json invalide)")

    from core.loader import ModLoader

    def cmd_start(ctx, args):
        if not args:
            print("Usage: adventure start <nom>")
            return
        ctx.reset()
        loader = ModLoader(ctx)
        loader.load_mods_from_folder("mods")
        adv_dir = Path(f"adventures/{args[0]}")
        if not adv_dir.exists():
            print(f"[CMD] Aventure introuvable : {args[0]}")
            return
        loader.load_single_mod_from_dir(adv_dir)
        engine = ctx.mod_states.get("engine")
        if engine is None:
            print("[CMD] L'aventure n'a pas créé d'engine.")
            return
        engine.start("start")

    def cmd_save(ctx, args):
        engine = ctx.mod_states.get("engine")
        if engine is None:
            print("[CMD] Aucune aventure en cours.")
            return
        if not args:
            print("Usage: adventure save <nom>")
            return
        path = f"saves/{args[0]}.json"
        os.makedirs("saves", exist_ok=True)
        try:
            engine.save_game(path)
            print(f"[CMD] Sauvegarde → {path}")
        except Exception as e:
            print(f"[CMD] Erreur : {e}")

    def cmd_load(ctx, args):
        if not args:
            print("Usage: adventure load <nom>")
            return
        path = f"saves/{args[0]}.json"
        if not os.path.exists(path):
            print(f"[CMD] Introuvable : {args[0]}")
            return
        engine = ctx.mod_states.get("engine")
        if engine is None:
            print("[CMD] Aucune aventure en cours.")
            return
        try:
            engine.load_game(path)
            print(f"[CMD] Chargement ← {path}")
        except EngineError as e:
            print(f"[CMD] {e}")

    def cmd_exit(ctx, args):
        raise SystemExit

    def cmd_clear(ctx, args):
        os.system("cls" if os.name == "nt" else "clear")

    # ── register_command ─────────────────────────────────────────────

    register_command("help",  cmd_help,  "Afficher l'aide",
                    completer=_complete_help)

    register_command("exit",  cmd_exit,  "Quitter")

    register_command("clear", cmd_clear, "Effacer le terminal")

    register_command("debug.ctx", cmd_ctx, "Afficher le contexte interne")

    register_command("adventure.list",  cmd_adventures, "Lister les aventures")

    register_command("adventure.start", cmd_start, "Démarrer une aventure",
                    completer=make_completer(Path("adventures")))

    register_command("adventure.save",  cmd_save, "Sauvegarder la partie")
    # Pas de completer : l'utilisateur donne un nom libre, pas un existant.

    register_command("adventure.load",  cmd_load, "Charger une sauvegarde",
                    completer=make_completer(Path("saves/*.json")))

    # ── handler CLI ───────────────────────────────────────────────
    def on_cli_input(ctx, raw):
        if run_command(ctx, raw):
            return
        engine = ctx.mod_states.get("engine")
        if engine is None:
            return
        try:
            engine.choose(int(raw))
        except ValueError:
            print("[CMD] Entrée invalide.")
        except EngineError as e:
            print(f"[CMD] {e}")

    ctx.events.on("on_cli_input", on_cli_input)