\# my-story-maker/docs/conventions/MANIFEST.md

# **StoryMaker V7 — Manifest Specification**

---

## **1. Introduction**

Every StoryMaker V7 mod must include a file:

```
manifest.json
```

This file defines:

* the mod's identity
* its version
* its dependencies
* its conflicts
* its permissions
* its type
* its entry point
* its metadata

The manifest is **mandatory** and must strictly follow this specification.

---

## **2. General Structure**

A complete valid manifest:

```json
{
  "name": "mod_example",
  "version": "1.0.0",
  "type": "extension",
  "priority": 50,
  "entrypoint": "main.py",

  "requires": {
    "mod_other": ">=1.0.0,<2.0.0"
  },

  "conflicts": {
    "mod_old": "*"
  },

  "permissions": [
    "filesystem_read",
    "filesystem_write",
    "ui"
  ],

  "description": "A short description of the mod.",
  "author": "Author Name",
  "license": "MIT"
}
```

All fields are described below.

---

## **3. Required Fields**

### **3.1 `name`**

Unique identifier of the mod.

* Format: `mod_<name>`
* `snake_case`
* lowercase only

Examples:

* `mod_cmd`
* `mod_error_and_log`

---

### **3.2 `version`**

The mod version, using **strict SemVer**.

Examples:

* `1.0.0`
* `2.3.1`

---

### **3.3 `type`**

Defines the mod type.

| Type           | Description                                                                 |
| -------------- | --------------------------------------------------------------------------- |
| `core_engine`  | Reserved for the engine core                                                |
| `core_default` | Essential built-in mods, loaded before all others                          |
| `default`      | Non-critical mods loaded automatically, located in `/core/default_mods/`   |
| `extension`    | Standard or optional mods, located in `/mods/default/` or external paths   |
| `experimental` | Unstable or experimental mods                                               |

> **Note:** `core_default` and `default` mods are bundled with the engine.
> Only `extension` and `experimental` mods are typically provided externally.

---

### **3.4 `priority`**

Defines load priority.

* Integer value (recommended range: 0–1000)
* Higher values are loaded earlier
* **Dependencies are always loaded first**, regardless of priority

Examples:

* `0` → lowest priority
* `100` → standard importance
* `900` → core-level priority

---

### **3.5 `entrypoint`**

Path to the main Python file of the mod.

Example:

```json
"entrypoint": "main.py"
```

---

## **4. Optional (Recommended) Fields**

### **4.1 `requires`**

Defines required dependencies.

Format:

```json
"requires": {
  "mod_name": ">=1.0.0,<2.0.0"
}
```

Rules:

* Versions are strictly validated
* The mod is disabled if a dependency is missing or incompatible

---

### **4.2 `conflicts`**

Defines incompatible mods.

Format:

```json
"conflicts": {
  "mod_name": "*"
}
```

or:

```json
"conflicts": {
  "mod_name": "<1.5.0"
}
```

---

### **4.3 `permissions`**

List of permissions requested by the mod.

Available permissions:

* `filesystem_read`
* `filesystem_write`
* `network`
* `ui`
* `spawn_process`
* `script_eval`
* `unsafe` (full access)

The core may:

* allow
* deny
* log
* or request confirmation (future UI)

---

### **4.4 `description`**

Short description of the mod.

---

### **4.5 `author`**

Name or alias of the author.

---

### **4.6 `license`**

License of the mod.

Examples:

* `MIT`
* `GPL-3.0`
* `Apache-2.0`

---

## **5. Reserved Fields (Future Use)**

The following fields are reserved for future extensions:

* `hooks`
* `services`
* `assets`
* `config_schema`

They must not be used at this stage.

---

## **6. Manifest Validation**

The core validates:

* presence of required fields
* version format
* dependency consistency
* absence of dependency cycles
* declared conflicts
* requested permissions

If validation fails:

* the mod is disabled
* a `MOD_MANIFEST_ERROR` event is emitted

---

## **7. Complete Example**

```json
{
  "name": "mod_cmd",
  "version": "1.0.0",
  "type": "core_default",
  "priority": 100,
  "entrypoint": "main.py",

  "requires": {
    "mod_error_and_log": ">=1.0.0"
  },

  "conflicts": {
    "mod_old_cmd": "*"
  },

  "permissions": [
    "ui"
  ],

  "description": "Provides a command-line interface for StoryMaker V7.",
  "author": "StoryMaker Team",
  "license": "MIT"
}
```

---

## **8. Summary**

| Field         | Required | Description           |
| ------------- | -------- | --------------------- |
| `name`        | ✔        | Mod identifier        |
| `version`     | ✔        | SemVer version        |
| `type`        | ✔        | Mod type              |
| `priority`    | ✔        | Load priority         |
| `entrypoint`  | ✔        | Main file             |
| `requires`    | ✔        | Dependencies          |
| `conflicts`   | ✔        | Incompatibilities     |
| `permissions` | ✖        | Requested permissions |
| `description` | ✖        | Description           |
| `author`      | ✖        | Author                |
| `license`     | ✖        | License               |
