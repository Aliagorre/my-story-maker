# StoryMaker V7

A **narrative operating system** — a minimal, modular Python runtime for building and running any kind of interactive experience.

The core contains zero domain logic. Every feature (UI, scripting, adventure formats, editors, networking…) lives in a **mod**. The engine provides the scaffolding; mods do the rest.

---

## Philosophy

- **The core does as little as possible** — lifecycle, event routing, service sharing, dependency resolution.
- **Everything that can be a mod must be a mod** — no hardcoded features.
- **Mods are isolated** — they communicate through the EventBus and the Service Registry, never by importing each other.
- **Errors never crash the engine** — faulty mods are disabled; the rest keeps running.

---

## Quick Start

```bash
git clone <repo>
cd my-story-maker
python main.py
```

Run the test suite:

```bash
python test.py
```

---

## Project Structure

```
/
├── main.py                         # Engine entry point
├── test.py                         # Test suite entry point
├── core/
│   ├── core_api.py                 # Public API exposed to mods
│   ├── event_bus.py                # Global publish/subscribe bus
│   ├── mod_loader.py               # Orchestrates the full mod lifecycle
│   ├── service_registry.py         # Service registration and retrieval
│   └── default_mods/
│       ├── mod_core_engine/        # Engine identity mod
│       └── mod_error_and_log/      # Logging + error events (priority 900)
├── mods/
│   └── default/
│       ├── mod_styled_text/        # ANSI text styling service
│       └── mod_styled_error_and_log/  # Coloured console output
├── resources/
│   ├── EVENTS.py                   # All registered event name constants
│   ├── LOG_LEVELS.py               # Log level constants
│   ├── MOD_TYPES.py                # Valid mod type constants
│   └── __handler.py                # Handler wrapper with modes and priorities
└── docs/
    ├── README.md                   # ← you are here
    ├── MAKE_MOD.md                 # How to build a mod (with examples)
    └── DOCUMENTATION.md            # Core internals reference
```

---

## Engine Lifecycle

```
ENGINE_BOOT
  → Mod discovery (core/default_mods/, mods/, mods/default/)
  → Manifest validation
  → Dependency resolution + load order
  → on_load() for each mod
ENGINE_INIT
  → on_init() for each mod
ENGINE_READY                  ← on_ready(event) fires here for all mods
  → Main loop  (ENGINE_TICK every 100 ms)
ENGINE_SHUTDOWN
  → on_shutdown() in reverse load order
```

---

## Bundled Mods

| Mod | Type | Service | Priority |
|---|---|---|---|
| `mod_error_and_log` | `core_default` | `logger` | 900 |
| `mod_styled_text` | `core_default` | `styled_text` | 120 |
| `mod_styled_error_and_log` | `extension` | — | 110 |

---

## Core API (quick reference)

```python
# Events
core.emit("MY_EVENT", {"key": "value"})
core.subscribe("ENGINE_READY", my_handler)

# Services
core.register_service("my_service", MyService())
service = core.get_service("my_service")

# Mods & manifests
instance = core.get_mod("mod_name")
manifest = core.get_manifest("mod_name")
all_mods = core.get_all_mods()

# Logging
core.log("INFO", "message")
```

Full reference → [`DOCUMENTATION.md`](DOCUMENTATION.md)  
Building a mod → [`MAKE_MOD.md`](MAKE_MOD.md)

---

## License

MIT
