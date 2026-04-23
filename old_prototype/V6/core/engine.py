# core/engine.py
import json
from typing import Any, Dict, List

from core.context import Context
from core.errors import EngineError
from core.graph import Graph
from EVENTS import EventBus


class Engine:
    def __init__(self, graph: Graph, context: Context, events: EventBus):
        self.graph   = graph
        self.context = context
        self.events  = events
        # FIX #10 : _in_node_actions n'était pas initialisé dans __init__ ;
        # getattr(self, "_in_node_actions", False) masquait le problème mais
        # l'attribut pouvait ne jamais exister formellement.
        self._in_node_actions: bool = False  # FIX #10

    def start(self, start_node_id: str) -> None:
        self.context.current_node = start_node_id
        self.events.emit("on_game_start", self.context)
        self.enter_node(start_node_id)

    def get_current_node(self) -> Dict[str, Any] | None:
        if self.context.current_node is None:
            self.events.emit_error("No current node set")
            return None
        return self.graph.get_node(self.context.current_node)

    def get_current_choices(self) -> List[Dict[str, Any]]:
        node = self.get_current_node()
        return self.graph.get_choices(node, self.context)

    def choose(self, choice_index: int) -> None:
        node = self.get_current_node()
        if node is None:
            return
        choices = self.graph.get_choices(node, self.context)
        if not (0 <= choice_index < len(choices)):
            self.events.emit_error(f"Invalid choice index {choice_index}")
            return
        self._apply_choice(choices[choice_index])

    def choose_by_id(self, choice_id: str) -> None:
        node = self.get_current_node()
        if node is None:
            return
        try:
            choice = self.graph.find_choice_by_id(node, choice_id, self.context)
        except EngineError as e:
            self.events.emit_error(str(e))
            return
        self._apply_choice(choice)

    def _execute_node_actions(self, node: Dict, key: str) -> None:
        self._in_node_actions = True
        try:
            actions = self.context.mod_states.get("actions", {})
            for action in node.get(key, []):
                if not isinstance(action, dict):
                    self.events.emit_error(f"Invalid action: {action!r}")
                    continue
                cond = action.get("conditions")
                if cond is not None and not self.context.condition_engine.evaluate(cond):
                    continue
                action_items = {k: v for k, v in action.items() if k != "conditions"}
                if len(action_items) != 1:
                    self.events.emit_error(f"Each action must have exactly one key: {action!r}")
                    continue
                name, args = next(iter(action_items.items()))
                if name not in actions:
                    self.events.emit_error(f"Unknown action '{name}'")
                    continue
                actions[name](self.context, args)
        finally:
            self._in_node_actions = False

    def enter_node(self, node_id: str) -> None:
        if self._in_node_actions:
            self.events.emit_error("enter_node() cannot be called from on_enter")
            return
        node = self.graph.get_node(node_id)
        self.context.current_node = node_id
        self._execute_node_actions(node, "on_enter")
        self.events.emit("on_node_enter", self.context, node)

    def _restore_node(self, node_id: str) -> None:
        """
        FIX #9 — Restaure le nœud courant après un load_game SANS rejouer
        les actions on_enter.

        enter_node() rejoue on_enter à chaque appel, ce qui est correct lors
        d'une navigation normale mais corrompt un état restauré depuis une
        sauvegarde (les effets de bord — décrémenter des stats, émettre des
        événements, modifier le state — seraient exécutés une seconde fois).

        _restore_node() se contente de pointer current_node et d'émettre
        on_node_enter pour que les mods d'affichage (UI, narrateur…) puissent
        rafraîchir leur vue sans altérer le state du jeu.
        """
        node = self.graph.get_node(node_id)
        self.context.current_node = node_id
        self.events.emit("on_node_enter", self.context, node)

    def _apply_choice(self, choice: Dict[str, Any]) -> None:
        current_node = self.graph.get_node(self.context.current_node)
        self._execute_node_actions(current_node, "on_quit")
        self.events.emit("on_choice_selected", self.context, choice)
        self.enter_node(choice["goto"])

    def save_game(self, path: str) -> None:
        # Laisser les mods déposer leurs données dans context.save_data
        self.context.save_data = {}
        self.events.emit("on_save", self.context)

        data = {
            "state":        self.context.state,
            "save_data":    self.context.save_data,
            "current_node": self.context.current_node,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_game(self, path: str) -> None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.events.emit_error(f"Invalid save file '{path}': {e}")
            return
        except FileNotFoundError:
            self.events.emit_error(f"Save file not found: '{path}'")
            return

        state        = data.get("state", {})
        save_data    = data.get("save_data", {})
        current_node = data.get("current_node")

        if not isinstance(state, dict):
            self.events.emit_error("Invalid save: 'state' must be a dict")
            return
        if current_node is None:
            self.events.emit_error("Save file has no current_node")
            return

        try:
            self.graph.get_node(current_node)
        except EngineError as e:
            self.events.emit_error(f"Save refers to unknown node '{current_node}'"f"from {e}")
            return

        old_state    = self.context.state
        old_node     = self.context.current_node
        old_savedata = getattr(self.context, "save_data", {})

        self.context.state        = state
        self.context.save_data    = save_data
        self.context.current_node = current_node
        try:
            # Les mods reconstruisent leur état depuis ctx.save_data
            self.events.emit("on_load", self.context)
        except Exception as e:
            self.context.state        = old_state
            self.context.save_data    = old_savedata
            self.context.current_node = old_node
            self.events.emit_error(f"Load failed during on_load handlers: {e}")
            return
        self._restore_node(current_node)  # FIX #9

def load_graph_from_file(path: str) -> Graph:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise EngineError(f"Invalid graph file '{path}': {e}") from e
    except FileNotFoundError:
        raise EngineError(f"Graph file not found: '{path}'")
    return Graph(data)

    return Graph(data)

