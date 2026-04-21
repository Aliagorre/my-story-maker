\# my-story-maker/docs/convention/NAMING.md

# **StoryMaker V7 — Naming Conventions**

---

## **1. Introduction**

This document defines the official naming conventions for StoryMaker V7.
They apply to the **core**, **core mods**, **default mods**, and all **external mods** intended to be compatible with the ecosystem.

These conventions ensure:

* code readability
* project consistency
* ease of navigation
* long-term maintainability

---

## **2. Mod Naming**

### **2.1 General Format**

All mods must follow this format:

```id="n1"
mod_<name>
```

Valid examples:

* `mod_cmd`
* `mod_error_and_log`
* `mod_ui`
* `mod_script_engine`
* `mod_graph_editor`

---

### **2.2 Rules**

* Names must use **snake_case**
* Names should be **concise and descriptive**
* Names must reflect the **primary responsibility** of the mod

Directory placement:

```id="n2"
/core/default_mods/mod_<name>/
```

```id="n3"
/mods/default/mod_<name>/
```

---

## **3. Python File Names**

### **3.1 Format**

* `snake_case`
* lowercase only
* words separated by underscores

Examples:

* `event_bus.py`
* `mod_loader.py`
* `service_registry.py`
* `dependency_resolver.py`

---

### **3.2 Rules**

* One file = one clear responsibility
* Avoid catch-all files
* Avoid generic names such as `utils.py` or `helpers.py`

---

## **4. Class Names**

### **4.1 Format**

* `PascalCase`

Examples:

* `EventBus`
* `ModLoader`
* `ServiceRegistry`
* `AdventureManager`

---

### **4.2 Rules**

* Names must represent a **clear concept**
* One class = one responsibility
* Avoid “god classes”

---

## **5. Functions and Methods**

### **5.1 Format**

* `snake_case`
* explicit verbs

Examples:

* `load_manifest()`
* `resolve_dependencies()`
* `emit_event()`
* `register_service()`
* `get_mod()`

---

### **5.2 Rules**

* One function = one action
* Names must clearly describe behavior
* Avoid unclear abbreviations

---

## **6. Variable Names**

### **6.1 Format**

* `snake_case`
* concise but descriptive

Examples:

* `mod_list`
* `manifest_data`
* `service_name`
* `event_payload`

---

### **6.2 Rules**

* Avoid single-letter variables (except loop indices like `i`, `j`)
* Avoid vague names such as `data`, `info`, `temp`

---

## **7. Event Names**

### **7.1 General Format**

Events must follow:

```id="n4"
CATEGORY_ACTION
```

All uppercase.

---

### **7.2 Official Categories**

* `ENGINE_*`
* `MOD_*`
* `UI_*`
* `ADVENTURE_*`
* `SCRIPT_*`
* `FS_*`

---

### **7.3 Examples**

* `ENGINE_BOOT`
* `ENGINE_READY`
* `MOD_ERROR`
* `UI_RENDER`
* `ADVENTURE_LOADED`
* `SCRIPT_EXECUTION_FAILED`

---

### **7.4 Rules**

* Always uppercase
* Always use an underscore between category and action
* Action must clearly describe a state or operation

---

## **8. Service Names**

### **8.1 Format**

* `snake_case`
* descriptive naming

Examples:

* `cmd_interface`
* `styled_text`
* `script_engine`
* `adventure_manager`

---

### **8.2 Rules**

* Name must reflect the **main responsibility**
* A service represents a **stable API** exposed by a mod

---

## **9. Directory Names**

### **9.1 Format**

* `snake_case`
* no spaces
* no uppercase letters

Examples:

* `core`
* `default_mods`
* `docs`
* `examples`
* `assets`

---

## **10. Summary**

| Element     | Format          | Example           |
| ----------- | --------------- | ----------------- |
| Mod         | `mod_<name>`    | `mod_cmd`         |
| Python File | snake_case      | `event_bus.py`    |
| Class       | PascalCase      | `ModLoader`       |
| Function    | snake_case      | `load_manifest()` |
| Variable    | snake_case      | `manifest_data`   |
| Event       | CATEGORY_ACTION | `ENGINE_READY`    |
| Service     | snake_case      | `script_engine`   |
| Directory   | snake_case      | `default_mods`    |
