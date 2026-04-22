\# my-story-maker/docs/mods/MOD_LYFECYCLE.md

# StoryMaker V7 — Mod Lifecycle

## 1. Introduction

Each StoryMaker V7 mod follows a strict lifecycle orchestrated by the core. This lifecycle ensures:

* consistent loading,
* predictable initialization,
* stable communication,
* clean deactivation,
* robustness in the presence of errors.

A mod lifecycle is composed of **four main hooks**:

1. `on_load(core)`
2. `on_init(core)`
3. `on_ready(core)`
4. `on_shutdown(core)`

These hooks are **optional**, but strongly recommended.

---

## 2. Lifecycle overview

Complete lifecycle:

```text
MOD_DISCOVERED
    ↓
Manifest read
    ↓
Validation
    ↓
Dependency resolution
    ↓
Mod load (on_load)
    ↓
Initialization (on_init)
    ↓
ENGINE_READY
    ↓
Final activation (on_ready)
    ↓
Main loop
    ↓
ENGINE_SHUTDOWN
    ↓
Mod shutdown (on_shutdown)
```

---

## 3. Lifecycle hooks

Each hook has a specific responsibility and must not be misused.

---

## 3.1 `on_load(core)`

### Execution timing

Immediately after the mod is imported, before global initialization.

### Recommended usage

* Read the mod manifest.
* Subscribe to events.
* Register services in the Service Registry.
* Prepare lightweight structures.
* Declare handlers.

### Restrictions

* Do not load heavy assets.
* Do not depend on other mods (they are not initialized yet).
* Do not execute complex business logic.

### Example

```python
def on_load(self, core):
    core.subscribe("ENGINE_READY", self._on_engine_ready)
    core.register_service("graph_api", GraphAPI())
```

---

## 3.2 `on_init(core)`

### Execution timing

After **all mods are loaded**, in the order defined by the Mod Loader.

### Recommended usage

* Initialize systems depending on other services.
* Load resources (files, templates, models).
* Prepare complex internal structures.
* Verify availability of critical services.

### Restrictions

* Do not start UI.
* Do not start persistent threads.

### Example

```python
def on_init(self, core):
    self.script_engine = core.get_service("script_engine")
    self.cache = self._load_templates()
```

---

## 3.3 `on_ready(core)`

### Execution timing

Immediately after the event:

```
ENGINE_READY
```

### Recommended usage

* Start user interfaces.
* Launch interactive systems.
* Load an adventure.
* Start threads or async tasks.

### Restrictions

* Do not register new services.
* Do not modify dependencies.

### Example

```python
def on_ready(self, core):
    self.ui.start()
```

---

## 3.4 `on_shutdown(core)`

### Execution timing

During engine shutdown, after:

```
ENGINE_SHUTDOWN
```

Mods are shut down in **reverse load order**.

### Recommended usage

* Release resources.
* Close files.
* Stop threads.
* Persist state.

### Restrictions

* Do not register services.
* Do not start new tasks.

### Example

```python
def on_shutdown(self, core):
    self.thread.stop()
    self.save_state()
```

---

## 4. Errors in hooks

### 4.1 Error in `on_load`

* Mod is disabled.
* `MOD_ERROR` event emitted.
* Engine continues.

### 4.2 Error in `on_init`

* Mod may be disabled.
* `MOD_ERROR` event emitted.

### 4.3 Error in `on_ready`

* Mod remains loaded but may be marked unstable.
* `MOD_ERROR` event emitted.

### 4.4 Error in `on_shutdown`

* `[ERROR]` log emitted.
* Engine continues shutdown.

---

## 5. Strict rules

* A mod must **never** access another mod’s internals directly.
* A mod must **never** import another mod.

A mod must use only:

* the EventBus,
* the Service Registry,
* the core API.

Additional constraints:

* A mod must not modify its manifest at runtime.
* A mod must not register services after `on_init`.

---

## 6. Summary

| Hook          | Timing             | Role                                   |
| ------------- | ------------------ | -------------------------------------- |
| `on_load`     | After import       | Declarations, services, subscriptions  |
| `on_init`     | After global load  | Dependency-based initialization        |
| `on_ready`    | After ENGINE_READY | UI, threads, interactive systems       |
| `on_shutdown` | Engine shutdown    | Cleanup, persistence, resource release |

The mod lifecycle must remain **simple**, **predictable**, **strict**, and **robust**.
