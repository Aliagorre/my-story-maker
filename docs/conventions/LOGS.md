\# my-story-maker/docs/conventions/LOGS.md

# **StoryMaker V7 — Logging Conventions**

---

## **1. Introduction**

The logging system in StoryMaker V7 is designed to be:

* **minimal** (no styling in the core)
* **predictable** (strict format)
* **stable** (no arbitrary changes)
* **extensible** (mods can enhance output)
* **secure** (no leakage of sensitive information)

The core provides a simple internal logger.
Mods may use this logger or expose their own logging system via a service.

---

## **2. Objectives**

The logging system is intended to:

* support debugging
* track the engine lifecycle
* diagnose mod errors
* understand dependency resolution and loading
* provide consistent logging across mods

Logs must remain **readable**, even without advanced UI.

---

## **3. Log Levels**

StoryMaker V7 uses standard logging levels:

| Level      | Description                               |
| ---------- | ----------------------------------------- |
| `DEBUG`    | Technical details, useful for development |
| `INFO`     | General operational information           |
| `WARNING`  | Non-critical issues                       |
| `ERROR`    | Non-fatal errors                          |
| `CRITICAL` | Fatal errors requiring shutdown           |

Mods must use these levels consistently.

---

## **4. Log Format**

The official format is:

```id="l1"
[LEVEL] [timestamp] [source] message
```

### **4.1 Example**

```
[INFO] [12:03:45] [core] Engine ready
```

### **4.2 Rules**

* `LEVEL` must always be uppercase
* `timestamp` must follow `HH:MM:SS` format
* `source` must be:

  * `"core"` for engine logs
  * `"mod_<name>"` for mods
* `message` must be clear and concise

---

## **5. Styling**

### **5.1 No Styling in the Core**

The core must never:

* apply colors
* add visual formatting
* use decorative elements

---

### **5.2 Styling via Mods**

Styling is handled by mods such as `mod_styled_text`, which may:

* add colors
* format logs visually
* improve readability

UI mods may:

* display logs in windows
* filter by level
* provide extended timestamps

---

## **6. Log Sources**

### **6.1 Core Logs**

The core logs:

* lifecycle events (`ENGINE_BOOT`, `ENGINE_READY`, etc.)
* mod loading
* internal errors
* dependency resolution
* conflicts
* requested permissions

---

### **6.2 Mod Logs**

Mods may log:

* their own errors
* important actions
* internal states
* emitted events

They should use the core logger to maintain consistency.

---

## **7. Logging and Errors**

### **7.1 Core Errors**

Example:

```
[ERROR] [12:04:12] [core] Failed to load manifest for mod_x
```

---

### **7.2 Mod Errors**

Example:

```
[ERROR] [12:05:33] [mod_script_engine] Exception during script execution
```

The core also emits a `MOD_ERROR` event.

---

### **7.3 Fatal Errors**

Example:

```
[CRITICAL] [12:06:01] [core] Fatal error: dependency resolution failed
```

The engine proceeds to shutdown.

---

## **8. Best Practices**

* Always use the core logger
* Never use `print()` in the core or in mods
* Use `DEBUG` for technical details
* Use `INFO` for key steps
* Use `WARNING` for non-blocking issues
* Use `ERROR` for recoverable failures
* Use `CRITICAL` for fatal errors

---

## **9. Summary**

| Element | Rule                                   |
| ------- | -------------------------------------- |
| Format  | `[LEVEL] [timestamp] [source] message` |
| Styling | None in the core                       |
| Levels  | DEBUG, INFO, WARNING, ERROR, CRITICAL  |
| Source  | `core` or `mod_<name>`                 |
| UI      | Handled by mods                        |
| Goal    | Readability, stability, extensibility  |
