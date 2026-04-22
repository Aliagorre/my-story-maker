\# my-story-maker/docs/conventions/convention.md

# 1. StoryMaker V7 - Objective

Define the standards governing:

* core code
* core mods (`mods_core`)
* default mods
* file structure
* manifests
* events
* versioning
* logging
* naming
* permissions

These conventions are **mandatory** across the entire project.

---

# **2) Naming Conventions**

## 2.1 — Mod Names

Strict format:

```
mod_<name>
```

Examples:

* `mod_cmd`
* `mod_error_and_log`
* `mod_ui_terminal`
* `mod_script_engine`

Core mods are located in `/core/default_mods/`.
Default mods are located in `/mods/default/`.

---

## 2.2 — Python File Names

* Use `snake_case`
* One file = one clear responsibility

Examples:

* `event_bus.py`
* `mod_loader.py`
* `service_registry.py`

---

## 2.3 — Class Names

* Use `PascalCase`

Examples:

* `EventBus`
* `ModLoader`
* `ScriptEngine`

---

## 2.4 — Functions and Methods

* Use `snake_case`
* Prefer explicit verbs

Examples:

* `load_manifest()`
* `resolve_dependencies()`
* `emit_event()`

---

## 2.5 — Event Names

Strict format:

```
ENGINE_<ACTION>
MOD_<ACTION>
ADVENTURE_<ACTION>
UI_<ACTION>
```

Examples:

* `ENGINE_BOOT`
* `ENGINE_READY`
* `MOD_ERROR`
* `UI_RENDER`
* `ADVENTURE_LOADED`

---

# **3) Project Structure Conventions**

## 3.1 — General Layout

```
/
├── core/
│   ├── event_bus.py
│   ├── mod_loader.py
│   ├── service_registry.py
│   ├── core_api.py
│   └── default_mods/
│       ├── mod_cmd/
│       ├── mod_error_and_log/
│       ├── mod_styled_text/
│       ├── mod_ui_terminal/
│       ├── mod_script_engine/
│       ├── mod_adventure_loader/
│       ├── mod_mod_manager/
│       ├── mod_file_system/
│       ├── mod_base_adventure/
│       └── ...
├── mods/
│   └── default/
│       ├── mod_graph_editor/
│       ├── mod_condition_engine/
│       └── ...
├── docs/
├── examples/
└── main.py
```

---

# **4) Manifest Conventions**

Each mod must include:

```
manifest.json
```

### Format:

```json
{
  "name": "mod_cmd",
  "version": "1.0.0",
  "type": "core_default",
  "priority": 50,
  "entrypoint": "main.py",
  "requires": {
    "mod_error_and_log": ">=1.0.0"
  },
  "conflicts": {
    "mod_old_logger": "*"
  },
  "permissions": [
    "filesystem_read",
    "filesystem_write",
    "ui",
    "network"
  ]
}
```

---

## 4.1 — Mod Types

| Type           | Description                                                               |
| -------------- | ------------------------------------------------------------------------- |
| `core_engine`  | Reserved for the core (rare)                                              |
| `core_default` | Essential built-in mods, required for the engine to function              |
| `default`      | Non-critical built-in mods, loaded automatically but not strictly required |
| `extension`    | Standard optional mods                                                    |
| `experimental` | Unstable mods                                                             |

---

## 4.2 — Versioning

* Strict **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`

Rules:

* **MAJOR** → breaking changes
* **MINOR** → backward-compatible features
* **PATCH** → fixes

---

# **5) Event Conventions**

## 5.1 — Event Structure

An event is a dictionary:

```python
{
  "name": "ENGINE_READY",
  "source": "core",
  "payload": {...},
  "timestamp": 1234567890
}
```

---

## 5.2 — Rules

* `name` is required
* `source` = mod or core
* `payload` must always be a dictionary (never `None`)
* `timestamp` is provided by the core

---

## 5.3 — Event Categories

* `ENGINE_*`
* `MOD_*`
* `UI_*`
* `ADVENTURE_*`
* `SCRIPT_*`
* `FS_*`

---

# **6) Logging Conventions**

## 6.1 — Levels

* `DEBUG`
* `INFO`
* `WARNING`
* `ERROR`
* `CRITICAL`

---

## 6.2 — Minimal Format

```
[LEVEL] [timestamp] [source] message
```

Example:

```
[INFO] [12:03:45] [core] Engine ready
```

---

## 6.3 — Styling Rules

* No styling in the core
* Styling is handled by `mod_styled_text`

---

# **7) Permission Conventions**

## 7.1 — Available Permissions

* `filesystem_read`
* `filesystem_write`
* `network`
* `ui`
* `spawn_process`
* `script_eval`
* `unsafe` (full access)

---

## 7.2 — Rules

* Dev mode: all permissions allowed
* Safe mode: restrictions may apply
* The core logs all permission requests

---

# **8) Documentation Conventions**

## 8.1 — Each Mod Must Include:

* `README.md`
* `manifest.json`
* `main.py`
* `/src/` (if needed)
* `/assets/` (if needed)

---

## 8.2 — Core Documentation Must Include:

* `API.md`
* `EVENTS.md`
* `LIFECYCLE.md`
* `MOD_CREATION_GUIDE.md`

---

# **9) Quality Standards**

* No dead code
* No `print` statements in the core
* No direct interaction between mods (use `ServiceRegistry`)
* Unit tests for the core
* Integration tests for core mods
