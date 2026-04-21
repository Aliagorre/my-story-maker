\# my-story-maker/docs/overview/PHILOSOPHY.md

# **StoryMaker V7 — Philosophy**

---

## **1. Introduction**

The philosophy of StoryMaker V7 is built around a simple but fundamental principle:

> **Anything that can be a mod must be a mod.**

The core is not a narrative engine.
It is not an editor.
It is not a specialized framework.

It is a **narrative operating system**: a minimal, stable, and extensible runtime designed to support a diverse ecosystem of powerful mods.

This approach ensures full creative freedom, long-term stability, and continuous extensibility.

---

## **2. Structured Minimalism**

The core must remain **small**, yet **precisely structured**.

### **2.1 What the Core Does**

* Manages the engine lifecycle
* Loads and initializes mods
* Resolves dependencies
* Provides a global EventBus
* Provides a Service Registry
* Handles errors
* Exposes a minimal public API

---

### **2.2 What the Core Must Never Do**

The core must not implement:

* narrative graph systems
* condition systems
* scenes or storytelling logic
* inventory systems
* character systems
* quest systems
* adventure formats
* user interfaces
* scripting systems

All of these belong **exclusively to mods**.

---

## **3. Radical Extensibility**

StoryMaker V7 is designed so that a mod can:

* create complex interfaces
* run media (e.g., video playback)
* handle multiplayer systems
* define custom languages or DSLs
* provide full-featured editors
* introduce new adventure formats
* replace the entire UI
* integrate rendering engines
* embed AI systems
* redefine how adventures are structured

The core must never restrict what a mod can achieve.
Its role is to provide a stable and predictable environment.

---

## **4. Strict Separation of Responsibilities**

### **4.1 Core**

* minimal
* stable
* unopinionated
* independent from mods

---

### **4.2 Core Mods**

* bundled with the engine
* required for usability
* minimal and extensible

---

### **4.3 Default Mods**

* designed for non-technical creators
* optional
* replaceable

---

### **4.4 External Mods**

* unrestricted
* experimental or advanced
* fully independent

This separation ensures clarity, modularity, and maintainability.

---

## **5. Full Mod Autonomy**

Mods are **applications** within the StoryMaker ecosystem.

They must be able to:

* communicate via the EventBus
* expose services through the Service Registry
* manage their own resources
* define their own internal lifecycles
* use any technology stack
* manage threading or asynchronous logic
* define their own internal conventions

The core must not impose implementation patterns.

---

## **6. Robustness and Stability**

The core must be:

* resilient to errors
* tolerant of faulty mods
* stable over time
* properly versioned
* clearly documented

A mod may fail, but the engine should continue running.
A mod may be disabled, but system stability must be preserved.

---

## **7. Clarity and Transparency**

StoryMaker V7 should be:

* readable
* understandable
* well-documented
* educational

Contributors must be able to quickly understand:

* how the core works
* how mods interact
* how to build a mod
* how to extend the system

Documentation is a core part of the project’s philosophy.

---

## **8. Long-Term Extensibility**

StoryMaker V7 is designed to evolve over time without requiring core rewrites.

The core must be generic enough to support:

* new types of mods
* new technologies
* new narrative paradigms
* new formats
* new tools
* new interfaces

The core must never become a bottleneck.

---

## **9. Summary**

The philosophy of StoryMaker V7 is based on four pillars:

1. **Structured minimalism**
2. **Radical extensibility**
3. **Strict separation of responsibilities**
4. **Robustness and stability**

These principles define StoryMaker V7 as a **narrative operating system**—capable of supporting any type of interactive experience, system, or innovation.
