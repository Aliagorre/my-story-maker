\# my-story-maker/docs/core/DEPENDENCY_RESOLUTION.md

# StoryMaker V7 — Dependency Resolution Specification

## 1. Introduction

Dependency resolution is one of the most sensitive mechanisms of the core. It ensures that:

* mods are loaded in a valid order,
* all dependencies are satisfied,
* version constraints are compatible,
* conflicts are detected,
* no dependency cycles can block the engine,
* problematic mods are safely disabled.

The system must be:

* **strict** (no ambiguity),
* **deterministic** (same input → same output),
* **robust** (never crashes the engine),
* **transparent** (clear logs and events).

---

## 2. Types of dependencies

### 2.1 Declared dependencies (`requires`)

In the manifest:

```json
"requires": {
  "mod_script_engine": ">=1.0.0,<2.0.0"
}
```

Each dependency specifies:

* a required mod,
* a SemVer version constraint.

---

### 2.2 Declared conflicts (`conflicts`)

```json
"conflicts": {
  "mod_old_graph": "*"
}
```

A conflict means:

* the mod cannot coexist with another mod,
* or not with specific versions of that mod.

---

### 2.3 Implicit dependencies

Some dependencies are implicit:

* `mods_core` must be loaded before regular mods,
* critical services must be available before dependent mods initialize.

---

## 3. Full resolution pipeline

The core follows a strict pipeline:

```
1. Collect manifests
2. Build dependency graph
3. Check missing dependencies
4. Check version mismatches
5. Check conflicts
6. Detect cycles
7. Topological sort
8. Priority sort
9. Final load order
```

Each step is described below.

---

## 4. Graph construction

The core builds a directed graph:

* each mod = a node,
* each dependency = an edge `A → B` (A depends on B).

Example:

```
mod_graph_editor → mod_script_engine
mod_script_engine → mod_error_and_log
```

Internal representation:

```python
dependencies = {
  "mod_graph_editor": ["mod_script_engine"],
  "mod_script_engine": ["mod_error_and_log"],
}
```

---

## 5. Missing dependency check

For each declared dependency:

* if the required mod does not exist → error,
* if the required mod is disabled → error.

On error:

* log `[ERROR]`,
* emit `MOD_DEPENDENCY_ERROR`,
* disable the mod.

---

## 6. Version compatibility check

For each dependency:

* the core validates the SemVer constraint,
* if the installed version does not match → error.

Example:

```
requires: ">=1.0.0,<2.0.0"
installed version: "2.1.0"
→ incompatible
```

On error:

* disable the mod,
* emit `MOD_DEPENDENCY_ERROR`.

---

## 7. Conflict detection

For each declared conflict:

* if the conflicting mod is present → error,
* if the version matches the constraint → error.

Example:

```json
"conflicts": {
  "mod_graph": "<1.5.0"
}
```

If `mod_graph` version `1.2.0` is installed → conflict.

On conflict:

* disable the mod,
* emit `MOD_CONFLICT`.

---

## 8. Cycle detection

The core ensures there are **no cycles** in the dependency graph.

Example of a cycle:

```
A → B
B → C
C → A
```

On detection:

* all involved mods are disabled,
* emit `MOD_DEPENDENCY_ERROR`.

---

## 9. Topological sorting

Once the graph is valid, the core performs a **topological sort** to compute a valid load order.

Example:

```
mod_error_and_log
mod_script_engine
mod_graph_editor
```

This guarantees:

* a mod is always loaded after its dependencies,
* no ambiguity,
* deterministic output.

---

## 10. Priority sorting

After topological sorting, mods are ordered by:

1. `priority` (from manifest),
2. alphabetical order as tie-breaker.

Example:

```
mod_error_and_log   (priority 900)
mod_cmd             (priority 100)
mod_graph_editor    (priority 50)
```

Dependencies always override priority.

---

## 11. Final load order

The final order respects:

1. dependencies,
2. priorities,
3. alphabetical ordering.

Example:

```
mod_error_and_log
mod_script_engine
mod_cmd
mod_graph_editor
```

---

## 12. Disabled mods

A mod is disabled if:

* invalid manifest,
* missing dependency,
* incompatible version,
* declared conflict,
* dependency cycle,
* error in `on_load`,
* error in `on_init`.

A disabled mod:

* is not loaded,
* is not initialized,
* is not accessible via `core.get_mod()`,
* may still appear in logs as disabled.

---

## 13. Summary

| Step         | Purpose                         |
| ------------ | ------------------------------- |
| Graph        | Represent dependencies          |
| Dependencies | Validate existence and versions |
| Conflicts    | Detect incompatibilities        |
| Cycles       | Ensure graph validity           |
| Topo sort    | Compute logical order           |
| Priority     | Refine final order              |
| Disable      | Ensure engine safety            |

Dependency resolution is **strictly deterministic**, **robust**, **predictable**, and guarantees engine stability.
