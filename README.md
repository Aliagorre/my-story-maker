# StoryMaker V7

A **narrative operating system** — a minimal, modular Python runtime for building and running any kind of interactive experience.

The core contains zero domain logic. Every feature lives in a **mod**. The engine provides lifecycle management, event routing, and dependency resolution; mods do everything else.

---

## Philosophy

- **The core does as little as possible** — lifecycle, event routing, mod loading, dependency resolution.
- **Everything that can be a mod must be a mod** — no hardcoded features.
- **Mods are isolated** — they communicate through the EventBus, never by importing each other.
- **Errors never crash the engine** — faulty mods are skipped; the rest keep running.

---

## Quick Start

```bash
git clone <repo>
cd storymaker-v7
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
│   └── mod_loader.py               # Mod discovery, loading, and lifecycle
└── mods/
    └── default/                    # Standard optional mods
```

---

## Engine Lifecycle

```
python main.py
  → EventBus and ModStorage created
  → ModLoader.load_all()
      → Mod discovery    (scans mods/)
      → Manifest parsing + validation
      → Dependency and conflict checks
      → Topological load order computed
      → on_load(core)    for each mod in order
      → on_init(core)    for each mod in order
      → on_ready(core)   for each mod in order
  → ENGINE_READY emitted on the bus
  → Input loop: each line emits COMMAND_INPUT
  → Ctrl+C / EOF
      → ModLoader.shutdown_all()
          → on_shutdown(core) in reverse order
```

---

## Core API (quick reference)

The `core` object passed to every hook:

```python
# Events
core.emit("MY_EVENT", {"key": "value"})
core.subscribe("MY_EVENT", my_callback)
core.get_event_bus()               # direct access to the EventBus

# Mod introspection
instance = core.get_mod("mod_name")
manifest = core.get_manifest("mod_name")
enabled  = core.get_all_enabled_mods()   # list of enabled mod names
all_mods = core.get_all_mods()           # list of all known mod names

# Logging
core.log("INFO", "message")        # emits LOG_EVENT

# Version
core.get_core_version()            # string, e.g. "7.0.0"

# Advanced patching (use with care)
core.override("mod_name.attr", new_value)
core.extend("mod_name.exports", {"key": fn})
```

Full reference → [`DOCUMENTATION.md`](DOCUMENTATION.md)
Building a mod → [`MAKE_MOD.md`](MAKE_MOD.md)

---

## License

MIT
