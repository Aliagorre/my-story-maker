\# my-story-maker/docs/overview/ARCHITECTURE.md

# **StoryMaker V7 — Architecture**

---

## **1. Introduction**

The architecture of StoryMaker V7 is built on a strict separation between:

* **the core**: a minimal, stable, and structured engine
* **mods**: independent, powerful, and unrestricted extensions
* **core mods**: essential built-in mods required for usability
* **default mods**: additional tools aimed at non-technical creators

This design enables **radical extensibility**: anything not strictly required for the engine to function is implemented as a mod.

---

## **2. Overall Structure**

The logical project structure is as follows:

```
/
├── main.py
├── core/
│   ├── event_bus.py
│   ├── mod_loader.py
│   ├── service_registry.py
│   ├── core_api.py
│   └── default_mods/
│       ├── mod_error_and_log/
│       ├── mod_cmd/
│       ├── mod_styled_text/
│       ├── mod_mod_manager/
│       ├── mod_file_system/
│       ├── mod_script_engine/
│       ├── mod_adventure_loader/
│       ├── mod_base_adventure/
│       └── mod_ui_terminal/
├── mods/
│   └── default/
│       ├── mod_graph_editor/
│       ├── mod_debug_tools/
│       ├── mod_condition_engine/
│       └── ...
└── docs/
```

Each directory has a clear and independent responsibility.

---

## **3. The Core**

The **core** is the engine's foundation.
It is intentionally minimal and contains **no domain-specific logic**.

---

### **3.1 Core Responsibilities**

The core provides:

* Engine lifecycle management
* Mod loading
* Dependency resolution
* Global EventBus
* Service Registry
* Error handling
* Minimal public API

It does **not** provide any narrative system, UI, or adventure format.

---

### **3.2 Internal Components**

#### **3.2.1 EventBus**

A global publish/subscribe system.
This is the primary communication mechanism between mods.

---

#### **3.2.2 Mod Loader**

Discovers, reads, validates, and loads mods.
Handles dependencies, conflicts, versions, and priorities.

---

#### **3.2.3 Service Registry**

Allows mods to expose services that can be accessed by other mods.
Prevents direct dependencies between mods.

---

#### **3.2.4 Core API**

The public interface exposed to mods.
Provides access to events, services, manifests, and core functionality.

---

## **4. Mods**

**Mods** are self-contained extensions.
They can implement any feature: UI, graphs, conditions, inventory, formats, networking, etc.

---

### **4.1 Mod Structure**

A typical mod contains:

```
mod_name/
├── manifest.json
├── main.py
├── src/
└── assets/
```

---

### **4.2 Mod Lifecycle**

Mods may implement the following hooks:

```python
on_load(core)
on_init(core)
on_ready(core)
on_shutdown(core)
```

---

### **4.3 Mod Communication**

Two mechanisms are available:

1. **EventBus** (recommended)
2. **Service Registry** (for stable APIs)

Mods must not directly access the internals of other mods.

---

## **5. Core Mods**

**Core mods** are bundled with the engine and are required to make it usable.

They are located in:

```
/core/default_mods/
```

They are split into two sub-types:

### **5.1 `core_default` — Required**

| Mod                | Main Role              | Service provided |
| ------------------ | ---------------------- | ---------------- |
| mod_error_and_log  | Logging + errors       | logger           |
| mod_cmd            | CLI interface          | cmd_interface    |
| mod_styled_text    | Text styling           | styled_text      |
| mod_mod_manager    | Mod management         | mod_manager      |
| mod_file_system    | File system access     | file_system      |
| mod_base_adventure | Base adventure types   | base_adventure   |

### **5.2 `default` — Non-critical but bundled**

| Mod                  | Main Role          | Service provided  |
| -------------------- | ------------------ | ----------------- |
| mod_script_engine    | Script engine      | script_engine     |
| mod_adventure_loader | Adventure loading  | adventure_manager |
| mod_ui_terminal      | Text UI            | ui_terminal       |

They follow the same philosophy as the core:
**minimal, structured, and extensible**.

---

## **6. Default Mods**

Default mods are not required for the engine to run, but are useful for creators.

They are located in:

```
/mods/default/
```

Examples:

* `mod_graph_editor`
* `mod_debug_tools`
* `mod_condition_engine`
* `mod_inventory`
* `mod_characters`
* `mod_quests`
* `mod_save_system`
* `mod_pygame_ui`
* `mod_network`

These mods can be disabled, replaced, or extended.

---

## **7. Global Lifecycle**

The engine follows this lifecycle:

1. **ENGINE_BOOT**
2. Mod discovery
3. Manifest loading
4. Dependency resolution
5. Mod loading (`on_load`)
6. Initialization (`on_init`)
7. **ENGINE_READY**
8. Final activation (`on_ready`)
9. Main loop (tick)
10. Shutdown (`on_shutdown`)

The core never restarts itself.
Resets are handled by mods.

---

## **8. Strict Separation of Responsibilities**

| Component         | Role                                        |
| ----------------- | ------------------------------------------- |
| **Core**          | Minimal, stable engine with no domain logic |
| **Core Mods**     | Essential features required for usability   |
| **Default Mods**  | Tools for non-technical creators            |
| **External Mods** | Free, experimental, or advanced extensions  |

This separation ensures:

* core stability
* complete freedom for mods
* long-term scalability

---

## **9. Long-Term Architectural Vision**

The architecture must support:

* new types of mods
* integration of new technologies
* custom DSL creation
* multiple adventure formats
* backward compatibility
* extreme modularity

StoryMaker V7 is designed to remain an **ecosystem**, not a fixed engine.
