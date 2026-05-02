# Making a Mod — StoryMaker V7

This guide covers everything you need to build a mod, from the minimal skeleton to advanced handler patterns.

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

    def on_ready(self, event):          # NOTE: receives the ENGINE_READY event dict, not core
        core.log("INFO", "Hello from mod_hello!")

    def on_shutdown(self, core):
        pass
```

> **`on_ready` signature differs from the other hooks.** It receives the `ENGINE_READY` event dict because it is wired as an event handler by the loader. Store `core` in `on_load` if you need it later.

The engine discovers the mod automatically — no registration needed.

---

## 2. Manifest Reference

```json
{
    "name":        "mod_example",       // required — mod_<snake_case>
    "version":     "1.2.0",             // required — strict SemVer
    "type":        "extension",         // required — see table below
    "priority":    50,                  // required — integer, higher loads earlier
    "entrypoint":  "main.py",           // required — path relative to mod dir

    "requires": {                       // required (can be empty)
        "mod_script_engine": ">=1.0.0,<2.0.0"
    },
    "conflicts": {                      // required (can be empty)
        "mod_old_engine": "*"
    },

    "permissions": [                    // optional
        "filesystem_read",
        "filesystem_write",
        "network",
        "ui",
        "spawn_process",
        "script_eval",
        "unsafe"
    ],

    "active":      true,                // optional — false / "off" / "disable" to disable
    "description": "Short description.",
    "author":      "Your Name",
    "license":     "MIT"
}
```

#### Mod types

| Type | Where | Description |
|---|---|---|
| `core_engine` | reserved | Core engine only |
| `core_default` | `core/default_mods/` | Required for the engine to run |
| `default` | `core/default_mods/` | Bundled, non-critical |
| `extension` | `mods/default/` or external | Standard optional mod |
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

```
on_load(self, core)     → after import; subscribe to events, register services
on_init(self, core)     → after all mods are loaded; use other mods' services
on_ready(self, event)   → ENGINE_READY fired; start UI, threads, adventures
on_shutdown(self, core) → ENGINE_SHUTDOWN; release resources, save state
```

All hooks are optional, but all four methods **must exist** and be callable — the loader validates this at import time.

### Storing core for later use

Because `on_ready` does not receive `core`, store it in `on_load`:

```python
def on_load(self, core):
    self.core = core
    core.subscribe("ENGINE_READY", self._on_ready)

def _on_ready(self, event):
    # self.core is available here
    self.core.log("INFO", "ready!")

def on_ready(self, event):
    pass  # still required, but can be a no-op
```

---

## 4. Emitting and Subscribing to Events

### Emit

```python
core.emit("ADVENTURE_STARTED", {"adventure_id": "demo"})
```

Only events declared in `resources/EVENTS.py` are accepted. To add custom events you must register them:

```python
core.get_event_bus().register("MY_CUSTOM_EVENT")
core.emit("MY_CUSTOM_EVENT", {"data": 42})
```

### Subscribe (simple)

Passing a plain callable wraps it automatically as a `normal` handler at priority 0:

```python
def on_load(self, core):
    core.subscribe("ENGINE_TICK", self._tick)

def _tick(self, event):
    pass   # called every tick
```

### Subscribe with a Handler object

Import `Handler` for full control over priority and mode:

```python
from resources.__handler import Handler

def on_load(self, core):
    core.subscribe(
        "LOG_EVENT",
        Handler(
            self._handle_log,
            name="my_log_handler",
            priority=50,        # higher = runs first
            mode="normal",      # see section 5
            mod_name="mod_hello",
        ),
    )
```

---

## 5. Handler Modes

The EventBus runs handlers in **priority order** (highest first). Each handler's `mode` controls what happens after it runs.

| Mode | Behaviour on success | Behaviour on exception |
|---|---|---|
| `normal` | pipeline continues | exception caught + logged, pipeline continues |
| `shadow` | **pipeline stops** | exception caught + logged, next handler runs (fallback) |
| `override` | **pipeline stops** | exception caught + logged, pipeline still stops |
| `chain` | handler controls continuation via `next()` | exception caught, pipeline stops |

#### `shadow` — the fallback pattern

`shadow` is used when a handler provides an enhanced version of a feature and should silently yield to the next handler on failure. The bundled logging system uses this:

```
log_write_file   (priority=900, normal)   → always writes to engine.log
log_console_styled (priority=100, shadow) → styled output; stops here if styled_text is available
log_console_plain  (priority=10,  shadow) → plain fallback; only reached if styled handler failed
```

A mod providing styled output:

```python
from resources.__handler import Handler

def on_load(self, core):
    core.subscribe(
        "LOG_EVENT",
        Handler(
            self._styled_log,
            name="my_styled_log",
            priority=100,
            mode="shadow",
            mod_name="mod_hello",
        ),
    )

def _styled_log(self, event):
    styled = self.core.get_service("styled_text")
    if styled is None:
        raise RuntimeError("no styled_text")   # falls back to plain handler
    p = event["payload"]
    print(styled.style(f"[{p['level']}] {p['message']}", color="cyan"))
```

#### `chain` — full pipeline control

The handler receives an async `next()` callable as its second argument:

```python
async def _chain_handler(self, event, next):
    print("before")
    await next()          # call remaining handlers
    print("after")
```

```python
core.subscribe(
    "ENGINE_TICK",
    Handler(self._chain_handler, mode="chain", priority=200),
)
```

---

## 6. Services

Services let mods expose a stable API to other mods without direct imports.

### Registering a service

Register in `on_load` (or `on_init` if you depend on another service):

```python
class MyService:
    def greet(self, name):
        return f"Hello, {name}!"

class Mod:
    def on_load(self, core):
        core.register_service("my_greeter", MyService())
```

Rules: name must be `snake_case`, a name can only be registered once.

### Consuming a service

```python
def on_init(self, core):
    greeter = core.get_service("my_greeter")
    if greeter is None:
        core.log("WARNING", "my_greeter not available")
        return
    print(greeter.greet("world"))
```

Always check for `None` — the service may not be loaded.

---

## 7. Logging

Emit a `LOG_EVENT` through the `logger` service provided by `mod_error_and_log`:

```python
def on_init(self, core):
    logger = core.get_service("logger")
    logger.log("INFO", "mod_hello", "Initialized.")
    logger.log("WARNING", "mod_hello", "Something looks off.")
    logger.log("ERROR", "mod_hello", "Something failed.")
```

Or use `core.log` for quick messages (source will be `"core"`):

```python
core.log("INFO", "quick message")
```

Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

---

## 8. Styled Text

`mod_styled_text` exposes the `styled_text` service:

```python
def on_init(self, core):
    self.styled = core.get_service("styled_text")

def on_ready(self, event):
    if self.styled:
        print(self.styled.h1("My Mod"))
        print(self.styled.style("Important", color="bright_red", styles=["bold"]))
        print(self.styled.frame("Framed text", style="double"))
        print(self.styled.bullet_list(["item one", "item two"]))
```

Available helpers: `style()`, `h1()`, `h2()`, `h3()`, `frame()`, `bullet_list()`, `numbered_list()`, `blockquote()`, `code()`, `indent()`.

---

## 9. Accessing Other Mods

Prefer services over direct mod access. When you do need the mod instance:

```python
other = core.get_mod("mod_other")
if other is not None:
    other.some_public_method()
```

Never import a mod's internals directly (`from mod_other.main import ...` is forbidden).

---

## 10. Full Example — `mod_counter`

A mod that counts ENGINE_TICK events and prints a styled report on shutdown.

```
mods/default/mod_counter/
├── manifest.json
└── main.py
```

**manifest.json**

```json
{
    "name": "mod_counter",
    "version": "1.0.0",
    "type": "extension",
    "priority": 40,
    "entrypoint": "main.py",
    "requires": {
        "mod_styled_text": ">=1.0.0"
    },
    "conflicts": {},
    "permissions": []
}
```

**main.py**

```python
from resources.__handler import Handler


class Mod:
    def on_load(self, core):
        self.core = core
        self.ticks = 0

        core.subscribe(
            "ENGINE_TICK",
            Handler(
                self._on_tick,
                name="counter_tick",
                priority=10,
                mode="normal",
                mod_name="mod_counter",
            ),
        )

    def on_init(self, core):
        self.styled = core.get_service("styled_text")
        self.logger = core.get_service("logger")

    def on_ready(self, event):
        if self.logger:
            self.logger.log("INFO", "mod_counter", "Counter started.")

    def on_shutdown(self, core):
        if self.styled:
            report = self.styled.frame(
                f"Total ticks: {self.ticks}", style="double"
            )
            print(report)
        else:
            print(f"Total ticks: {self.ticks}")

    def _on_tick(self, event):
        self.ticks += 1
```
