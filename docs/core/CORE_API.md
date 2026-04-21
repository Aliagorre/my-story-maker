\# my-story-maker/docs/core/CORE_API.md

# **StoryMaker V7 — Core API Specification**

---

## **1. Introduction**

The Core API is the minimal public interface exposed to mods.
It enables:

* emitting events
* subscribing to events
* registering services
* accessing services
* retrieving manifests
* accessing loaded mods
* logging consistently

The core exposes **no business logic**.
The API is intentionally **small**, **stable**, and **predictable**.

---

## **2. API Overview**

The `core` object, provided to mods via lifecycle hooks (`on_load`, `on_init`, etc.), exposes the following methods:

### **Complete List**

| Method                                  | Description                                 |
| --------------------------------------- | ------------------------------------------- |
| `core.emit(event_name, payload={})`     | Emit an event                               |
| `core.subscribe(event_name, callback)`  | Subscribe to an event                       |
| `core.register_service(name, instance)` | Register a service                          |
| `core.get_service(name)`                | Retrieve a service                          |
| `core.get_mod(name)`                    | Retrieve a mod instance                     |
| `core.get_manifest(name)`               | Retrieve a mod manifest                     |
| `core.log(level, message)`              | Log a message                               |
| `core.get_all_mods()`                   | List all loaded mods                        |
| `core.get_core_version()`               | Get core version                            |
| `core.get_event_bus()`                  | Direct access (advanced) to EventBus        |
| `core.get_service_registry()`           | Direct access (advanced) to ServiceRegistry |

Mods must interact **only through this API**.
Direct access to core internals is not allowed.

---

## **3. Detailed API**

---

### **3.1 `core.emit(event_name, payload={})`**

Emits an event to the global EventBus.

#### **Signature**

```python id="c1"
core.emit(event_name: str, payload: dict = {})
```

#### **Rules**

* `event_name` must follow the `CATEGORY_ACTION` convention
* `payload` must be a dictionary (never `None`)
* The core automatically injects:

  * `source`
  * `timestamp`

#### **Example**

```python id="c2"
core.emit("UI_BUTTON_CLICKED", {"button": "start"})
```

---

### **3.2 `core.subscribe(event_name, callback)`**

Subscribes to an event.

#### **Signature**

```python id="c3"
core.subscribe(event_name: str, callback: Callable)
```

#### **Rules**

* `callback(event)` must accept a single argument
* A mod can subscribe to multiple events
* Subscriptions are active from `on_load`

#### **Example**

```python id="c4"
def on_ready(event):
    print("Engine is ready!")

core.subscribe("ENGINE_READY", on_ready)
```

---

### **3.3 `core.register_service(name, instance)`**

Registers a service for other mods to use.

#### **Signature**

```python id="c5"
core.register_service(name: str, instance: Any)
```

#### **Rules**

* `name` must be in `snake_case`
* A service can only be registered once
* If a service already exists → error + `MOD_ERROR` event

#### **Example**

```python id="c6"
core.register_service("script_engine", ScriptEngine())
```

---

### **3.4 `core.get_service(name)`**

Retrieves a registered service.

#### **Signature**

```python id="c7"
core.get_service(name: str) -> Any
```

#### **Rules**

* Returns `None` if the service does not exist
* Mods must handle missing services safely

#### **Example**

```python id="c8"
engine = core.get_service("script_engine")
```

---

### **3.5 `core.get_mod(name)`**

Returns the instance of a loaded mod.

#### **Signature**

```python id="c9"
core.get_mod(name: str) -> ModInstance
```

#### **Rules**

* `name` must match the exact mod name (`mod_xxx`)
* Returns `None` if the mod is not loaded

#### **Example**

```python id="c10"
cmd_mod = core.get_mod("mod_cmd")
```

---

### **3.6 `core.get_manifest(name)`**

Returns a mod’s manifest.

#### **Signature**

```python id="c11"
core.get_manifest(name: str) -> dict
```

#### **Example**

```python id="c12"
manifest = core.get_manifest("mod_graph_editor")
```

---

### **3.7 `core.log(level, message)`**

Logs a message using the core logger.

#### **Signature**

```python id="c13"
core.log(level: str, message: str)
```

#### **Allowed Levels**

* `DEBUG`
* `INFO`
* `WARNING`
* `ERROR`
* `CRITICAL`

#### **Example**

```python id="c14"
core.log("INFO", "Graph editor initialized")
```

---

### **3.8 `core.get_all_mods()`**

Returns the list of loaded mods.

#### **Signature**

```python id="c15"
core.get_all_mods() -> list[str]
```

#### **Example**

```python id="c16"
mods = core.get_all_mods()
```

---

### **3.9 `core.get_core_version()`**

Returns the core version (SemVer).

#### **Signature**

```python id="c17"
core.get_core_version() -> str
```

---

### **3.10 `core.get_event_bus()` *(advanced use)*

Returns the internal EventBus instance.

#### **Signature**

```python id="c18"
core.get_event_bus() -> EventBus
```

#### **Rules**

* Intended for advanced use cases only
* Prefer `core.emit()` and `core.subscribe()`

---

### **3.11 `core.get_service_registry()` *(advanced use)*

Returns the internal ServiceRegistry instance.

#### **Signature**

```python id="c19"
core.get_service_registry() -> ServiceRegistry
```

---

## **4. What the API Must Never Expose**

The API must never allow:

* direct access to core internal structures
* direct interaction between mods without mediation
* access to internal threads
* direct file system control by the core
* direct permission management
* direct access to internal loaders

The API must remain **small**, **stable**, and **predictable**.

---

## **5. Summary**

| Function               | Purpose               |
| ---------------------- | --------------------- |
| `emit`                 | Emit an event         |
| `subscribe`            | Subscribe to an event |
| `register_service`     | Expose a service      |
| `get_service`          | Retrieve a service    |
| `get_mod`              | Retrieve a mod        |
| `get_manifest`         | Retrieve a manifest   |
| `log`                  | Log messages          |
| `get_all_mods`         | List loaded mods      |
| `get_core_version`     | Get core version      |
| `get_event_bus`        | Advanced access       |
| `get_service_registry` | Advanced access       |
