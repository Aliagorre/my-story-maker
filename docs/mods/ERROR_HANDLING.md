\# my-story-maker/docs/mods/ERROR_HANDLING.md

# StoryMaker V7 — Error Handling Specification

## 1. Introduction

Error handling in StoryMaker V7 is based on three fundamental principles:

1. **The core must never crash.**
2. **A mod must never be able to crash the engine.**
3. **All errors must be logged and emitted as events.**

The system must be:

* **strict**,
* **robust**,
* **transparent**,
* **predictable**,
* **modular**.

---

## 2. Error types

StoryMaker V7 defines four categories of errors:

### 2.1 Core errors

Internal engine errors, including:

* loading failures,
* dependency resolution failures,
* lifecycle errors,
* internal EventBus or Service Registry errors.

---

### 2.2 Manifest errors

Errors related to:

* manifest structure,
* required fields,
* SemVer formatting,
* permissions,
* declared dependencies.

---

### 2.3 Dependency errors

Errors related to:

* missing dependencies,
* incompatible versions,
* cycles,
* declared conflicts.

---

### 2.4 Mod runtime errors

Errors occurring in:

* `on_load`,
* `on_init`,
* `on_ready`,
* `on_shutdown`,
* event handlers,
* internal mod logic.

---

## 3. General policy

### 3.1 The core must never raise unhandled exceptions

All internal exceptions must be:

* caught,
* logged,
* converted into events,
* handled safely.

---

### 3.2 A mod must never stop the engine

If a mod raises an exception:

* the error is caught,
* a log entry is emitted,
* a `MOD_ERROR` event is emitted,
* the mod may be disabled if necessary,
* the engine continues running.

---

### 3.3 Errors must be visible

Each error must:

* appear in logs,
* be associated with an event,
* be traceable.

---

## 4. Error-related events

The core emits the following events:

| Event                  | Description                       |
| ---------------------- | --------------------------------- |
| `MOD_ERROR`            | A mod error occurred              |
| `MOD_MANIFEST_ERROR`   | Invalid manifest                  |
| `MOD_DEPENDENCY_ERROR` | Invalid dependencies              |
| `MOD_CONFLICT`         | Conflict detected                 |
| `ENGINE_ERROR`         | Internal core error               |
| `ENGINE_FATAL_ERROR`   | Critical error requiring shutdown |

These events are defined in `EVENTS.md`.

---

## 5. Errors in lifecycle hooks

### 5.1 `on_load`

If an error occurs:

* log `[ERROR]`,
* emit `MOD_ERROR`,
* the mod is **disabled**.

---

### 5.2 `on_init`

If an error occurs:

* log `[ERROR]`,
* emit `MOD_ERROR`,
* the mod may be disabled.

---

### 5.3 `on_ready`

If an error occurs:

* log `[WARNING]` or `[ERROR]`,
* emit `MOD_ERROR`,
* the mod remains loaded but may be marked unstable.

---

### 5.4 `on_shutdown`

If an error occurs:

* log `[ERROR]`,
* the engine continues shutdown.

---

## 6. Errors in event handlers

### 6.1 Absolute rule

**A handler must never block event propagation.**

If a handler raises an exception:

* the error is caught,
* log `[ERROR]`,
* emit `MOD_ERROR`,
* propagation continues.

---

### 6.2 Impact

* The mod may be marked unstable,
* but the engine continues.

---

## 7. Automatic mod disabling

A mod is automatically disabled if:

* its manifest is invalid,
* its dependencies are invalid,
* a conflict is detected,
* a cycle is detected,
* `on_load` fails,
* `on_init` fails,
* it produces repeated errors.

A disabled mod:

* is not loaded,
* is not initialized,
* is not accessible via `core.get_mod()`,
* may still appear in logs as disabled.

---

## 8. Fatal errors

An error is considered **fatal** if:

* it prevents the engine from continuing,
* it blocks dependency resolution,
* it prevents loading of core mods,
* it corrupts the internal state of the core.

In this case:

* log `[CRITICAL]`,
* emit `ENGINE_FATAL_ERROR`,
* immediate shutdown.

---

## 9. Best practices for mods

* Always catch internal errors.
* Never allow exceptions to propagate.
* Log errors with context.
* Never block an event handler.
* Never assume a service exists.
* Always check dependencies via `core.get_service()`.
* Use `try/except` in lifecycle hooks.

---

## 10. Summary

| Error type          | Action                          |
| ------------------- | ------------------------------- |
| Invalid manifest    | Disable mod                     |
| Invalid dependency  | Disable mod                     |
| Conflict            | Disable mod                     |
| Cycle               | Disable mod                     |
| Error in `on_load`  | Disable mod                     |
| Error in `on_init`  | Possible disable                |
| Error in `on_ready` | Mark as unstable                |
| Error in handler    | Log + event, continue           |
| Core internal error | `ENGINE_ERROR`                  |
| Fatal error         | `ENGINE_FATAL_ERROR` + shutdown |

Error handling must remain **robust**, **predictable**, **non-blocking**, and **transparent**.
