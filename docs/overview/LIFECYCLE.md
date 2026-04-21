\# my-story-maker/docs/overview/LIFECYCLE.md

# **StoryMaker V7 — Lifecycle**

---

## **1. Introduction**

The StoryMaker V7 lifecycle defines the **exact sequence** in which:

* the core starts,
* mods are discovered, loaded, and initialized,
* the engine becomes operational,
* the main loop runs,
* the engine shuts down cleanly.

This lifecycle is **strict**, **predictable**, and **stable**, ensuring both core robustness and full freedom for mods.

---

## **2. Overview**

The complete engine lifecycle is as follows:

1. **ENGINE_BOOT**
2. Mod discovery
3. Manifest loading and validation
4. Dependency resolution
5. Mod loading (`on_load`)
6. Mod initialization (`on_init`)
7. **ENGINE_READY**
8. Main loop (tick)
9. Shutdown (`on_shutdown`)

The core **never restarts itself**.
Resets are handled by mods via events.

---

## **3. Detailed Phases**

---

## **3.1 Phase 1 — ENGINE_BOOT**

The engine starts.
The core initializes its internal structures:

* minimal internal logger
* global EventBus
* Service Registry
* mod management structures
* internal clock (timestamp)

Event emitted:

```id="a1"
ENGINE_BOOT
```

No mods are loaded at this stage.

---

## **3.2 Phase 2 — Mod Discovery**

The core scans the following directories:

* `/core/default_mods/`
* `/mods/`
* `/mods/default/`
* any additional configured paths

All available mods are identified.
No validation is performed yet.

---

## **3.3 Phase 3 — Manifest Loading and Validation**

For each mod, the core:

* reads `manifest.json`
* validates structure
* checks required fields
* verifies requested permissions
* validates mod type
* checks version format

If an error occurs:

* the mod is disabled
* a `MOD_MANIFEST_ERROR` event is emitted

---

## **3.4 Phase 4 — Dependency Resolution**

The core builds a dependency graph based on:

* `requires`
* `conflicts`
* version ranges
* priority

It validates:

* dependency cycles
* incompatible versions
* declared conflicts
* missing dependencies

If an issue is detected:

* the mod is disabled
* a `MOD_DEPENDENCY_ERROR` event is emitted

Once validated, the core computes the **final load order**.

---

## **3.5 Phase 5 — Mod Loading (`on_load`)**

For each mod, in the resolved order:

1. The core dynamically imports the entry point (`main.py`)
2. Instantiates the main mod class
3. Calls the hook:

```python id="a2"
on_load(core)
```

At this stage:

* the mod can read its manifest
* the mod can subscribe to events
* the mod can register services
* the mod must not execute business logic yet

If an error occurs:

* `MOD_ERROR` event is emitted
* the mod may be disabled

---

## **3.6 Phase 6 — Mod Initialization (`on_init`)**

After all mods are loaded, the core calls:

```python id="a3"
on_init(core)
```

for each mod, in the same order.

At this stage:

* services are available
* dependencies are resolved
* mods can initialize internal structures
* mods can load resources
* mods can prepare their logic

---

## **3.7 Phase 7 — ENGINE_READY**

Once all mods are initialized, the core emits:

```id="a4"
ENGINE_READY
```

From this point:

* the engine is fully operational
* mods can run normally
* UIs can be displayed
* adventures can be loaded
* systems can activate

---

## **3.8 Phase 8 — Main Loop (Tick)**

The core enters the main execution loop.

### **3.8.1 Synchronous Tick (Default)**

At each tick:

* the core emits `ENGINE_TICK`
* mods react
* UIs update
* internal systems run

---

### **3.8.2 Asynchronous Tick (Optional)**

The core may use an `asyncio` loop:

* async events
* async handlers
* non-blocking I/O

---

### **3.8.3 Tick Rules**

* The core must never block
* Mods handle their own threading or async logic
* The core never restarts itself
* Resets are handled via events (e.g., `ADVENTURE_RESET_REQUEST`)

---

## **3.9 Phase 9 — Shutdown (`on_shutdown`)**

When the engine needs to stop:

1. The core emits:

```id="a5"
ENGINE_SHUTDOWN
```

2. For each mod, in reverse load order, the core calls:

```python id="a6"
on_shutdown(core)
```

Mods must:

* release resources
* close files
* stop threads
* persist state if necessary

The core then exits cleanly.

---

## **4. Error Handling in the Lifecycle**

### **4.1 Core Errors**

If an internal error occurs:

* `ENGINE_ERROR` event
* detailed logging
* clean shutdown if required

---

### **4.2 Mod Errors**

If a mod fails:

* `MOD_ERROR` event
* stack trace provided
* mod may be disabled
* engine continues if possible

---

### **4.3 Fatal Errors**

If execution cannot continue:

* `ENGINE_FATAL_ERROR`
* immediate shutdown

---

## **5. Visual Summary**

```id="a7"
ENGINE_BOOT
    ↓
Mod Discovery
    ↓
Manifest Loading
    ↓
Dependency Resolution
    ↓
Mod Loading (on_load)
    ↓
Mod Initialization (on_init)
    ↓
ENGINE_READY
    ↓
Main Loop (tick)
    ↓
ENGINE_SHUTDOWN
    ↓
Mods on_shutdown
```
