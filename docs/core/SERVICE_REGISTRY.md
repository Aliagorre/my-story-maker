\# my-story-maker/docs/core/SERVICE_REGISTRY.md

# StoryMaker V7 — Service Registry Specification

## 1. Introduction

The **Service Registry** is a central component of the core.  
It allows mods to:

- expose reusable services,  
- access services provided by other mods,  
- share stable APIs without direct dependencies,  
- avoid cross-imports between mods.

The Service Registry is designed to be:

- **simple**,  
- **predictable**,  
- **robust**,  
- **strict**,  
- **compatible with any type of service** (objects, functions, classes, wrappers, etc.).

---

## 2. Objectives

The Service Registry must allow:

- registering a service under a unique name,  
- retrieving a service by name,  
- checking the existence of a service,  
- preventing collisions,  
- ensuring the stability of exposed APIs.

It must **never**:

- handle business logic,  
- modify services,  
- enforce a specific type,  
- manage the lifecycle of services.

---

## 3. Service Registry API

The Service Registry is **not directly exposed** to mods.  
Mods interact with it through the core API:

- `core.register_service(name, instance)`
- `core.get_service(name)`

For internal documentation, the full API is described below.

---

### 3.1 `register(name: str, instance: Any)`

Registers a service.

#### Internal Signature

```python
register(name: str, instance: Any)
```

#### Rules

* `name` must be in snake_case.
* `instance` can be any Python object.
* A service can only be registered **once**.
* If a service already exists:

  * log `ERROR`,
  * emit `MOD_ERROR`,
  * registration is refused.

#### Example

```python
service_registry.register("script_engine", ScriptEngine())
```

---

### 3.2 `get(name: str) -> Any`

Retrieves a service.

#### Internal Signature

```python
get(name: str) -> Any
```

#### Rules

* Returns `None` if the service does not exist.
* The calling mod must handle missing services.

#### Example

```python
engine = service_registry.get("script_engine")
```

---

### 3.3 `exists(name: str) -> bool`

Checks if a service exists.

#### Internal Signature

```python
exists(name: str) -> bool
```

#### Example

```python
if service_registry.exists("styled_text"):
    ...
```

---

### 3.4 `list_services() -> list[str]`

Returns the list of registered services.

#### Internal Signature

```python
list_services() -> list[str]
```

---

## 4. Service Lifecycle

### 4.1 Registration

Services should be registered in:

* `on_load` (if the service is simple),
* or `on_init` (if the service depends on other services).

### 4.2 Availability

A service is available:

* immediately after registration,
* to all mods,
* until shutdown.

### 4.3 Destruction

The Service Registry **never destroys** services.
Mods must handle their own cleanup in `on_shutdown`.

---

## 5. Best Practices

### 5.1 One service = one stable API

A service should:

* expose a clear API,
* document its methods,
* remain stable across minor versions,
* avoid breaking changes.

### 5.2 Do not expose temporary objects

❌ Bad:

```python
core.register_service("temp_buffer", [])
```

✔ Correct:

```python
core.register_service("adventure_manager", AdventureManager())
```

### 5.3 Do not expose unnecessary services

A service should be:

* useful to multiple mods,
* stable,
* coherent.

### 5.4 Avoid overly generic names

❌ `utils`
❌ `helpers`
❌ `misc`

✔ `script_engine`
✔ `styled_text`
✔ `adventure_manager`

---

## 6. Errors and Conflict Handling

### 6.1 Service already registered

If a mod attempts to register an existing service:

* log `[ERROR]`,
* emit `MOD_ERROR`,
* registration is refused.

### 6.2 Missing service

If a mod tries to use a missing service:

* the mod must handle the error,
* the core does not raise an exception,
* the mod may emit a `[WARNING]` log.

### 6.3 Critical services

Some services provided by core mods are considered critical:

* `styled_text`
* `cmd_interface`
* `script_engine`
* `adventure_manager`

If one is missing:

* emit `ENGINE_ERROR`,
* log `[CRITICAL]`,
* shutdown may occur.

---

## 7. Summary

| Function        | Role               |
| --------------- | ------------------ |
| `register`      | Register a service |
| `get`           | Retrieve a service |
| `exists`        | Check existence    |
| `list_services` | List services      |

The Service Registry is:

* simple,
* stable,
* strict,
* essential for engine modularity.

```
```
