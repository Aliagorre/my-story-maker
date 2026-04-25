\# my-story-maker/README.md

# **StoryMaker V7 — Development Guidelines**

StoryMaker is a modular storytelling engine built around a minimal, extensible core.
Its architecture is designed to separate responsibilities clearly: the core handles orchestration, while features are implemented through mods.

---

## **Project Structure**

```
/core/            # Engine core
/mods/            # User and external mods
/default_mods/    # Built-in essential mods
/docs/            # Documentation
/examples/        # Sample projects
main.py           # Entry point
```

---

## **Core Principles**

* **Minimalism** — The core does as little as possible
* **Modularity** — Everything is a mod
* **Predictability** — Explicit lifecycle and behavior
* **Extensibility** — Easy to add, replace, or remove features
* **Separation of concerns** — Core vs mods

---

## **Core Responsibilities**

The core is intentionally lightweight and unopinionated. It provides:

* Logging (basic levels only)
* Error handling and reporting
* Mod loading and lifecycle management
* Dependency resolution
* Event system (EventBus)
* Service registry
* Permission system (design stage)
* Public API for mods

### **Lifecycle Overview**

```
ENGINE_BOOT
→ Load Mods
ENGINE_INIT
ENGINE_READY
→ Main Loop (tick)
ENGINE_SHUTDOWN
```

---

## **Mod System**

Mods extend the engine and implement all features.

### **Manifest Requirements**

Each mod must define a manifest (JSON or YAML):

* `name`
* `version` (SemVer)
* `requires`
* `conflicts`
* `priority`
* `permissions`
* `type`
* `entrypoint`

### **Lifecycle Hooks**

```python
on_load()
on_init()
on_ready()
on_shutdown()
```

---

## **Core Mods (`/core/default_mods/`)**

These are required for a usable system.

| Mod                     | Responsibility                 |
| ----------------------- | ------------------------------ |
| `mod_error_and_log`     | Error handling and log display |
| `mod_cmd`               | CLI interface                  |
| `mod_styled_text`       | Text styling                   |
| `mod_ui`                | Terminal UI                    |
| `mod_mod_manager`       | Mod management                 |
| `mod_file_system`       | File access                    |
| `mod_script_engine`     | Script execution               |
| `mod_adventure_manager` | Adventure loading              |
| `mod_base_adventure`    | Example adventure              |

---

## **Default Mods (`/mods/default/`)**

Optional but recommended for end users.

* Graph editor
* Condition engine
* Inventory system
* Character system
* Quest system
* Save/load system
* Graphical UI (Pygame)
* Networking (multiplayer)

---

## **Core API (Simplified)**

```python
core.emit(event, payload)
core.subscribe(event, callback)

core.register_service(name, service)
core.get_service(name)

core.get_mod(name)
core.get_manifest(name)

core.log(level, message)
```

---

## **Development Standards**

* Python: **PEP 8 + internal conventions**
* Versioning: **Strict SemVer**
* Clear separation between core and mods
* No direct access between mods (use services)

---

## **Testing Strategy**

* Core: unit tests
* Core mods: integration tests
* Default mods: functional tests

---

## **Future Extensions** 

* Mod marketplace (My dream)
* AI assistant integration (My friend's dream)
* Analytics tools 
* Audio engine

---

## **Getting Started**

1. Clone the repository
2. Run `main.py`
3. Explore `/examples/`
4. Create your first mod

