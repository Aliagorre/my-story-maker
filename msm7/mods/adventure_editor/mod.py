# mods/adventure_editor/mod.py
#
# Éditeur d'aventure CLI.
#
# ÉTAT PERSISTÉ dans ctx.mod_states["editor"] :
#   adventure  : str | None       nom du dossier aventure en cours
#   graph      : dict             {"nodes": [...]} chargé en mémoire
#   meta       : dict             contenu de mod.json
#   dirty      : bool             modifications non sauvegardées
#   adv_dir    : Path             chemin complet vers le dossier aventure
#
# COMMANDES :
#   new_adventure              Scaffolde une nouvelle aventure
#   edit <nom>                 Ouvre une aventure existante
#   editor                     Affiche l'état de l'éditeur
#   nodes                      Liste les nœuds
#   node <id>                  Détail d'un nœud
#   add_node                   Assistant de création de nœud
#   edit_node <id>             Édite un nœud existant
#   del_node <id>              Supprime un nœud
#   add_choice <node_id>       Ajoute un choix à un nœud
#   edit_choice <n_id> <c_id>  Édite un choix
#   del_choice <n_id> <c_id>   Supprime un choix
#   edit_meta                  Édite le mod.json
#   validate                   Valide la cohérence du graphe
#   editor_save                Sauvegarde graph.json + mod.json
#   discard                    Abandonne les modifications

import json
from pathlib import Path

# ════════════════════════════════════════════════════════════════════
# MOD TEMPLATE
# ════════════════════════════════════════════════════════════════════

_MOD_PY_TEMPLATE = '''\
# adventures/{name}/mod.py

def register(ctx):
    from core import load_graph_from_file, Engine
    graph  = load_graph_from_file("adventures/{name}/graph.json")
    engine = Engine(graph, ctx, ctx.events)
    ctx.mod_states["engine"] = engine
'''

_MOD_JSON_TEMPLATE = {
    "name":        "",
    "description": "",
    "depends":     [],
    "version":     "1.0.0",
    "active":      True,
    "variables":   {},
}

_GRAPH_TEMPLATE = {
    "nodes": [
        {
            "id":      "start",
            "text":    "Le début de votre aventure.",
            "choices": [],
        }
    ]
}


def register(ctx):
    st      = ctx.mod_states.get("styled_text_api")
    cmd_api = ctx.mod_states.get("cmd_api")
    if st is None:
        raise RuntimeError("adventure_editor requires styled_text")
    if cmd_api is None:
        raise RuntimeError("adventure_editor requires cmd")

    ADV_ROOT = Path("adventures")

    # ── état éditeur ─────────────────────────────────────────────
    def _state() -> dict:
        return ctx.mod_states.setdefault("editor", {
            "adventure": None,
            "graph":     None,
            "meta":      None,
            "dirty":     False,
            "adv_dir":   None,
        })

    # ── helpers d'affichage ───────────────────────────────────────
    def _h(text):      print("\n" + st["title"](text))
    def _ok(msg):      print(st["color"]("  ✓ " + msg, "green"))
    def _err(msg):     print(st["color"]("  ✗ " + msg, "red"))
    def _warn(msg):    print(st["color"]("  ⚠ " + msg, "yellow"))
    def _info(msg):    print(st["color"]("  · " + msg, "white"))
    def _sep():        print(st["color"]("  " + "─" * 48, "white"))

    def _prompt(label, default=None):
        suffix = f" [{default}]" if default is not None else ""
        raw = input(st["bold"](f"  {label}{suffix} > ")).strip()
        return raw if raw else (str(default) if default is not None else "")

    def _choose(label, options, allow_empty=False):
        """Affiche une liste numérotée, retourne l'option choisie ou None."""
        for i, opt in enumerate(options):
            print(f"    {st['color'](str(i), 'cyan')}. {opt}")
        if allow_empty:
            print(f"    {st['color']('q', 'cyan')}. Annuler")
        raw = _prompt(label)
        if raw.lower() == "q":
            return None
        try:
            idx = int(raw)
            if 0 <= idx < len(options):
                return options[idx]
        except ValueError:
            if raw in options:
                return raw
        _err("Sélection invalide.")
        return None

    def _confirm(msg) -> bool:
        raw = _prompt(st["color"](msg + " (o/n)", "yellow"), "n")
        return raw.lower() == "o"

    # ── vérification état ouvert ──────────────────────────────────
    def _require_open():
        s = _state()
        if s["graph"] is None:
            _err("Aucune aventure ouverte. Utilisez 'edit <nom>'.")
            return False
        return True

    def _dirty_warn():
        s = _state()
        if s["dirty"]:
            _warn("Modifications non sauvegardées (editor_save / discard).")

    # ── accès nœud ───────────────────────────────────────────────
    def _nodes_index() -> dict:
        s = _state()
        return {n["id"]: n for n in s["graph"]["nodes"]}

    def _get_node(node_id: str) -> dict | None:
        return _nodes_index().get(node_id)

    # ════════════════════════════════════════════════════════════════
    # BUILDERS GUIDÉS
    # ════════════════════════════════════════════════════════════════

    def _available_operators() -> list[str]:
        """Opérateurs enregistrés dans le ConditionEngine."""
        return sorted(ctx.condition_engine.operators.keys())

    def _available_actions() -> list[str]:
        return sorted(ctx.mod_states.get("actions", {}).keys())

    def _available_variables() -> list[str]:
        """Variables connues : state + mod_states (clés de premier niveau)."""
        keys = list(ctx.state.keys())
        for mod, val in ctx.mod_states.items():
            if isinstance(val, dict):
                keys += [f"{mod}.{k}" for k in val.keys()]
        return sorted(set(keys))

    # ── builder de texte ─────────────────────────────────────────
    def _build_text(current=None) -> str | list:
        """
        Retourne soit une string simple, soit une liste conditionnelle.
        current : valeur existante affichée comme référence.
        """
        _h("Éditeur de texte")
        if current:
            _info(f"Valeur actuelle : {json.dumps(current, ensure_ascii=False)}")

        mode = _choose("Mode", ["Texte simple", "Texte conditionnel (liste)"],
                       allow_empty=True)
        if mode is None:
            return current

        if mode == "Texte simple":
            val = _prompt("Texte")
            return val if val else (current or "")

        # Mode liste conditionnelle
        entries = list(current) if isinstance(current, list) else []
        while True:
            _sep()
            if entries:
                for i, e in enumerate(entries):
                    cond = e.get("conditions", "—")
                    _info(f"{i}. [{json.dumps(cond)}] {e.get('value','')}")
            else:
                _info("(aucune entrée)")

            action = _choose("Action", ["Ajouter une entrée", "Supprimer une entrée",
                                        "Terminer"], allow_empty=False)
            if action == "Terminer" or action is None:
                break
            if action == "Ajouter une entrée":
                val  = _prompt("Texte de l'entrée")
                cond = _build_condition(label="Condition (vide = défaut)")
                entry: dict = {"value": val}
                if cond is not None:
                    entry["conditions"] = cond
                entries.append(entry)
            elif action == "Supprimer une entrée" and entries:
                raw = _prompt("Index à supprimer")
                try:
                    entries.pop(int(raw))
                except (ValueError, IndexError):
                    _err("Index invalide.")

        return entries if entries else (current or "")

    # ── builder de condition ─────────────────────────────────────
    def _build_condition(current=None, label="Condition") -> dict | str | bool | None:
        """
        Guide l'utilisateur pour construire une condition.
        Retourne None si annulé / vide.
        """
        ops = _available_operators()
        _h(f"Builder de condition — {label}")
        if current is not None:
            _info(f"Condition actuelle : {json.dumps(current, ensure_ascii=False)}")
        _info(f"Opérateurs disponibles : {', '.join(ops)}")

        kind = _choose("Type de condition", [
            "Aucune (toujours vrai)",
            "Variable booléenne simple",
            "Opérateur",
        ], allow_empty=True)
        if kind is None:
            return current  # annulé

        if kind == "Aucune (toujours vrai)":
            return None

        if kind == "Variable booléenne simple":
            vars_ = _available_variables()
            _info(f"Variables : {', '.join(vars_) or '(aucune)'}")
            var = _prompt("Nom de la variable")
            return var if var else None

        # Opérateur
        op = _choose("Opérateur", ops, allow_empty=True)
        if op is None:
            return current

        # Opérateurs logiques récursifs
        if op == "not":
            _info("Construisez la sous-condition :")
            sub = _build_condition(label="sous-condition")
            return {"not": sub} if sub is not None else None

        if op in ("and", "or"):
            subs = []
            while True:
                _info(f"Sous-condition {len(subs)+1} (vide pour terminer) :")
                sub = _build_condition(label=f"sous-condition {len(subs)+1}")
                if sub is None:
                    break
                subs.append(sub)
                if not _confirm("Ajouter une autre sous-condition ?"):
                    break
            return {op: subs} if subs else None

        # Opérateur binaire ou unaire
        _info("Arguments : variable ('player_gold'), littéral (10), ou expression")
        arg1 = _prompt("Argument 1")
        arg1 = _parse_arg(arg1)

        # Opérateurs unaires
        if op in ("abs",):
            return {op: arg1}

        arg2 = _prompt("Argument 2")
        arg2 = _parse_arg(arg2)

        # between : 3 arguments
        if op == "between":
            arg3 = _prompt("Argument 3 (max)")
            arg3 = _parse_arg(arg3)
            return {op: [arg1, arg2, arg3]}

        return {op: [arg1, arg2]}

    def _parse_arg(raw: str):
        """Convertit une string saisie en type Python approprié."""
        if raw.lower() == "true":  return True
        if raw.lower() == "false": return False
        if raw.lower() in ("null", "none"): return None
        try: return int(raw)
        except ValueError: pass
        try: return float(raw)
        except ValueError: pass
        return raw   # string / nom de variable

    # ── builder d'action ─────────────────────────────────────────
    def _build_action(current=None) -> dict | None:
        """Construit une action {action: args, conditions?}."""
        actions = _available_actions()
        _h("Builder d'action")
        if current:
            _info(f"Action actuelle : {json.dumps(current, ensure_ascii=False)}")

        action_name = _choose("Action", actions, allow_empty=True)
        if action_name is None:
            return current

        args = None

        if action_name == "set":
            var = _prompt("Variable cible")
            val = _parse_arg(_prompt("Valeur"))
            args = [var, val]

        elif action_name == "unset":
            var = _prompt("Variable à supprimer")
            args = var

        elif action_name == "emit":
            event = _prompt("Nom de l'événement")
            extra = _prompt("Arguments supplémentaires (vide = aucun)")
            if extra:
                args = [event, extra]
            else:
                args = event

        else:
            # Action inconnue : saisie libre en JSON
            raw = _prompt(f"Arguments pour '{action_name}' (JSON)")
            try:
                args = json.loads(raw) if raw else None
            except json.JSONDecodeError:
                args = raw

        result: dict = {action_name: args}

        if _confirm("Ajouter une condition à cette action ?"):
            cond = _build_condition(label="condition de l'action")
            if cond is not None:
                result["conditions"] = cond

        return result

    # ── builder de liste d'actions ────────────────────────────────
    def _build_actions(current: list | None, label: str) -> list:
        entries = list(current or [])
        while True:
            _sep()
            _info(f"Actions {label} ({len(entries)}) :")
            for i, a in enumerate(entries):
                _info(f"  {i}. {json.dumps(a, ensure_ascii=False)}")

            action = _choose("Action", ["Ajouter", "Supprimer", "Terminer"],
                             allow_empty=False)
            if action == "Terminer" or action is None:
                break
            if action == "Ajouter":
                a = _build_action()
                if a:
                    entries.append(a)
            elif action == "Supprimer" and entries:
                raw = _prompt("Index à supprimer")
                try:
                    entries.pop(int(raw))
                except (ValueError, IndexError):
                    _err("Index invalide.")
        return entries

    # ════════════════════════════════════════════════════════════════
    # COMMANDES PRINCIPALES
    # ════════════════════════════════════════════════════════════════

    # ── new_adventure ─────────────────────────────────────────────
    def cmd_new_adventure(ctx, args):
        _h("Nouvelle aventure")
        folder = _prompt("Nom du dossier (sans espaces)")
        if not folder:
            _err("Nom invalide.")
            return
        adv_dir = ADV_ROOT / folder
        if adv_dir.exists():
            _err(f"Le dossier '{folder}' existe déjà.")
            return

        name  = _prompt("Nom affiché", default=folder)
        desc  = _prompt("Description", default="")
        deps  = _prompt("Dépendances (séparées par virgules)", default="")
        dep_list = [d.strip() for d in deps.split(",") if d.strip()]

        meta = dict(_MOD_JSON_TEMPLATE)
        meta["name"]        = name
        meta["description"] = desc
        meta["depends"]     = dep_list

        adv_dir.mkdir(parents=True)
        (adv_dir / "mod.py").write_text(
            _MOD_PY_TEMPLATE.format(name=folder), encoding="utf-8"
        )
        (adv_dir / "mod.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (adv_dir / "graph.json").write_text(
            json.dumps(_GRAPH_TEMPLATE, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        _ok(f"Aventure '{folder}' créée dans {adv_dir}")
        _info("Utilisez 'edit <nom>' pour l'éditer.")

    # ── edit ──────────────────────────────────────────────────────
    def cmd_edit(ctx, args):
        if not args:
            print("Usage: edit <nom_aventure>")
            return

        s = _state()
        if s["dirty"] and not _confirm("Modifications non sauvegardées. Continuer ?"):
            return

        folder  = args[0]
        adv_dir = ADV_ROOT / folder

        if not adv_dir.exists():
            _err(f"Aventure '{folder}' introuvable.")
            return

        try:
            meta  = json.loads((adv_dir / "mod.json").read_text(encoding="utf-8"))
            graph = json.loads((adv_dir / "graph.json").read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError) as e:
            _err(f"Erreur de lecture : {e}")
            return

        s["adventure"] = folder
        s["adv_dir"]   = adv_dir
        s["meta"]      = meta
        s["graph"]     = graph
        s["dirty"]     = False

        _ok(f"Aventure '{folder}' ouverte — {len(graph['nodes'])} nœud(s)")

    # ── editor status ─────────────────────────────────────────────
    def cmd_editor(ctx, args):
        s = _state()
        _h("Éditeur d'aventure")
        if s["adventure"] is None:
            _info("Aucune aventure ouverte.")
            return

        dirty_label = st["color"](" ●modifié", "yellow") if s["dirty"] else ""
        _info(f"Aventure  : {st['bold'](s['adventure'])}{dirty_label}")
        _info(f"Titre     : {s['meta'].get('name', '?')}")
        _info(f"Version   : {s['meta'].get('version', '?')}")
        _info(f"Nœuds     : {len(s['graph']['nodes'])}")
        print()

    # ── nodes ─────────────────────────────────────────────────────
    def cmd_nodes(ctx, args):
        if not _require_open(): return
        s = _state()
        _h("Nœuds")
        nodes = s["graph"]["nodes"]
        if not nodes:
            _info("Aucun nœud.")
            return
        for n in nodes:
            nb_choices = len(n.get("choices", []))
            has_enter  = "▶" if n.get("on_enter") else " "
            has_quit   = "◀" if n.get("on_quit")  else " "
            nid   = st["color"](n["id"].ljust(20), "cyan")
            flags = st["color"](f"{has_enter}{has_quit}", "yellow")
            print(f"  {flags} {nid}  {nb_choices} choix")
        print()

    # ── node detail ───────────────────────────────────────────────
    def cmd_node(ctx, args):
        if not _require_open(): return
        if not args:
            print("Usage: node <id>")
            return
        node = _get_node(args[0])
        if node is None:
            _err(f"Nœud '{args[0]}' introuvable.")
            return

        _h(f"Nœud : {node['id']}")
        _info(f"text     : {json.dumps(node.get('text', ''), ensure_ascii=False)}")
        _info(f"on_enter : {json.dumps(node.get('on_enter', []), ensure_ascii=False)}")
        _info(f"on_quit  : {json.dumps(node.get('on_quit',  []), ensure_ascii=False)}")
        _sep()
        for c in node.get("choices", []):
            cond = f"  [{json.dumps(c['conditions'])}]" if "conditions" in c else ""
            cid  = st["color"](c["id"].ljust(15), "cyan")
            print(f"  {cid} → {c['goto']}{st['color'](cond, 'yellow')}  \"{c['text']}\"")
        if not node.get("choices"):
            _info("(aucun choix)")
        print()

    # ── add_node ──────────────────────────────────────────────────
    def cmd_add_node(ctx, args):
        if not _require_open(): return
        s = _state()

        _h("Nouveau nœud")
        node_id = _prompt("ID du nœud")
        if not node_id:
            _err("ID obligatoire.")
            return
        if _get_node(node_id):
            _err(f"Un nœud '{node_id}' existe déjà.")
            return

        text     = _build_text()
        on_enter = _build_actions(None, "on_enter") if _confirm("Ajouter des actions on_enter ?") else []
        on_quit  = _build_actions(None, "on_quit")  if _confirm("Ajouter des actions on_quit ?")  else []

        node: dict = {"id": node_id, "text": text, "choices": []}
        if on_enter: node["on_enter"] = on_enter
        if on_quit:  node["on_quit"]  = on_quit

        s["graph"]["nodes"].append(node)
        s["dirty"] = True
        _ok(f"Nœud '{node_id}' ajouté.")

    # ── edit_node ─────────────────────────────────────────────────
    def cmd_edit_node(ctx, args):
        if not _require_open(): return
        if not args:
            print("Usage: edit_node <id>")
            return
        s    = _state()
        node = _get_node(args[0])
        if node is None:
            _err(f"Nœud '{args[0]}' introuvable.")
            return

        _h(f"Édition nœud : {node['id']}")
        field = _choose("Champ à éditer", ["text", "on_enter", "on_quit", "id"],
                        allow_empty=True)
        if field is None:
            return

        if field == "text":
            node["text"] = _build_text(current=node.get("text"))

        elif field == "on_enter":
            node["on_enter"] = _build_actions(node.get("on_enter"), "on_enter")
            if not node["on_enter"]:
                node.pop("on_enter", None)

        elif field == "on_quit":
            node["on_quit"] = _build_actions(node.get("on_quit"), "on_quit")
            if not node["on_quit"]:
                node.pop("on_quit", None)

        elif field == "id":
            new_id = _prompt("Nouvel ID", default=node["id"])
            if new_id and new_id != node["id"]:
                if _get_node(new_id):
                    _err(f"L'ID '{new_id}' existe déjà.")
                    return
                # Mettre à jour les goto qui pointaient vers l'ancien id
                old_id = node["id"]
                node["id"] = new_id
                for n in s["graph"]["nodes"]:
                    for c in n.get("choices", []):
                        if c.get("goto") == old_id:
                            c["goto"] = new_id
                _ok(f"ID renommé '{old_id}' → '{new_id}' (gotos mis à jour)")

        s["dirty"] = True
        _ok("Nœud mis à jour.")

    # ── del_node ──────────────────────────────────────────────────
    def cmd_del_node(ctx, args):
        if not _require_open(): return
        if not args:
            print("Usage: del_node <id>")
            return
        s      = _state()
        node   = _get_node(args[0])
        if node is None:
            _err(f"Nœud '{args[0]}' introuvable.")
            return

        # Vérifier les références entrantes
        refs = [
            f"{n['id']}.{c['id']}"
            for n in s["graph"]["nodes"]
            for c in n.get("choices", [])
            if c.get("goto") == args[0]
        ]
        if refs:
            _warn(f"Des choix pointent vers ce nœud : {', '.join(refs)}")
            if not _confirm("Supprimer quand même ?"):
                return

        s["graph"]["nodes"] = [n for n in s["graph"]["nodes"] if n["id"] != args[0]]
        s["dirty"] = True
        _ok(f"Nœud '{args[0]}' supprimé.")

    # ── add_choice ────────────────────────────────────────────────
    def cmd_add_choice(ctx, args):
        if not _require_open(): return
        if not args:
            print("Usage: add_choice <node_id>")
            return
        s    = _state()
        node = _get_node(args[0])
        if node is None:
            _err(f"Nœud '{args[0]}' introuvable.")
            return

        _h(f"Nouveau choix → {node['id']}")
        choice_id = _prompt("ID du choix")
        if not choice_id:
            _err("ID obligatoire.")
            return

        text = _prompt("Texte du choix")

        # goto : liste des nœuds existants
        node_ids = [n["id"] for n in s["graph"]["nodes"]]
        _info(f"Nœuds disponibles : {', '.join(node_ids)}")
        goto = _prompt("goto (id du nœud cible)")
        if goto not in node_ids:
            _warn(f"Nœud '{goto}' inexistant — le choix sera invalide jusqu'à sa création.")

        cond = _build_condition(label="Condition du choix") if _confirm(
            "Ajouter une condition ?") else None

        choice: dict = {"id": choice_id, "text": text, "goto": goto}
        if cond is not None:
            choice["conditions"] = cond

        node.setdefault("choices", []).append(choice)
        s["dirty"] = True
        _ok(f"Choix '{choice_id}' ajouté à '{node['id']}'.")

    # ── edit_choice ───────────────────────────────────────────────
    def cmd_edit_choice(ctx, args):
        if not _require_open(): return
        if len(args) < 2:
            print("Usage: edit_choice <node_id> <choice_id>")
            return
        s    = _state()
        node = _get_node(args[0])
        if node is None:
            _err(f"Nœud '{args[0]}' introuvable.")
            return

        choices = node.get("choices", [])
        choice  = next((c for c in choices if c["id"] == args[1]), None)
        if choice is None:
            _err(f"Choix '{args[1]}' introuvable.")
            return

        _h(f"Édition choix {args[0]}.{args[1]}")
        field = _choose("Champ à éditer",
                        ["text", "goto", "conditions"], allow_empty=True)
        if field is None:
            return

        if field == "text":
            new_text = _prompt("Texte", default=choice["text"])
            if new_text:
                choice["text"] = new_text

        elif field == "goto":
            node_ids = [n["id"] for n in s["graph"]["nodes"]]
            _info(f"Nœuds : {', '.join(node_ids)}")
            new_goto = _prompt("goto", default=choice["goto"])
            if new_goto:
                if new_goto not in node_ids:
                    _warn(f"Nœud '{new_goto}' inexistant.")
                choice["goto"] = new_goto

        elif field == "conditions":
            cond = _build_condition(
                current=choice.get("conditions"),
                label="Condition du choix"
            )
            if cond is None:
                choice.pop("conditions", None)
                _info("Condition supprimée.")
            else:
                choice["conditions"] = cond

        s["dirty"] = True
        _ok("Choix mis à jour.")

    # ── del_choice ────────────────────────────────────────────────
    def cmd_del_choice(ctx, args):
        if not _require_open(): return
        if len(args) < 2:
            print("Usage: del_choice <node_id> <choice_id>")
            return
        s    = _state()
        node = _get_node(args[0])
        if node is None:
            _err(f"Nœud '{args[0]}' introuvable.")
            return

        before = len(node.get("choices", []))
        node["choices"] = [c for c in node.get("choices", [])
                           if c["id"] != args[1]]
        if len(node["choices"]) == before:
            _err(f"Choix '{args[1]}' introuvable.")
            return

        s["dirty"] = True
        _ok(f"Choix '{args[1]}' supprimé.")

    # ── edit_meta ─────────────────────────────────────────────────
    def cmd_edit_meta(ctx, args):
        if not _require_open(): return
        s    = _state()
        meta = s["meta"]

        _h("Édition mod.json")
        field = _choose("Champ",
                        ["name", "description", "version", "depends", "variables"],
                        allow_empty=True)
        if field is None:
            return

        if field in ("name", "description", "version"):
            val = _prompt(field, default=meta.get(field, ""))
            if val:
                meta[field] = val

        elif field == "depends":
            current = ", ".join(meta.get("depends", []))
            raw = _prompt("Dépendances (virgule)", default=current)
            meta["depends"] = [d.strip() for d in raw.split(",") if d.strip()]

        elif field == "variables":
            _h("Variables")
            vars_ = meta.setdefault("variables", {})
            for k, v in vars_.items():
                _info(f"  {k} = {json.dumps(v)}")

            action = _choose("Action",
                             ["Ajouter / modifier", "Supprimer"], allow_empty=True)
            if action == "Ajouter / modifier":
                key = _prompt("Nom de la variable")
                val = _parse_arg(_prompt("Valeur par défaut"))
                vars_[key] = val
                _ok(f"Variable '{key}' = {val!r}")
            elif action == "Supprimer":
                key = _prompt("Nom à supprimer")
                if key in vars_:
                    del vars_[key]
                    _ok(f"Variable '{key}' supprimée.")
                else:
                    _err(f"'{key}' introuvable.")

        s["dirty"] = True
        _ok("Métadonnées mises à jour.")

    # ── validate ─────────────────────────────────────────────────
    def cmd_validate(ctx, args):
        if not _require_open(): return
        s      = _state()
        graph  = s["graph"]
        errors = []
        warns  = []

        node_ids = {n["id"] for n in graph["nodes"]}

        for node in graph["nodes"]:
            nid = node.get("id", "???")

            if "text" not in node:
                errors.append(f"Nœud '{nid}' : champ 'text' manquant")

            for c in node.get("choices", []):
                cid  = c.get("id", "???")
                ref  = f"{nid}.{cid}"
                if "text" not in c:
                    errors.append(f"Choix {ref} : champ 'text' manquant")
                if "goto" not in c:
                    errors.append(f"Choix {ref} : champ 'goto' manquant")
                elif c["goto"] not in node_ids:
                    errors.append(f"Choix {ref} : goto '{c['goto']}' inexistant")
                if "id" not in c:
                    errors.append(f"Choix dans '{nid}' : 'id' manquant")

        # Nœuds sans choix et sans goto entrant (non-start)
        all_gotos = {c["goto"]
                     for n in graph["nodes"]
                     for c in n.get("choices", [])
                     if "goto" in c}
        for node in graph["nodes"]:
            if node["id"] == "start":
                continue
            if not node.get("choices") and node["id"] not in all_gotos:
                warns.append(f"Nœud '{node['id']}' : aucun choix et jamais ciblé (nœud mort ?)")

        if not node_ids:
            errors.append("Le graphe est vide")
        if "start" not in node_ids:
            errors.append("Nœud 'start' manquant")

        _h("Validation")
        if errors:
            for e in errors:
                _err(e)
        else:
            _ok("Aucune erreur structurelle.")
        if warns:
            for w in warns:
                _warn(w)
        if not warns and not errors:
            _info("Le graphe est propre.")
        print()

    # ── editor_save ───────────────────────────────────────────────
    def cmd_editor_save(ctx, args):
        if not _require_open(): return
        s = _state()

        # Validation automatique avant sauvegarde
        errors = []
        node_ids = {n["id"] for n in s["graph"]["nodes"]}
        for node in s["graph"]["nodes"]:
            for c in node.get("choices", []):
                if c.get("goto") not in node_ids:
                    errors.append(f"{node['id']}.{c.get('id')} → '{c.get('goto')}' inexistant")
        if errors:
            _err("Sauvegarde bloquée — erreurs de validation :")
            for e in errors:
                _err(f"  {e}")
            _info("Corrigez les erreurs ou utilisez 'validate' pour le détail.")
            return

        adv_dir = s["adv_dir"]
        try:
            (adv_dir / "graph.json").write_text(
                json.dumps(s["graph"], indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
            (adv_dir / "mod.json").write_text(
                json.dumps(s["meta"], indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except OSError as e:
            _err(f"Erreur d'écriture : {e}")
            return

        s["dirty"] = False
        _ok(f"Sauvegardé → {adv_dir}")

    # ── discard ───────────────────────────────────────────────────
    def cmd_discard(ctx, args):
        if not _require_open(): return
        s = _state()
        if not s["dirty"]:
            _info("Aucune modification à abandonner.")
            return
        if not _confirm("Abandonner toutes les modifications ?"):
            return
        # Recharger depuis le disque
        try:
            s["meta"]  = json.loads((s["adv_dir"] / "mod.json").read_text(encoding="utf-8"))
            s["graph"] = json.loads((s["adv_dir"] / "graph.json").read_text(encoding="utf-8"))
            s["dirty"] = False
            _ok("Modifications abandonnées — fichiers rechargés.")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            _err(f"Erreur de rechargement : {e}")

    # ════════════════════════════════════════════════════════════════
    # ENREGISTREMENT
    # ════════════════════════════════════════════════════════════════

    make_completer = cmd_api["make_completer"]

    # ── helpers locaux ────────────────────────────────────────────────

    def _node_ids(ctx):
        """Nœuds du graphe ouvert dans l'éditeur."""
        s = ctx.mod_states.get("editor", {})
        if not s.get("graph"):
            return []
        return [n["id"] for n in s["graph"]["nodes"]]

    def _complete_choice(text, all_args, ctx):
        """
        Complète le choice_id en fonction du node_id déjà tapé (all_args[0]).
        Cas manuel car le 2e argument dépend du 1er.
        """
        s = ctx.mod_states.get("editor", {})
        if not s.get("graph") or not all_args:
            return []
        node = next((n for n in s["graph"]["nodes"] if n["id"] == all_args[0]), None)
        if node is None:
            return []
        return [c["id"] for c in node.get("choices", [])
                if c["id"].startswith(text)]

    reg = cmd_api["register_command"]
    reg("editor.new_adventure", cmd_new_adventure, "Scaffolder une nouvelle aventure")
    # Pas de completer : saisie interactive guidée, pas d'argument CLI.

    reg("editor.edit",     cmd_edit,    "Ouvrir une aventure pour édition",
        completer=make_completer(Path("adventures")))

    reg("editor.editor",   cmd_editor,  "État de l'éditeur")
    reg("editor.nodes",    cmd_nodes,   "Lister les nœuds du graphe")
    reg("editor.add_node", cmd_add_node,"Ajouter un nœud")
    reg("editor.edit_meta",cmd_edit_meta,"Éditer mod.json")
    reg("editor.validate", cmd_validate,"Valider la cohérence du graphe")
    reg("editor.save",     cmd_editor_save, "Sauvegarder l'aventure")
    reg("editor.discard",  cmd_discard, "Abandonner les modifications")
    # Les 5 ci-dessus : pas d'argument ou saisie interactive → pas de completer.

    reg("editor.node",     cmd_node,    "Détail d'un nœud",
        completer=make_completer(_node_ids))

    reg("editor.edit_node",cmd_edit_node,"Éditer un nœud",
        completer=make_completer(_node_ids))

    reg("editor.del_node", cmd_del_node,"Supprimer un nœud",
        completer=make_completer(_node_ids))

    reg("editor.add_choice",cmd_add_choice,"Ajouter un choix à un nœud",
        completer=make_completer(_node_ids))

    reg("editor.edit_choice",cmd_edit_choice,"Éditer un choix",
        completer=_complete_choice)
    # Cas manuel : arg1 = node_id, arg2 = choice_id dépendant du node.
    # Tab sur arg1 → propose les nodes.
    # Tab sur arg2 → propose les choices du node tapé.
    # make_completer ne couvre pas ce cas, voir _complete_choice ci-dessus.

    reg("editor.del_choice",cmd_del_choice,"Supprimer un choix",
        completer=_complete_choice)
    # Même logique que edit_choice.
