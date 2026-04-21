\# my-story-maker/docs/core/MOD_LOADER.md

# StoryMaker V7 — Mod Loader Specification

## 1. Introduction

The **Mod Loader** is the core component responsible for:

- discovering mods,
- reading and validating their manifests,
- resolving dependencies,
- detecting conflicts,
- determining load order,
- dynamically loading entrypoints,
- instantiating mods,
- executing lifecycle hooks (`on_load`, `on_init`, `on_shutdown`),
- handling errors,
- safely disabling problematic mods.

The Mod Loader must be:

- **strict** (rigorous validation),
- **robust** (never crash),
- **deterministic** (predictable load order),
- **transparent** (clear logs),
- **extensible** (future support for plugins, hot-reload, etc.).

---

## 2. Mod Loading Lifecycle

The Mod Loader follows a strict pipeline:

```

1. Discovery
2. Manifest reading
3. Manifest validation
4. Dependency resolution
5. Conflict detection
6. Load order computation
7. Loading (on_load)
8. Initialization (on_init)

```

Each step is described below.

---

## 3. Mod Discovery

The Mod Loader scans the following directories:

```

/core/default_mods/
/mods/
/mods/default/

```

A folder is recognized as a mod if:

- it starts with `mod_`,
- it contains a `manifest.json`,
- it contains a valid `entrypoint`.

For each discovered mod, the core emits:

```

MOD_DISCOVERED

```

---

## 4. Manifest Reading

For each mod, the Mod Loader:

- opens `manifest.json`,
- parses the JSON,
- verifies required fields,
- stores data in an internal structure.

On error:

- logs `[ERROR]`,
- emits `MOD_MANIFEST_ERROR`,
- disables the mod.

---

## 5. Manifest Validation

The Mod Loader checks:

- `name` (format `mod_xxx`),
- `version` (strict SemVer),
- `type` (allowed value),
- `priority` (integer),
- `entrypoint` (existing file),
- `permissions` (valid list),
- `requires` (SemVer format),
- `conflicts` (SemVer format).

On failure:

- mod is disabled,
- `MOD_MANIFEST_ERROR` event is emitted.

---

## 6. Dependency Resolution

The Mod Loader builds a directed graph:

- each mod = a node,
- each dependency = an edge.

It checks:

- missing dependencies,
- incompatible versions,
- cyclic dependencies,
- declared conflicts,
- unsatisfiable constraints.

On error:

- mod is disabled,
- `MOD_DEPENDENCY_ERROR` event is emitted.

Once validated, the loader computes final order using:

- topological sorting,
- then priority sorting.

---

## 7. Conflict Detection

The Mod Loader checks:

- conflicts declared in manifests,
- implicit conflicts (e.g. multiple mods providing the same critical service),
- version conflicts.

On conflict:

- mod is disabled,
- `MOD_CONFLICT` event is emitted.

---

## 8. Load Order Computation

Final order respects:

1. dependencies (highest priority),
2. `priority` value,
3. alphabetical order as a fallback.

Example:

```

mod_error_and_log   (priority 900)
mod_cmd             (priority 100)
mod_graph_editor    (priority 50)

```

---

## 9. Mod Loading (`on_load`)

For each mod, in computed order:

1. dynamic import of entrypoint (`importlib`),
2. instantiation of the main class,
3. execution of hook:

```

on_load(core)

```

At this stage:

- mods may subscribe to events,
- mods may register services,
- mods may read their manifest,
- mods must not yet execute business logic.

On error:

- `MOD_ERROR` event is emitted,
- mod is disabled.

---

## 10. Mod Initialization (`on_init`)

After all mods are loaded:

- the Mod Loader calls `on_init(core)` for each mod,
- in the same order as `on_load`.

At this stage:

- services are available,
- dependencies are guaranteed,
- mods can initialize internal state,
- mods can load resources.

On error:

- `MOD_ERROR` event is emitted,
- mod may be disabled if necessary.

---

## 11. Mod Shutdown (`on_shutdown`)

During engine shutdown:

1. `ENGINE_SHUTDOWN` event is emitted,
2. `on_shutdown(core)` is called for each mod,
3. in **reverse load order**.

Mods must:

- release resources,
- close files,
- stop threads,
- persist state if needed.

---

## 12. Error Handling

### 12.1 Mod Errors

- caught safely,
- logged,
- `MOD_ERROR` event emitted,
- mod disabled if necessary.

### 12.2 Critical Errors

If an error prevents the engine from continuing:

- `ENGINE_FATAL_ERROR` event,
- immediate shutdown.

---

## 13. Hot-Reload (Future)

The Mod Loader is designed to support:

- reloading a mod without restarting the engine,
- reloading a service,
- reloading scripts.

This feature will be introduced in a future version.

---

## 14. Summary

| Step | Role |
|------|------|
| Discovery | Find mods |
| Reading | Load manifests |
| Validation | Verify structure |
| Dependencies | Check versions and cycles |
| Conflicts | Detect incompatibilities |
| Order | Compute load sequence |
| on_load | Load mods |
| on_init | Initialize mods |
| on_shutdown | Clean up mods |

The Mod Loader is **strict**, **robust**, **deterministic**, and **predictable**.

