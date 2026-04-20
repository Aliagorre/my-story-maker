\# my-story-maker/overview.md

---

## **1. StoryMaker V7 — Overview**

**StoryMaker V7** is a **narrative operating system**: a general-purpose platform designed for creating, running, and orchestrating all types of interactive experiences (text-based, graphical, hybrid, networked, etc.).

* The **core** contains **no adventure-specific logic**.
* All higher-level functionality (graphs, conditions, inventory, UI, adventure formats, etc.) is handled by **mods**.
* The system is designed for both:

  * **Developers / modders** (clear, stable, extensible API),
  * **Non-technical creators** (through a curated set of high-quality default mods).

---

## **2. Role of the Core**

The **core** is minimal by design, yet structurally robust. It provides:

* **Engine lifecycle management**

  * Boot, mod loading, initialization, execution, shutdown

* **Mod loading and management**

  * Manifest parsing
  * Dependency, version, and conflict resolution
  * Load ordering and execution

* **Global EventBus**

  * Publish/subscribe event system

* **Service Registry**

  * Registration and access to services exposed by mods

* **Error handling**

  * Captures errors from both core and mods
  * Emits error events (`ENGINE_ERROR`, `MOD_ERROR`)

* **Minimal public API**

  * Core interaction layer for mods

The core has **no knowledge** of adventures, formats, UI, graphs, conditions, or gameplay systems.

---

## **3. Role of Mods**

Mods are the functional building blocks of the StoryMaker ecosystem.

They can:

* Implement systems such as graphs, conditions, inventory, quests, characters, etc.
* Provide user interfaces (terminal, graphical, web)
* Define adventure formats
* Offer editors, tools, scripting systems, or DSLs

Mods interact with the core through:

* The **EventBus**
* The **Service Registry**
* The **core public API**

Some mods are considered **core mods** (essential for usability), but they remain technically standard mods.

---

## **4. Engine Lifecycle**

Standard lifecycle:

1. **ENGINE_BOOT**

   * Core startup
   * Minimal initialization (logging, internal structures)

2. **Manifest Discovery**

   * Scan mod directories
   * Validate manifests

3. **Dependency Resolution**

   * Validate `requires`, `conflicts`, versions, priorities

4. **Mod Loading**

   * Import entrypoints
   * Execute `on_load` hooks

5. **Initialization**

   * Execute `on_init` hooks
   * Register services

6. **ENGINE_READY**

   * Engine is fully initialized
   * Emits `ENGINE_READY`

7. **Execution Loop**

   * Main loop (sync or async)
   * Optional `ENGINE_TICK` events
   * Mods react through the EventBus

8. **ENGINE_SHUTDOWN**

   * Execute `on_shutdown` hooks
   * Release resources
   * Terminate process

The core **does not restart itself**.
Resets (e.g., restarting an adventure) are handled by mods via events and their own logic.

---

## **5. High-Level Architecture**

* **`main.py`**

  * Minimal entry point
  * Initializes the core and starts the lifecycle

* **`/core/`**

  * `event_bus.py` → Global EventBus
  * `mod_loader.py` → Discovery, manifests, dependencies, loading
  * `service_registry.py` → Service registration and access
  * `core_api.py` → Public interface exposed to mods
  * `default_mods/` → Core mods (CLI, logging, minimal UI, etc.)

* **`/mods/`**

  * `default/` → Non-core default mods (graphs, conditions, inventory, etc.)
  * Other directories → extensions, experiments, custom mods

---

## **6. Design Philosophy**

* **Minimal yet structured**

  * The core does the minimum required, but does it cleanly

* **Everything that can be a mod should be a mod**

  * The core never implements features that can be externalized

* **Radical extensibility**

  * A mod should be able to:

    * open complex UIs
    * handle multiplayer
    * run media
    * define its own language
  * without requiring changes to the core

* **Logical isolation**

  * Mods communicate primarily through:

    * the EventBus
    * declared services
  * Direct access to another mod’s internals is discouraged

---

## **7. Target Audience**

### **Developers / Modders**

* Build advanced systems (graphs, conditions, UI, networking, etc.)
* Integrate custom languages, DSLs, or external libraries

### **Non-Technical Creators**

* Use default mods (graph editors, condition systems, UI, etc.)
* Create and manage adventures through visual tools or simple formats
