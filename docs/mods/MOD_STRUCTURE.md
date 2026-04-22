\# my-story-maker/docs/mods/MOD_STRUCTURE.md

# StoryMaker V7 — Mod Structure Specification

## 1. Introduction

A StoryMaker V7 mod is a **self-contained unit**, composed of:

* a dedicated directory,
* a strict manifest,
* a Python entrypoint,
* an internal code space (`src/`),
* an asset space (`assets/`).

The structure must be **simple**, **predictable**, and **standardized** so that:

* the Mod Loader can operate without ambiguity,
* contributors can navigate easily,
* mods can be shared, versioned, and maintained.

---

## 2. Official mod structure

Minimal and complete structure:

```
mod_<name>/
├── manifest.json
├── main.py
├── src/
│   └── ... (internal modules)
└── assets/
    └── ... (non-Python files)
```

Each element is described below.

---

## 3. `manifest.json` (required)

The manifest:

* identifies the mod,
* declares its version,
* defines dependencies,
* declares permissions,
* specifies the entrypoint,
* defines the mod type.

It must strictly follow the specification defined in `MANIFEST.md`.

If invalid → the mod is **disabled**.

---

## 4. `main.py` (required)

This is the **entrypoint** of the mod.

It must contain:

* a main class,
* freely named but coherent,
* exposing lifecycle hooks (optional but recommended):

```python
class ModMain:
    def on_load(self, core):
        pass

    def on_init(self, core):
        pass

    def on_ready(self, core):
        pass

    def on_shutdown(self, core):
        pass
```

### Rules

* The file must exist.
* It must be importable without errors.
* The main class must be instantiable without arguments.
* The class name is flexible but must be clear.

---

## 5. `src/` (strongly recommended)

Contains **all internal code** of the mod.

Example:

```
src/
├── parser.py
├── ui_components.py
├── graph_engine.py
└── utils/
    └── tokenizer.py
```

### Rules

* No complex logic should be placed in `main.py`.
* `main.py` should act as an **orchestrator**, not a dump file.
* Internal code must be well-organized.

---

## 6. `assets/` (optional)

Contains non-Python resources:

* images,
* audio,
* templates,
* JSON files,
* configuration files,
* DSL scripts,
* other resources.

### Rules

* The mod must manage its own asset loading.
* The core provides no asset system.

---

## 7. Lifecycle hooks

A mod may implement the following hooks:

### 7.1 `on_load(core)`

Called immediately after import.

Use cases:

* subscribe to events,
* register services,
* read manifest data,
* initialize lightweight structures.

---

### 7.2 `on_init(core)`

Called after **all mods are loaded**.

Use cases:

* initialize systems depending on other mods,
* load resources,
* prepare core logic.

---

### 7.3 `on_ready(core)`

Called after `ENGINE_READY`.

Use cases:

* start UI,
* launch interactive systems,
* load an adventure.

---

### 7.4 `on_shutdown(core)`

Called during engine shutdown.

Use cases:

* release resources,
* close files,
* stop threads,
* persist state.

---

## 8. Strict rules

### 8.1 One mod = one directory

No nested mods, no sub-mod systems.

---

### 8.2 Directory name must start with `mod_`

Valid examples:

* `mod_cmd`
* `mod_graph_editor`
* `mod_inventory`

---

### 8.3 No direct access to other mods

Mods must use:

* the EventBus,
* the Service Registry.

---

### 8.4 No cross-imports between mods

Forbidden:

```python
from mod_graph_editor.main import GraphEditor
```

Allowed:

```python
core.get_service("graph_api")
```

---

### 8.5 No business logic in the core

Anything not strictly required for engine operation → belongs in a mod.

---

## 9. Complete example

```
mod_graph_editor/
├── manifest.json
├── main.py
├── src/
│   ├── graph_model.py
│   ├── graph_renderer.py
│   └── ui/
│       └── editor_window.py
└── assets/
    ├── icons/
    └── templates/
```

---

## 10. Summary

| Element         | Role                                     |
| --------------- | ---------------------------------------- |
| `manifest.json` | Identity, version, dependencies          |
| `main.py`       | Entrypoint, lifecycle hooks              |
| `src/`          | Internal logic                           |
| `assets/`       | Resources                                |
| Hooks           | Mod lifecycle                            |
| Rules           | No cross-imports, no core business logic |

A mod structure must remain **simple**, **clear**, **predictable**, and **extensible**.
