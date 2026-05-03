# Core Documentation — StoryMaker V7

Internal reference for the engine core. For mod authoring see `MAKE_MOD.md`.

---

## 1. Architecture Overview

```
main.py
  └─ EventBus        ← synchronous pub/sub, drives all communication
  └─ ModStorage      ← shared mutable state across the pipeline
  └─ ModLoader       ← full mod lifecycle
        ├─ discover_mods()
        ├─ _load_manifest()
        ├─ _resolve_dependencies()
        ├─ _check_conflicts()
        ├─ _compute_load_order()
        ├─ _load_mod()           → import → instantiate → on_load → on_init
        ├─ load_all()            → above steps + on_ready for all mods
        └─ shutdown_all()        → on_shutdown in reverse order
  └─ CoreAPI         ← public interface handed to each mod
```

`ModStorage` is the single shared data structure read and written by all pipeline steps and by `CoreAPI`.

---

## 2. ModStorage

`core/mod_loader.py` — `ModStorage` dataclass

```python
@dataclass
class ModStorage:
    manifests: Dict[str, dict]   # raw manifests, keyed by mod name
    instances: Dict[str, Any]    # live Mod instances (set only after successful load)
    states:    Dict[str, str]    # "disabled" | "enable"
    exports:   Dict[str, dict]   # module-level exports dicts, keyed by mod name
```

A mod's instance is available to others only when `states[name] == "enable"` and `instances[name] is not None`.

### ModRecord (internal)

`ModLoader` uses `ModRecord` internally — it is never exposed to mods:

```python
@dataclass
class ModRecord:
    name:     str
    path:     Path
    manifest: dict
    module:   Any | None        # imported module object
    instance: Any | None        # Mod class or bare module
    exports:  dict
    state:    str               # "disabled" | "loaded" | "error"
```

---

## 3. EventBus

`core/event_bus.py`

A simple synchronous pub/sub broker. Events must be registered before they can be subscribed to or emitted.

### API

```python
event_bus.register(event_name: str)                         # declare a new event
event_bus.subscribe(event_name: str, callback: Callable) -> bool
event_bus.unsubscribe(event_name: str, callback: Callable) -> bool
event_bus.emit(event: dict) -> bool                         # False if event unknown
```

`subscribe` returns `False` if the event has not been registered or the callback is not callable.

### Event structure

```python
{
    "name":      "ENGINE_READY",     # UPPER_CASE string
    "source":    "core_engine",      # emitting mod name or "core_engine"
    "payload":   {},                 # always a dict
    "timestamp": 1234567890.0        # float, from time.time()
}
```

### Execution

`emit` iterates all subscribers for that event name in registration order and calls each callback synchronously. The handler list is copied before iteration, so unsubscribing mid-dispatch is safe.

### Error handling

If a subscriber raises an exception, `emit` catches it and re-emits an `ERROR_EVENT`:

```python
{
    "name":    "ERROR_EVENT",
    "payload": {
        "exception": str(e),
        "handler":   callback.__name__,
        "source":    original_event["source"],
    },
    "source":    "event_bus",
    "timestamp": time(),
}
```

The remaining subscribers for the original event continue to run.

> There is **no handler priority, no pipeline, and no handler modes** (`shadow`, `chain`, etc.). All subscribers are plain callables called in subscription order.

### Known events (main.py)

The engine emits these events directly on the bus (via `event_bus.emit`, not `core.emit`):

| Event | When | Payload |
|---|---|---|
| `ENGINE_READY` | after `load_all()` returns | `{}` |
| `COMMAND_INPUT` | each non-empty line from stdin | `{"raw": line}` |

Any event referenced in `resources/EVENTS.py` must be registered before use.

---

## 4. CoreAPI

`core/core_api.py` — the `core` object mods receive in every hook.

```python
CoreAPI(event_bus, mod_storage, mod_name: str)
```

### Methods

```python
# Events
core.emit(event_name: str, payload: dict)
    # Emits {name, payload, source=mod_name, timestamp=time()} on the bus

core.subscribe(event_name: str, callback: Callable) -> bool
    # Delegates to event_bus.subscribe

core.get_event_bus() -> EventBus
    # Returns the underlying EventBus for direct access (register, unregister, etc.)

# Logging
core.log(level: str, message: str, **context)
    # Shorthand: emits LOG_EVENT with payload {level, message, context}

# Mod introspection
core.get_mod(name: str) -> Any | None
    # Live Mod instance from mod_storage.instances, or None

core.get_manifest(name: str) -> dict | None
    # Raw manifest dict from mod_storage.manifests, or None

core.get_all_enabled_mods() -> list[str]
    # Names where mod_storage.states[name] == "enable"

core.get_all_mods() -> list[str]
    # All names in mod_storage.states, regardless of state

core.get_core_version() -> str
    # version field of the "core_engine" manifest, or "7.0.0"

# Advanced patching
core.override(path: str, new_value)
    # Replace an attribute by dotted path: core.override("mod_dice.exports.roll", fn)

core.extend(path: str, additions: dict)
    # Merge keys into a dict attribute: core.extend("mod_dice.exports", {"adv": fn})
```

There is **no service registry**. Mods share functionality by exposing public methods on their `Mod` instance (accessed via `core.get_mod`) or via the module-level `exports` dict.

---

## 5. ModLoader Pipeline

`core/mod_loader.py`

### `load_all()` (async)

```
discover_mods()            → scan mods_root for mod_* directories with manifest.json
_resolve_dependencies()    → mark state="error" if a required mod is missing
_check_conflicts()         → mark state="error" if a conflicting mod is present
_compute_load_order()      → topological sort (skips error mods)
for each mod in load_order:
    _load_mod(rec)         → import → get Mod or module → on_load → on_init → mark "loaded"
for each loaded mod:
    _call_lifecycle("on_ready")
```

### `shutdown_all()` (async)

```
for each mod in reversed(load_order):
    on_shutdown(core)
    state → "disabled"
```

### `reload_mod(name)` (async)

Hot-reloads a single mod: `on_shutdown` → purge from `sys.modules` → `_load_mod` → `on_ready`. Does not rewire existing EventBus subscribers or update dependents.

---

## 6. Mod Discovery

`discover_mods()` scans the single `mods_root` directory passed to `ModLoader` (in `main.py`: `Path(__file__).parent / "mods"`).

A subdirectory is recognised as a mod if:
- `manifest.json` exists inside it.
- The manifest contains at least `"name"` and `"entrypoint"`.
- The file referenced by `"entrypoint"` exists on disk.

Missing or malformed manifests are silently skipped. Recognised mods get a `ModRecord` in state `"disabled"` and an entry in `mod_storage.manifests` and `mod_storage.states`.

Manifest defaults applied when fields are absent:

| Field | Default |
|---|---|
| `version` | `"1.0.0"` |
| `type` | `"extension"` |
| `priority` | `0` |
| `requires` | `{}` |
| `conflicts` | `{}` |
| `permissions` | `[]` |

---

## 7. Dependency Resolution

### `_resolve_dependencies()`

For every mod, checks each key in `requires`. If any required mod name is not present in `self._mods`, the mod's state is set to `"error"`. Version constraints in the manifest are stored but **not evaluated** at this stage.

### `_check_conflicts()`

For every mod, checks each key in `conflicts`. If any conflicting mod name is present in `self._mods`, the mod's state is set to `"error"`.

### `_compute_load_order()`

Builds a dependency graph from `requires` keys (error mods excluded). Runs a topological sort:

1. At each pass, collect all mods whose dependencies are already in the output list (the "ready" set).
2. If no mods are ready (cycle), add all remaining mods as-is (cycle breaking).
3. Within the ready set, sort by `priority` descending (higher priority loads first), then alphabetically as a tiebreaker.

The result is stored in `self._load_order`.

---

## 8. Dynamic Loading (`_load_mod`)

For each mod in load order (skipping state `"error"`):

1. Resolves `entrypoint` path; marks `"error"` if the file is missing.
2. Imports the module via `importlib.util.spec_from_file_location`.
3. Gets the mod instance: `getattr(module, "Mod", module)` — prefers a `Mod` class; falls back to the bare module.
4. Creates a `CoreAPI(event_bus, mod_storage, name)` and attaches it as `rec.instance.core`.
5. Calls `on_load(core)`, then `on_init(core)` via `_call_lifecycle`.
6. Reads the module-level `exports` dict (if present) and stores it in `mod_storage.exports[name]`.
7. Sets `rec.state = "loaded"`, adds instance to `mod_storage.instances`, sets `mod_storage.states[name] = "enable"`.

Any exception at steps 1–6 sets `rec.state = "error"` and aborts loading that mod.

---

## 9. Lifecycle Hook Dispatch (`_call_lifecycle`)

```python
async def _call_lifecycle(self, rec: ModRecord, hook: str) -> None:
```

Retrieves `getattr(rec.instance, hook, None)`. If the attribute exists, calls it with the `core` stored on `rec.instance`. Supports both sync and async hook functions.

**All four hooks receive `core` as their only argument**, including `on_ready`.

| Hook | Called in | Arg | Failure behaviour |
|---|---|---|---|
| `on_load` | `_load_mod` | `core` | mod marked `"error"` |
| `on_init` | `_load_mod` | `core` | mod marked `"error"` |
| `on_ready` | `load_all` (second pass) | `core` | logged, mod stays loaded |
| `on_shutdown` | `shutdown_all` | `core` | logged, shutdown continues |

---

## 10. Version System

`core/__version.py` (referenced by the manifest processor)

### `Version`

Immutable dataclass with `major`, `minor`, `patch`.

```python
v = Version.parse("1.2.3")   # → Version(1, 2, 3)
str(v)                        # "1.2.3"
```

Wildcard segments (`"*"`) are supported and treated as equal to anything during comparison.

### `ConstraintParser`

```python
ConstraintParser.parse(">=1.0.0,<2.0.0")  # → list[Condition]
ConstraintParser.parse("*")               # → "*" (matches any version)
ConstraintParser.parse("1.2.3")           # → [Condition(op="=", target=Version(1,2,3))]
```

Comma-separated constraints are ANDed together.

### `ConstraintResolver`

```python
ConstraintResolver.satisfies(version, constraints) -> bool
```

Returns `False` if either argument is `None`. `"*"` always returns `True`.

> Note: as of the current loader implementation, version constraints in `requires` are stored in the manifest but not evaluated during dependency checking — only the presence or absence of the required mod name is checked.

---

## 11. Error Handling Policy

- **No unhandled exceptions in the core.** All pipeline stages use `try/except`.
- **A mod error never stops the engine.** The mod is marked `"error"` or skipped; remaining mods continue.
- **EventBus exceptions** are caught per-handler and re-emitted as `ERROR_EVENT`; other subscribers for the same event continue running.
- There is no `MOD_ERROR` or `ENGINE_FATAL_ERROR` event emitted by the core loader — errors surface via `ERROR_EVENT` on the bus.
