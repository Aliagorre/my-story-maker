# main.py
# run_hybrid.py
#
# Point d'entrée hybride : CLI dans un thread secondaire,
# boucle UI dans le thread principal.
#
# POURQUOI DEUX THREADS
# ─────────────────────
# input() est bloquant et doit rester dans un thread secondaire.
# La boucle UI (pygame, tkinter, Qt…) doit être dans le thread principal
# — c'est une contrainte des toolkits graphiques sur macOS et Windows.
#
# CONTRAT AVEC LES MODS
# ─────────────────────
# Un mod qui veut fournir une boucle UI doit exposer dans mod_states :
#
#   ctx.mod_states["ui_run"] = fn(ctx, render_lock) → None
#
# Cette fonction est appelée dans le thread principal et bloque jusqu'à
# fermeture de la fenêtre.  Elle doit acquérir render_lock pendant le
# rendu et pendant chaque modification d'état issue de l'UI
# (clic sur un choix, etc.).
#
# Les mods qui ne font que réagir aux events engine (on_node_enter…)
# n'ont rien à faire — le lock est géré ici et dans le mod UI.
#
# THREAD-SAFETY
# ─────────────
# Le GIL Python protège les opérations atomiques sur les dicts.
# render_lock est un threading.Lock() classique acquis :
#   - dans le thread CLI, autour de chaque emit("on_cli_input")
#   - dans le thread UI, autour de chaque draw() et de chaque choose()
# Les handlers engine (on_node_enter, on_choice_selected…) s'exécutent
# sous le lock du côté qui a déclenché l'action — pas besoin de lock
# supplémentaire dans les mods métier.

import threading
from core import Context, ModLoader
from core.errors import EngineError


def run_hybrid():
    # ── Chargement des mods ───────────────────────────────────────
    context = Context()
    try:
        loader   = ModLoader(context)
        warnings = loader.load_mods_from_folder("mods")
        for w in warnings:
            print(f"[warn] {w}")
    except EngineError as e:
        print(f"[erreur fatale] Impossible de charger les mods : {e}")
        return

    if not context.mod_states.get("mods_loaded"):
        print("[warn] Aucun mod chargé.")

    # ── Lock partagé ──────────────────────────────────────────────
    # Distribué aux deux parties (CLI thread + UI run).
    # Si aucun mod UI n'est chargé, on utilise nullcontext()
    # pour que le thread CLI fonctionne exactement comme run_CLI.
    render_lock = threading.Lock()
    context.mod_states["render_lock"] = render_lock

    # ── Thread CLI ────────────────────────────────────────────────
    _stop = threading.Event()   # signalé quand la boucle UI se ferme

    def cli_thread():
        while not _stop.is_set():
            try:
                raw = input("> ").strip()
            except KeyboardInterrupt:
                # ^C annule la saisie, on continue
                print()
                continue
            except EOFError:
                # Fin de stdin (^D, pipe) → arrêt propre
                _stop.set()
                break

            if not raw:
                continue

            # On acquiert le lock pour que emit() et un éventuel draw()
            # ne s'exécutent pas en même temps.
            with render_lock:
                try:
                    context.events.emit("on_cli_input", context, raw)
                except SystemExit:
                    _stop.set()
                    break
                except EngineError as e:
                    print(f"[erreur] {e}")
                except Exception as e:
                    print(f"[erreur inattendue] {type(e).__name__}: {e}")

    t = threading.Thread(target=cli_thread, daemon=True, name="cli")
    t.start()

    # ── Boucle UI (thread principal) ──────────────────────────────
    ui_run = context.mod_states.get("ui_run")

    if ui_run is not None:
        # Un mod UI est chargé : il prend la main ici.
        # Il doit signaler _stop ou lever SystemExit pour sortir.
        try:
            ui_run(context, render_lock)
        except SystemExit:
            pass
        except Exception as e:
            print(f"[erreur UI] {type(e).__name__}: {e}")
        finally:
            _stop.set()
    else:
        # Pas de mod UI : on attend juste la fin du thread CLI.
        # Comportement identique à run_CLI.
        try:
            t.join()
        except KeyboardInterrupt:
            _stop.set()

    # ── Sortie propre ─────────────────────────────────────────────
    _stop.set()
    t.join(timeout=2)

    print("\nAu revoir.")
    try:
        with render_lock:
            context.events.emit("on_exit", context)
    except (SystemExit, Exception):
        pass


if __name__ == "__main__":
    run_hybrid()