\# my-story-maker/docs/ROADMAP.md

# StoryMaker V7 — Official Roadmap

## 1. Introduction

This roadmap outlines the planned development stages for StoryMaker V7.
It is organized into **phases**, each with:

* a clear objective,
* defined deliverables,
* set priorities,
* consistency with the engine’s modular architecture.

The roadmap is **evolving**, but its foundations must remain **stable**.

---

# 2. Phase 1 — Engine Foundations (V7.0.0)

**Objective:** stabilize the core of the engine and ensure a solid base for the ecosystem.

### Deliverables

* Functional minimal core
* Stable EventBus (sync + async)
* Stable Service Registry
* Complete Mod Loader
* Dependency resolution (SemVer + conflicts + cycles)
* Robust error handling
* Official mod structure
* Minimal and stable Core API
* Complete documentation

### Priority

⭐⭐⭐⭐⭐ (critical)

### Status

In progress / nearly complete

---

# 3. Phase 2 — Default Mods (V7.1.0)

**Objective:** provide an immediately usable environment.

### Deliverables

* mod_error_and_log
* mod_cmd
* mod_styled_text
* mod_script_engine
* mod_adventure_loader
* mod_ui_terminal
* mod_debug_tools
* mod_graph_editor (minimal version)

### Priority

⭐⭐⭐⭐

### Status

To be finalized after core stabilization

---

# 4. Phase 3 — Narrative Ecosystem (V7.2.0)

**Objective:** enable the creation of complete adventures.

### Deliverables

* Minimal narrative DSL
* Scene system
* Choice system
* Variable system
* Condition system
* Action system
* Integration with mod_script_engine
* Stable API for adventures

### Priority

⭐⭐⭐

### Status

To start after default mods

---

# 5. Phase 4 — Creative Tools (V7.3.0)

**Objective:** provide modern creation tools.

### Deliverables

* Graphical adventure editor (mod_graph_editor v2)
* Narrative graph visualization
* Script editor
* Event inspector
* Service inspector
* Advanced debug mode

### Priority

⭐⭐⭐

### Status

Planned

---

# 6. Phase 5 — Advanced UI (V7.4.0)

**Objective:** improve user experience.

### Deliverables

* mod_ui_web (modern web UI)
* mod_ui_desktop (native UI via toolkit)
* mod_ui_mobile (optional)
* Theme system
* Reusable widget system

### Priority

⭐⭐

### Status

Planned

---

# 7. Phase 6 — External Ecosystem (V7.5.0)

**Objective:** open StoryMaker V7 to the community.

### Deliverables

* Official external mod format
* Developer documentation
* Mod templates
* CLI to create mods
* Packaging system
* Distribution system (mod marketplace, future)

### Priority

⭐⭐

### Status

Planned

---

# 8. Phase 7 — Advanced Features (V7.6.0+)

**Objective:** extend the engine’s capabilities.

### Possibilities

* Hot-reload of mods
* Hot-reload of scripts
* Multiplayer narrative mode
* Collaborative mode
* UI plugin system
* Advanced save system
* AI integration (optional, sandboxed)

### Priority

⭐

### Status

Long term

---

# 9. Long-Term Vision

StoryMaker V7 aims to become:

* a modular narrative engine,
* an extensible ecosystem,
* a powerful creation tool,
* a stable framework for interactive adventures,
* an open platform for developers.

Core philosophy:
**small core, large ecosystem.**

---

# 10. Summary

| Phase | Objective           | Priority | Status      |
| ----- | ------------------- | -------- | ----------- |
| 1     | Engine foundations  | ⭐⭐⭐⭐⭐    | In progress |
| 2     | Default mods        | ⭐⭐⭐⭐     | To start    |
| 3     | Narrative ecosystem | ⭐⭐⭐      | To start    |
| 4     | Creative tools      | ⭐⭐⭐      | Planned     |
| 5     | Advanced UI         | ⭐⭐       | Planned     |
| 6     | External ecosystem  | ⭐⭐       | Planned     |
| 7     | Long-term features  | ⭐        | Long term   |
