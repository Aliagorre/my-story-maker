# Core Documentation — StoryMaker V7

Internal reference for the engine core. For mod authoring see `MAKE_MOD.md`.

---

## 1. Architecture Overview

```
main.py
  └─ EventBus          ← global pub/sub, drives everything
  └─ ServiceRegistry   ← shared service store
  └─ CoreAPI           ← public interface handed to mods
  └─ ModLoader         ← orchestrates the full pipeline
        ├─ ModDiscovery
        ├─ ManifestLoader (ManifestReader → ManifestValidator → ManifestProcessor)
        ├─ DependencyModule (GraphBuilder → Checker → ConflictChecker → CycleDetector → Sorter)
        ├─ DynamicLoader   (import → instantiate → on_load)
        ├─ InitExecutor    (on_init)
        ├─ ReadyExecutor   (emit ENGINE_READY)
        └─ ShutdownExecutor (on_shutdown, reversed)
```

`ModStorage` is the single mutable data structure shared across all pipeline steps.

---

## 2. ModStorage

`core/__mod_storage.py`

All pipeline stages read and write one `ModStorage` instance.

```python
class ModStorage:
    manifests:    dict[str, dict]       # parsed manifests (versions → Version objects)
    states:       dict[str, str]        # "discovered" | "enable" | "disable"
    instances:    dict[str, Any]        # live Mod instances
    paths:        dict[str, Path]       # mod directory paths
    errors:       dict[str, list]       # per-mod error strings
    dependencies: dict[str, list[str]]  # dependency graph edges
    conflicts:    dict[str, list[str]]  # declared conflicts (raw)
    load_order:   list[str]             # final sorted mod names
```

A mod is accessible to other mods only when `states[mod] == "enable"` and `instances[mod] is not None`.

---

## 3. EventBus

`core/event_bus.py`

### Registered events

Only events declared in `resources/EVENTS.py` can be emitted or subscribed to. The full list:

```
ENGINE_BOOT      ENGINE_INIT      ENGINE_READY
ENGINE_TICK      ENGINE_SHUTDOWN
ENGINE_ERROR     ENGINE_FATAL_ERROR
MOD_DISCOVERED   MOD_LOADED       MOD_INITIALIZED
MOD_ERROR        MOD_MANIFEST_ERROR
MOD_DEPENDENCY_ERROR  MOD_CONFLICT
LOG_EVENT
```

Custom events must be registered first:

```python
core.get_event_bus().register("MY_EVENT")   # returns False if name is not UPPER_CASE
core.get_event_bus().unregister("MY_EVENT")
```

### Event structure

Every emitted event is a dict:

```python
{
    "name":      "ENGINE_READY",   # UPPER_CASE string
    "source":    "core",           # "core" or "mod_<name>"
    "payload":   {},               # always a dict, never None
    "timestamp": 1234567890        # UNIX int, injected by CoreAPI.emit()
}
```

### API

```python
event_bus.emit(event: dict) -> bool
event_bus.subscribe(event_name: str, callback) -> bool
event_bus.unsubscribe(event_name: str, callback) -> bool
event_bus.register(event_name: str) -> bool
event_bus.unregister(event_name: str) -> bool
```

`subscribe` and `unsubscribe` accept both a raw callable and a `Handler` object.

### Execution

Each `emit()` builds a `HandlerPipeline` from the sorted handler list and runs it:

- If an asyncio loop is running → `loop.create_task(pipeline.run(event))`
- Otherwise → `asyncio.run(pipeline.run(event))` (sync entry point)

Async handler functions are awaited transparently.

---

## 4. Handler and Pipeline

`resources/__handler.py`, `core/__pipeline.py`

### Handler

```python
Handler(
    func: Callable,
    priority: int = 0,         # higher = runs first
    name: str | None = None,   # defaults to func.__name__
    mode: str = "normal",      # "normal" | "shadow" | "override" | "chain"
    mod_name: str | None = None,
)
```

Raw callables passed to `subscribe` are auto-wrapped as `Handler(callback)` (normal, priority 0).

### Pipeline execution rules

Handlers are sorted by **priority descending** before execution.

| Mode | On success | On exception |
|---|---|---|
| `normal` | continue to next handler | caught + logged + `MOD_ERROR` emitted, continue |
| `shadow` | **stop pipeline** | caught + logged, **continue to next handler** (fallback) |
| `override` | **stop pipeline** | caught + logged, still stop |
| `chain` | handler receives `async next()` — it decides continuation | caught + logged, stop |

`shadow` is the key mode for layered fallbacks (e.g. styled → plain console output).

---

## 5. ServiceRegistry

`core/service_registry.py`

```python
registry.register(name: str, instance: Any) -> bool
registry.unregister(name: str) -> bool
registry.get(name: str) -> Any          # None if missing
registry.exists(name: str) -> bool
registry.list_services() -> list[str]   # sorted alphabetically
```

Rules enforced by `register`:

- `name` must be `snake_case` (lowercase, digits, underscores only).
- A name can only be registered once — duplicate registration is refused and emits `MOD_ERROR`.
- `instance` must not be `None`.

`get` returns `None` silently when the service is absent; it never raises.

---

## 6. CoreAPI

`core/core_api.py`  — the object mods receive as `core` in every hook.

```python
# Events
core.emit(event_name: str, payload: dict = {}, source: str = "core") -> bool
core.subscribe(event_name: str, callback) -> bool

# Services
core.register_service(name: str, instance: Any) -> bool
core.get_service(name: str) -> Any

# Mod introspection
core.get_mod(name: str) -> Any          # live instance or None
core.get_manifest(name: str) -> dict    # stored manifest or None
core.get_all_mods() -> list[str]        # names with state == "enable"

# Logging
core.log(level: str, message: str)      # emits LOG_EVENT; source = "core"

# Version
core.get_core_version() -> str          # from core_engine manifest, fallback "7.0.0"

# Advanced (prefer the wrappers above)
core.get_event_bus() -> EventBus
core.get_service_registry() -> ServiceRegistry
```

`core._mod_storage` is set by `main.py` after `ModLoader` is created — it is not part of the public API.

---

## 7. ModLoader Pipeline

`core/mod_loader.py`

### `load_all()`

```
emit ENGINE_BOOT
ModDiscovery.discover_mods()          → scans core/default_mods/, mods/, mods/default/
ManifestLoader.run_manifest_pipeline() → read → validate → store (or disable)
DependencyModule.run()                → graph → check → conflicts → cycles → sort
DynamicLoader.run_dynamic_loading()   → import → instantiate → on_load → wire on_ready
emit ENGINE_INIT
InitExecutor.run_on_init()            → on_init for each mod in load_order
ReadyExecutor.run_on_ready()          → emit ENGINE_READY  (triggers on_ready handlers)
```

### `shutdown()`

```
emit ENGINE_SHUTDOWN
ShutdownExecutor.run_on_shutdown()    → on_shutdown in reverse load_order
```

### Mod discovery rules

A directory is a mod if it: starts with `mod_`, lives inside a scanned path, and contains `manifest.json`. Emits `MOD_DISCOVERED` for each.

---

## 8. Dependency Resolution

`core/__dependency.py`

Pipeline: `DependencyGraphBuilder → DependencyChecker → ConflictChecker → CycleDetector → PriorityTopoSorter`

**Graph**: directed edges `mod → dependency`. Built from `requires` keys.

**Checks that disable a mod** (emitting `MOD_DEPENDENCY_ERROR` or `MOD_CONFLICT`):

- Required mod missing from manifests.
- Required mod is already disabled.
- Installed version does not satisfy the SemVer constraint.
- Declared conflict matches an active mod's version.
- Mod participates in a dependency cycle.

**Sort order** (stored in `mod_storage.load_order`):

1. Topological (dependencies always precede dependents).
2. `priority` descending within the same topological level.
3. Alphabetical as tie-breaker.

---

## 9. Manifest Validation

`core/__manifest.py`

Required fields and their checks:

| Field | Rule |
|---|---|
| `name` | `str`, starts with `mod_`, `snake_case` |
| `version` | `str`, strict SemVer (`MAJOR.MINOR.PATCH`) |
| `type` | one of `core_engine`, `core_default`, `default`, `extension`, `experimental` |
| `priority` | `int` |
| `entrypoint` | file exists relative to mod directory |
| `requires` | `dict` |
| `conflicts` | `dict` |
| `permissions` | `list` (optional field; validated only if present) |

Failure on any rule → mod disabled + `MOD_MANIFEST_ERROR`.

After validation, `ManifestProcessor.store()`:

- Converts `version` string to a `Version` object.
- Converts every constraint string in `requires` / `conflicts` to `list[Condition]` (or `"*"`).
- Honours the `active` field: `false`, `"off"`, `"disable"` → state `"disable"`.

---

## 10. Version System

`core/__version.py`

### `Version`

Immutable dataclass with `major`, `minor`, `patch` (each `int` or `"*"`).

```python
v = Version.parse("1.2.3")   # → Version(1, 2, 3)
v = Version.parse("1.*.0")   # wildcard segment
str(v)                        # "1.2.3"
```

### `VersionComparator`

```python
VersionComparator.compare(a, b) -> int   # -1 | 0 | 1
VersionComparator.equals(a, b)  -> bool
```

Wildcard segments (`"*"`) are treated as equal to anything.

### `ConstraintParser`

```python
ConstraintParser.parse(">=1.0.0,<2.0.0")  # → list[Condition]
ConstraintParser.parse("*")               # → "*"
ConstraintParser.parse("1.2.3")           # → [Condition(op="=", target=Version(1,2,3))]
```

### `ConstraintResolver`

```python
ConstraintResolver.satisfies(version, constraints) -> bool
```

Returns `False` if either argument is `None`. `"*"` always returns `True`.

---

## 11. Error Handling Policy

- **No unhandled exceptions in the core.** All pipeline stages use `try/except`.
- **A mod error never stops the engine.** The mod is disabled; remaining mods continue.
- **Every error is logged and emitted** as `MOD_ERROR` or `ENGINE_ERROR`.
- **Fatal errors** emit `ENGINE_FATAL_ERROR` and trigger shutdown.

Hook error consequences:

| Hook | On failure |
|---|---|
| `on_load` | mod disabled, `MOD_ERROR` |
| `on_init` | mod disabled, instance set to `None`, `MOD_ERROR` |
| `on_ready` | `MOD_ERROR` only (mod stays loaded) |
| `on_shutdown` | logged, shutdown continues |
| event handler | caught, `MOD_ERROR`, pipeline continues |

---

## 12. Bundled Mods

### `mod_error_and_log` (core_default, priority 900)

Provides the `logger` service and wires all lifecycle/error events to log output.

```python
logger = core.get_service("logger")
logger.log(level, source, message)  # emits LOG_EVENT
```

Subscribes two handlers to `LOG_EVENT`:

- `log_write_file` (normal, priority 900) — always appends to `engine.log`.
- `log_console_plain` (shadow, priority 10) — plain stdout fallback.

### `mod_styled_text` (core_default, priority 120)

Provides the `styled_text` service for ANSI-coloured terminal output. No external dependencies.

### `mod_styled_error_and_log` (extension, priority 110)

Subscribes `log_console_styled` (shadow, priority 100) to `LOG_EVENT`. Intercepts between the file writer and the plain fallback. Silently yields to plain output if `styled_text` is unavailable.
