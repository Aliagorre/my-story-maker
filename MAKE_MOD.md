# Making a Mod — StoryMaker V7

Everything you need to build a mod, from a minimal skeleton to event handling and mod interaction.

---

## 1. Minimal Mod

### Directory layout

```
mods/default/mod_hello/
├── manifest.json
└── main.py
```

### `manifest.json`

```json
{
    "name": "mod_hello",
    "version": "1.0.0",
    "type": "extension",
    "priority": 50,
    "entrypoint": "main.py",
    "requires": {},
    "conflicts": {},
    "permissions": []
}
```

### `main.py`

```python
class Mod:
    def on_load(self, core):
        pass

    def on_init(self, core):
        pass

    def on_ready(self, core):
        core.log("INFO", "Hello from mod_hello!")

    def on_shutdown(self, core):
        pass
```

All four lifecycle methods **must exist** and be callable — the loader checks for them. All four receive `core` as their only argument.

The engine discovers the mod automatically; no registration is needed.

---

## 2. Manifest Reference

```json
{
    "name":        "mod_example",       // required — must start with mod_
    "version":     "1.2.0",             // required — strict SemVer MAJOR.MINOR.PATCH
    "type":        "extension",         // required — see table below
    "priority":    50,                  // required — integer, higher loads earlier
    "entrypoint":  "main.py",           // required — path relative to mod directory

    "requires": {                       // required (may be empty)
        "mod_other": ">=1.0.0,<2.0.0"
    },
    "conflicts": {                      // required (may be empty)
        "mod_legacy": "*"
    },

    "permissions": [],                  // optional list

    "active": true,                     // optional — false / "off" / "disable" disables mod
    "description": "Short description.",
    "author":      "Your Name",
    "license":     "MIT"
}
```

#### Mod types

| Type | Location | Description |
|---|---|---|
| `core_engine` | reserved | Core identity mod |
| `core_default` | `core/default_mods/` | Required for the engine to run |
| `default` | `core/default_mods/` | Bundled, non-critical |
| `extension` | `mods/default/` | Standard optional mod |
| `experimental` | anywhere | Unstable / work-in-progress |

#### Version constraints (in `requires` / `conflicts`)

```
"*"               any version
">=1.2.0"         at least 1.2.0
"<2.0.0"          below 2.0.0
">=1.0.0,<2.0.0"  range (comma = AND)
"=1.*.*"          wildcard segments
```

---

## 3. Lifecycle Hooks

All hooks are called with `core` as the only argument:

```
on_load(self, core)     → mod is imported; subscribe to events here
on_init(self, core)     → all mods are loaded; access other mod instances here
on_ready(self, core)    → engine is about to start its input loop; start your features here
on_shutdown(self, core) → engine is stopping; save state, release resources
```

Hooks may be sync or async — the loader handles both transparently:

```python
async def on_load(self, core):
    await some_async_setup()
```

If a hook is missing the loader simply skips it (though all four should exist per the manifest contract).

---

## 4. Subscribing to Events

Pass any callable to `core.subscribe`. The EventBus calls it with the event dict whenever the event fires.

```python
def on_load(self, core):
    core.subscribe("ENGINE_TICK", self._on_tick)

def _on_tick(self, event):
    # event is {"name": ..., "source": ..., "payload": ..., "timestamp": ...}
    pass
```

Subscriptions should be made in `on_load` so they are in place before `on_init` and `on_ready` run.

### Event structure

Every event is a plain dict:

```python
{
    "name":      "ENGINE_TICK",   # UPPER_CASE string
    "source":    "core_engine",   # who emitted it
    "payload":   {},              # always a dict
    "timestamp": 1234567890.0     # float, seconds since epoch
}
```

---

## 5. Emitting Events

```python
core.emit("MY_EVENT", {"key": "value"})
```

Only events that have been registered on the EventBus are accepted. Built-in events live in `resources/EVENTS.py`. To emit a custom event, register it first:

```python
def on_load(self, core):
    core.get_event_bus().register("MY_CUSTOM_EVENT")

def on_ready(self, core):
    core.emit("MY_CUSTOM_EVENT", {"data": 42})
```

`register` returns `False` (and does nothing) if the name is already registered, so it is safe to call in `on_load`.

---

## 6. Logging

```python
core.log("INFO", "Mod started.")
core.log("WARNING", "Something looks off.")
core.log("ERROR", "Something failed.")
```

This emits a `LOG_EVENT` with the payload `{"level": ..., "message": ..., "context": {}}`. Any mod subscribed to `LOG_EVENT` will receive it.

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

---

## 7. Accessing Other Mods

```python
def on_init(self, core):
    other = core.get_mod("mod_other")
    if other is not None:
        other.some_public_method()
```

`get_mod` returns the live `Mod` instance, or `None` if the mod is not loaded. Use `on_init` for this — other mods are guaranteed to be loaded by then. Never import a mod's internals directly.

You can also inspect a mod's manifest:

```python
manifest = core.get_manifest("mod_other")
```

And list all currently enabled mods:

```python
names = core.get_all_enabled_mods()   # ["mod_a", "mod_b", ...]
```

---

## 8. Exports

A mod can expose a dict of values via a module-level `exports` variable. Other mods can read it through `core.get_mod`:

```python
# mod_dice/main.py
def roll(sides):
    import random
    return random.randint(1, sides)

exports = {"roll": roll}

class Mod:
    def on_load(self, core): pass
    def on_init(self, core): pass
    def on_ready(self, core): pass
    def on_shutdown(self, core): pass
```

```python
# another mod
def on_init(self, core):
    dice = core.get_mod("mod_dice")
    result = dice.exports["roll"](20)
```

---

## 9. Full Example — `mod_counter`

Counts `ENGINE_TICK` events and logs a report on shutdown.

**`manifest.json`**

```json
{
    "name": "mod_counter",
    "version": "1.0.0",
    "type": "extension",
    "priority": 40,
    "entrypoint": "main.py",
    "requires": {},
    "conflicts": {},
    "permissions": []
}
```

**`main.py`**

```python
class Mod:
    def on_load(self, core):
        self.core = core
        self.ticks = 0
        core.subscribe("ENGINE_TICK", self._on_tick)

    def on_init(self, core):
        pass

    def on_ready(self, core):
        core.log("INFO", "Counter started.")

    def on_shutdown(self, core):
        core.log("INFO", f"Total ticks counted: {self.ticks}")

    def _on_tick(self, event):
        self.ticks += 1
```
