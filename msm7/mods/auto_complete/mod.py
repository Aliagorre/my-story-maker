# mods/autocomplete/mod.py
#
# COMMENT ÇA MARCHE
# ════════════════════════════════════════════════════════════════════
#
# Ce mod configure readline pour intercepter la touche Tab.
# À chaque Tab, readline appelle _completer(text, state) :
#   text  = le mot courant que l'utilisateur est en train de taper
#   state = index du candidat demandé (readline appelle 0, 1, 2…
#           jusqu'à ce qu'on retourne None)
#
# NAVIGATION DE L'ARBRE
# ─────────────────────
# On lit le buffer complet (readline.get_line_buffer()) pour savoir
# où on en est dans la saisie, puis on descend l'arbre des commandes
# mot par mot :
#
#   "adv"              → on est à la racine, on filtre par "adv"
#                        → ["adventure"]
#   "adventure "       → on est entré dans le dossier "adventure",
#                        espace final = mot complet, proposer ses enfants
#                        → ["list", "load", "save", "start"]
#   "adventure s"      → dans "adventure", fragment "s"
#                        → ["save", "start"]
#   "adventure start " → "adventure.start" est une commande,
#                        on appelle son completer déclaré
#                        → noms dans adventures/
#   "help adv"         → "help" est une commande avec son propre completer
#                        → ["adventure"]
#
# OÙ DÉCLARER L'AUTOCOMPLÉTION D'UNE COMMANDE
# ─────────────────────────────────────────────
# Directement dans register_command(), pas ici.
# C'est le code qui crée la commande qui sait ce qu'elle attend.
#
#   cmd_api["register_command"](
#       "mon_mod.ma_cmd",
#       ma_fonction,
#       "Description",
#       completer=lambda text, all_args, ctx: [...]  # ← ici
#   )
#
# Si completer=None (défaut), Tab ne propose rien après la commande.
# Ce mod n'a pas besoin d'être modifié pour supporter une nouvelle commande.
#
# ════════════════════════════════════════════════════════════════════

def register(ctx):
    cmd_api = ctx.mod_states.get("cmd_api")
    if cmd_api is None:
        raise RuntimeError("autocomplete requires cmd to be loaded first")

    # ----------------------------------------------------------------
    # Import readline
    # ----------------------------------------------------------------
    try:
        import readline
    except ImportError:
        try:
            import pyreadline3 as readline
        except ImportError:
            ctx.events.emit_warning(
                "autocomplete: readline non disponible — "
                "installez 'pyreadline3' sur Windows."
            )
            return   # mod inactif, pas d'erreur fatale

    # ----------------------------------------------------------------
    # Navigation de l'arbre
    # ----------------------------------------------------------------

    def _walk(tree: dict, parts: list):
        """
        Descend dans l'arbre mot par mot.
        S'arrête dès qu'un nœud est une commande (les mots suivants = args)
        ou qu'un mot est inconnu.

        Retourne (nœud_courant, mots_restants_non_consommés).

        Exemples avec l'arbre {adventure: {start: {is_command}, list: {is_command}}} :
          _walk(tree, ["adventure", "start"])
              → (nœud start, [])          ← commande trouvée
          _walk(tree, ["adventure"])
              → (nœud adventure, [])      ← dossier, pas de reste
          _walk(tree, ["adventure", "x"])
              → (nœud adventure, ["x"])   ← "x" inconnu, on s'arrête dans adventure
        """
        node = tree
        for i, p in enumerate(parts):
            if not isinstance(node, dict):
                return node, parts[i:]
            if node.get("is_command"):
                # On est sur une commande, tout ce qui suit = arguments
                return node, parts[i:]
            if p not in node:
                # Mot inconnu dans ce dossier, on retourne le dossier courant
                return node, parts[i:]
            node = node[p]
        return node, []

    def _folder_candidates(node: dict, prefix: str) -> list[str]:
        """Retourne les clés d'un dossier commençant par prefix."""
        if not isinstance(node, dict) or node.get("is_command"):
            return []
        return sorted(k for k in node.keys() if k.startswith(prefix))

    # ----------------------------------------------------------------
    # Completer principal
    # ----------------------------------------------------------------

    def _completer(text, state):
        try:
            candidates = _get_candidates(text)
            return candidates[state] if state < len(candidates) else None
        except Exception:
            return None   # ne jamais laisser remonter dans readline

    def _get_candidates(text: str) -> list[str]:
        buf   = readline.get_line_buffer().lstrip()
        parts = buf.split()
        tree  = cmd_api["list_commands"](ctx)

        # ── cas 1 : buffer vide ou 1er mot en cours ──────────────
        # On est à la racine, on complète le nom de dossier/commande.
        if not parts or (len(parts) == 1 and not buf.endswith(" ")):
            return _folder_candidates(tree, text)

        # ── cas 2 : espace final (dernier mot entièrement tapé) ───
        # Tous les mots sont complets, on propose la suite.
        if buf.endswith(" "):
            node, remaining = _walk(tree, parts)

            if isinstance(node, dict) and node.get("is_command"):
                # On est sur une commande : appeler son completer
                return _call_completer(node, text, remaining, ctx)
            else:
                # On est dans un dossier : proposer ses enfants
                return _folder_candidates(node, "")

        # ── cas 3 : mot partiel en fin de buffer ──────────────────
        # parts[-1] est en cours de frappe, parts[:-1] sont complets.
        complete_parts = parts[:-1]
        node, remaining = _walk(tree, complete_parts)

        if isinstance(node, dict) and node.get("is_command"):
            # Déjà sur une commande (ex: "help ad"),
            # le fragment courant est un argument → appeler son completer
            return _call_completer(node, text, remaining + [text], ctx)
        else:
            # Dans un dossier, filtrer ses enfants par le fragment
            return _folder_candidates(node, text)

    def _call_completer(cmd_node: dict, text: str,
                        all_args: list, ctx) -> list[str]:
        """
        Appelle le completer déclaré sur le nœud de commande.
        Si aucun n'est déclaré, retourne [].
        """
        completer = cmd_node.get("completer")
        if completer is None:
            return []
        try:
            result = completer(text, all_args, ctx)
            return result if result is not None else []
        except Exception:
            return []

    # ----------------------------------------------------------------
    # Configuration readline
    # ----------------------------------------------------------------

    readline.set_completer(_completer)
    # Seul \t est délimiteur : l'espace fait partie du buffer
    # et on le gère nous-mêmes via get_line_buffer().
    readline.set_completer_delims("\t")
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set editing-mode emacs")
    readline.parse_and_bind("set completion-ignore-case on")