\# my-story-maker/docs/mods/DEFAULT_MODS_OVERVIEW.md

# StoryMaker V7 — Default Mods Overview

## 1. Introduction

StoryMaker V7 includes a set of **default mods** that provide:

* essential engine functionality,
* critical services,
* basic interaction tools,
* building blocks for creating adventures,
* foundations for external mods.

These mods are loaded automatically, unless explicitly disabled in development mode.

They are classified into three categories:

* **core_default**: required for the engine to function
* **default**: provided by default but not critical
* **extension**: additional useful but non-essential features

---

## 2. Default Mods List

Below is the official list of mods provided with StoryMaker V7.

---

# 2.1 Core Default Mods (required)

These mods are necessary for the engine to function.
They must be loaded before all others.

---

### **mod_error_and_log**

**Type:** core_default
**Role:**

* Provides the engine’s minimal logging system
* Handles mod errors
* Emits events like `MOD_ERROR`, `ENGINE_ERROR`, etc.

**Services provided:**

* `logger` (internal core API)

**Dependencies:** none
**Priority:** 900

---

### **mod_cmd**

**Type:** core_default
**Role:**

* Provides a simple command-line interface
* Allows interaction with the engine via terminal
* Serves as a base for debugging tools

**Services provided:**

* `cmd_interface`

**Dependencies:**

* `mod_error_and_log`

**Priority:** 100

---

### **mod_styled_text**

**Type:** core_default
**Role:**

* Provides text styling capabilities
* Allows other mods to display enriched text
* Adds colors, frames, formatting, etc.

**Services provided:**

* `styled_text`

**Dependencies:**

* `mod_error_and_log`

**Priority:** 120

---

# 2.2 Default Mods (non-critical)

These mods are loaded automatically but are not required for the engine to function.

---

### **mod_script_engine**

**Type:** default
**Role:**

* Provides an internal scripting engine
* Enables execution of DSLs, expressions, and rules
* Serves as a foundation for advanced mods

**Services provided:**

* `script_engine`

**Dependencies:**

* `mod_error_and_log`

**Priority:** 200

---

### **mod_adventure_loader**

**Type:** default
**Role:**

* Loads adventures from disk
* Manages internal formats
* Provides access to adventure data

**Services provided:**

* `adventure_manager`

**Dependencies:**

* `mod_error_and_log`
* `mod_script_engine`

**Priority:** 250

---

### **mod_ui_terminal**

**Type:** default
**Role:**

* Provides a simple text-based user interface
* Displays scenes, choices, and dialogue
* Acts as a fallback if no graphical UI is available

**Services provided:**

* `ui_terminal`

**Dependencies:**

* `mod_styled_text`

**Priority:** 300

---

# 2.3 Extension Mods (optional)

These mods add useful but non-essential features.

---

### **mod_graph_editor**

**Type:** extension
**Role:**

* Provides a narrative graph editor
* Allows visualization and editing of adventures
* Serves as a creation tool

**Services provided:**

* `graph_api`

**Dependencies:**

* `mod_script_engine`
* `mod_styled_text`

**Priority:** 50

---

### **mod_debug_tools**

**Type:** extension
**Role:**

* Provides advanced debugging tools
* Inspection of events, services, and mods
* Simple profiler

**Services provided:**

* `debug_tools`

**Dependencies:**

* `mod_error_and_log`

**Priority:** 80

---

## 3. Global Summary

| Mod                  | Type         | Main Role         | Services          | Priority |
| -------------------- | ------------ | ----------------- | ----------------- | -------- |
| mod_error_and_log    | core_default | Logs + errors     | logger            | 900      |
| mod_cmd              | core_default | CLI interface     | cmd_interface     | 100      |
| mod_styled_text      | core_default | Text styling      | styled_text       | 120      |
| mod_script_engine    | default      | Script engine     | script_engine     | 200      |
| mod_adventure_loader | default      | Adventure loading | adventure_manager | 250      |
| mod_ui_terminal      | default      | Text UI           | ui_terminal       | 300      |
| mod_graph_editor     | extension    | Narrative editor  | graph_api         | 50       |
| mod_debug_tools      | extension    | Debug tools       | debug_tools       | 80       |

---

## 4. Philosophy of Default Mods

Default mods must:

* be **simple**,
* be **stable**,
* be **well documented**,
* provide **reusable services**,
* serve as a **reference** for external mods,
* never break core compatibility.

They form the official **toolkit** of StoryMaker V7.
