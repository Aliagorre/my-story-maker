# core/__dependency.py

from collections import defaultdict, deque

from core.__mod_storage import ModStorage
from core.__version import ConstraintResolver


class DependencyGraphBuilder:
    @staticmethod
    def build(mod_storage: ModStorage):
        graph = {}
        for mod, manifest in mod_storage.manifests.items():
            requires = manifest.get("requires", {})
            graph[mod] = list(requires.keys())
        mod_storage.dependencies = graph
        return graph

class DependencyChecker:
    @staticmethod
    def check(mod_storage: ModStorage, emit_error):
        for mod in mod_storage.dependencies:
            if mod_storage.states.get(mod) == "disable":
                continue
            requires = mod_storage.manifests[mod]["requires"]
            for dep, constraints in requires.items():
                if dep not in mod_storage.manifests:
                    mod_storage.states[mod] = "disable"
                    emit_error("MOD_DEPENDENCY_ERROR", {
                        "mod": mod,
                        "missing": dep
                    })
                    continue
                if mod_storage.states.get(dep) == "disable":
                    mod_storage.states[mod] = "disable"
                    emit_error("MOD_DEPENDENCY_ERROR", {
                        "mod": mod,
                        "disabled_dep": dep
                    })
                    continue
                dep_version = mod_storage.manifests[dep]["version"]
                if not ConstraintResolver.satisfies(dep_version, constraints):
                    mod_storage.states[mod] = "disable"
                    emit_error("MOD_DEPENDENCY_ERROR", {
                        "mod": mod,
                        "dep": dep,
                        "constraint": constraints,
                        "found": dep_version
                    })

class ConflictChecker:
    @staticmethod
    def check(mod_storage: ModStorage, emit_error):
        for mod in mod_storage.manifests:
            if mod_storage.states.get(mod) == "disable":
                continue
            conflicts = mod_storage.manifests[mod].get("conflicts", {})
            for target, constraints in conflicts.items():
                if target not in mod_storage.manifests:
                    continue
                target_version = mod_storage.manifests[target]["version"]
                if ConstraintResolver.satisfies(target_version, constraints):
                    mod_storage.states[mod] = "disable"
                    emit_error("MOD_CONFLICT", {
                        "mod": mod,
                        "conflict_with": target,
                        "constraint": constraints
                    })

class CycleDetector:
    @staticmethod
    def detect(graph):
        state = {}  # None / visiting / visited
        cycles = set()
        def dfs(node, stack):
            if state.get(node) == "visiting":
                cycles.update(stack)
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

class TopologicalSorter:
    @staticmethod
    def sort(graph, active_mods):
        indegree = defaultdict(int)
        for mod in graph:
            for dep in graph[mod]:
                indegree[dep] += 1
        queue = deque([m for m in active_mods if indegree[m] == 0])
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)

            for dep in graph.get(node, []):
                indegree[dep] -= 1
                if indegree[dep] == 0:
                    queue.append(dep)
        return order

class PrioritySorter:
    @staticmethod
    def sort(order, mod_storage):
        return sorted(
            order,
            key=lambda m: (
                -mod_storage.manifests[m].get("priority", 0),
                m
            )
        )

class DependencyModule:
    def __init__(self, emit_error, log):
        self.emit_error = emit_error
        self.log = log

    def run(self, mod_storage: ModStorage):
        graph = DependencyGraphBuilder.build(mod_storage)
        DependencyChecker.check(mod_storage, self.emit_error)
        ConflictChecker.check(mod_storage, self.emit_error)
        cycles = CycleDetector.detect(graph)
        for mod in cycles:
            mod_storage.states[mod] = "disable"
            self.emit_error("MOD_DEPENDENCY_ERROR", {"cycle": mod})
        active_mods = [
            m for m in mod_storage.manifests
            if mod_storage.states.get(m) != "disable"
        ]
        topo_order = TopologicalSorter.sort(graph, active_mods)
        final_order = PrioritySorter.sort(topo_order, mod_storage)
        mod_storage.load_order = final_order
        mod_storage.load_order = final_order
