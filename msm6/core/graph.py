# core/graph.py
from core.errors import EngineError
from core.context import Context
from typing import Dict, Any, List

class Graph:
    def __init__(self, data: Dict[str, Any]):
        if "nodes" not in data:
            raise EngineError("Graph data is missing 'nodes' key")

        seen = {}
        for n in data["nodes"]:
            if n["id"] in seen:
                raise EngineError(f"Duplicate node id '{n['id']}'")
            seen[n["id"]] = n

        self.nodes = seen
        self.validate()

    def get_node(self, node_id: str) -> Dict[str, Any]:
        if node_id not in self.nodes:
            raise EngineError(f"Node '{node_id}' not found")
        return self.nodes[node_id]

    def get_choices(self, node: Dict[str, Any] | None, context: Context) -> List[Dict[str, Any]]:
        if node is None:
            raise EngineError("Cannot get choices: node is None")
        if not hasattr(context, "condition_engine"):
            raise EngineError("Invalid context: missing condition_engine")
        result = []
        for c in node.get("choices", []):
            cond = c.get("conditions")
            if cond is None or context.condition_engine.evaluate(cond):
                if "goto" not in c:
                    raise EngineError(f"Choice in node '{node['id']}' missing 'goto'")
                result.append(c)
        return result

    def find_choice_by_id(self, node: Dict[str, Any] | None, choice_id: str, context: Context) -> Dict[str, Any]:
        if node is None:
            raise EngineError("Cannot find choice: node is None")
        for c in self.get_choices(node, context):
            if "id" not in c:
                raise EngineError(f"Choice in node '{node['id']}' missing 'id'")
            if c["id"] == choice_id:
                return c
        raise EngineError(f"Choice id '{choice_id}' not available in current node")

    def validate(self):
        if not self.nodes:
            raise EngineError("Graph has no nodes")
        for node_id, node in self.nodes.items():
            if "text" not in node:
                raise EngineError(f"Node '{node_id}' missing 'text'")
            if "id" not in node:
                raise EngineError(f"Node '{node_id}' missing 'id'")
            for c in node.get("choices", []):
                if "text" not in c:
                    raise EngineError(f"Choice in node '{node_id}' missing 'text'")
                if "goto" not in c:
                    raise EngineError(f"Choice in node '{node_id}' missing 'goto'")
                if "id" not in c:
                    raise EngineError(f"Choice in node '{node_id}' missing 'id'")
                if c["goto"] not in self.nodes:
                    raise EngineError(f"Choice in node '{node_id}' points to unknown node '{c['goto']}'")
