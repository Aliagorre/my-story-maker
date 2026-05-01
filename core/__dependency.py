# core/__dependency.py

from collections import defaultdict
from heapq import heappop, heappush

from core.__mod_storage import ModStorage
from core.__version import ConstraintResolver
from resources.EVENTS import MOD_CONFLICT, MOD_DEPENDENCY_ERROR
from resources.LOG_LEVELS import DEBUG


class DependencyGraphBuilder:
    @staticmethod
    def build(mod_storage: ModStorage) -> dict:
        """
        Return dependencies graph
        """
        graph = {}
        for mod, manifest in mod_storage.manifests.items():
            requires = manifest.get("requires", {})
            graph[mod] = list(requires.keys())
        mod_storage.dependencies = graph
        return graph


class DependencyChecker:
    @staticmethod
    def check(mod_storage: ModStorage, emit_error) -> None:
        """
        Disable mods if miss dependencies
        """
        for mod in mod_storage.dependencies:
            if mod_storage.states.get(mod) == "disable":
                continue
            requires = mod_storage.manifests[mod]["requires"]
            for dep, constraints in requires.items():
                if dep not in mod_storage.manifests:
                    mod_storage.states[mod] = "disable"
                    emit_error(MOD_DEPENDENCY_ERROR, {"mod": mod, "missing": dep})
                    continue
                if mod_storage.states.get(dep) == "disable":
                    mod_storage.states[mod] = "disable"
                    emit_error(MOD_DEPENDENCY_ERROR, {"mod": mod, "disabled_dep": dep})
                    continue
                if constraints == "*":
                    continue
                if not isinstance(constraints, list):
                    mod_storage.states[mod] = "disable"
                    emit_error(
                        MOD_DEPENDENCY_ERROR,
                        {
                            "mod": mod,
                            "dep": dep,
                            "invalid_constraint_format": constraints,
                        },
                    )
                    continue
                dep_version = mod_storage.manifests[dep]["version"]
                if not ConstraintResolver.satisfies(dep_version, constraints):
                    mod_storage.states[mod] = "disable"
                    emit_error(
                        MOD_DEPENDENCY_ERROR,
                        {
                            "mod": mod,
                            "dep": dep,
                            "constraint": constraints,
                            "found": dep_version,
                        },
                    )


class ConflictChecker:
    @staticmethod
    def check(mod_storage: ModStorage, emit_error) -> None:
        """
        Disable mods if in conflict with other
        """
        for mod in mod_storage.manifests:
            if mod_storage.states.get(mod) == "disable":
                continue
            conflicts = mod_storage.manifests[mod].get("conflicts", {})
            for target, constraints in conflicts.items():
                if target not in mod_storage.manifests:
                    continue
                if mod_storage.states.get(target) == "disable":
                    continue
                target_version = mod_storage.manifests[target]["version"]
                if ConstraintResolver.satisfies(target_version, constraints):
                    mod_storage.states[mod] = "disable"
                    emit_error(
                        MOD_CONFLICT,
                        {
                            "mod": mod,
                            "conflict_with": target,
                            "constraint": constraints,
                        },
                    )


class CycleDetector:
    @staticmethod
    def detect(graph):
        """
        Return cycle dependencies
        """
        state = {}
        cycles = set()

        def dfs(node, stack):
            if state.get(node) == "visiting":
                if node in stack:
                    idx = stack.index(node)
                    cycles.update(stack[idx:])
                return
            if state.get(node) == "visited":
                return
            state[node] = "visiting"
            for dep in graph.get(node, []):
                dfs(dep, stack + [dep])
            state[node] = "visited"

        for node in graph:
            if state.get(node) is None:
                dfs(node, [node])
        return cycles


class PriorityTopoSorter:
    @staticmethod
    def sort(graph, mod_storage, active_mods) -> list:
        """
        Return list of mod ordered for loading.
        """
        # dep -> [mods qui en dépendent]
        adj = defaultdict(list)
        indegree = {m: 0 for m in active_mods}
        # Construction correcte
        for mod in active_mods:
            for dep in graph.get(mod, []):
                if dep in indegree:
                    adj[dep].append(mod)  # dep → mod
                    indegree[mod] += 1
        # heap = ( -priority, name )
        heap = []
        for mod in active_mods:
            if indegree[mod] == 0:
                prio = mod_storage.manifests[mod].get("priority", 0)
                heappush(heap, (-prio, mod))
        order = []
        while heap:
            _, mod = heappop(heap)
            order.append(mod)
            for dependent in adj[mod]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    prio = mod_storage.manifests[dependent].get("priority", 0)
                    heappush(heap, (-prio, dependent))
        return order


class DependencyModule:
    def __init__(self, log, emit_error):
        self.emit_error = emit_error
        self.log = log

    def run(self, mod_storage: ModStorage) -> None:
        """
        complete mod_storage.load_order
        disable conflict mod and circular dependencies
        """
        graph = DependencyGraphBuilder.build(mod_storage)
        DependencyChecker.check(mod_storage, self.emit_error)
        ConflictChecker.check(mod_storage, self.emit_error)
        cycles = CycleDetector.detect(graph)
        for mod in cycles:
            mod_storage.states[mod] = "disable"
            self.log(DEBUG, f"cycle dependencies from {mod}")
            self.emit_error(MOD_DEPENDENCY_ERROR, {"cycle": mod})
        active_mods = [
            m for m in mod_storage.manifests if mod_storage.states.get(m) != "disable"
        ]
        final_order = PriorityTopoSorter.sort(graph, mod_storage, active_mods)
        mod_storage.load_order = final_order
