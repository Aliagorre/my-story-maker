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
They are all located in `/core/default_mods/`.

They are classified into three categories:

* **core_default**: required for the engine to function
* **default**: provided by default but not critical
* **extension**: additional useful but non-essential features (located in `/mods/default/`)

---

## 2. Default Mods List

Below is the official list of mods provided with StoryMaker V7.

---

# 2.1 Core Default Mods (required)

These mods are necessary for the engine to function.
They must be loaded before all others.
Located in `/core/default_mods/`.

---

### **mod_error_and_log**

**Type:** core_default
**Role:**

* Provides the engine's minimal logging system
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

### **mod_mod_manager**

**Type:** core_default
**Role:**

* Manages the list of loaded and available mods
* Exposes mod metadata to other mods
* Provides runtime mod inspection capabilities

**Services provided:**

* `mod_manager`

**Dependencies:**

* `mod_error_and_log`

**Priority:** 850

---

### **mod_file_system**

**Type:** core_default
**Role:**

* Provides a unified file system access layer
* Abstracts read/write operations for other mods
* Manages paths and directory conventions

**Services provided:**

* `file_system`

**Dependencies:**

* `mod_error_and_log`

**Priority:** 800

---

### **mod_base_adventure**

**Type:** core_default
**Role:**

* Defines the base data structures for adventures
* Provides shared types used by other adventure-related mods
* Acts as a foundation for `mod_adventure_loader` and external mods

**Services provided:**

* `base_adventure`

**Dependencies:**

* `mod_error_and_log`

**Priority:** 400

---

# 2.2 Default Mods (non-critical)

These mods are loaded automatically but are not required for the engine to function.
Located in `/core/default_mods/`.

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
* `mod_base_adventure`
* `mod_file_system`

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
Located in `/mods/default/`.

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

| Mod                  | Type         | Main Role              | Services         | Priority | Location             |
| -------------------- | ------------ | ---------------------- | ---------------- | -------- | -------------------- |
| mod_error_and_log    | core_default | Logs + errors          | logger           | 900      | core/default_mods/   |
| mod_mod_manager      | core_default | Mod management         | mod_manager      | 850      | core/default_mods/   |
| mod_file_system      | core_default | File system access     | file_system      | 800      | core/default_mods/   |
| mod_base_adventure   | core_default | Base adventure types   | base_adventure   | 400      | core/default_mods/   |
| mod_styled_text      | core_default | Text styling           | styled_text      | 120      | core/default_mods/   |
| mod_cmd              | core_default | CLI interface          | cmd_interface    | 100      | core/default_mods/   |
| mod_script_engine    | default      | Script engine          | script_engine    | 200      | core/default_mods/   |
| mod_adventure_loader | default      | Adventure loading      | adventure_manager| 250      | core/default_mods/   |
| mod_ui_terminal      | default      | Text UI                | ui_terminal      | 300      | core/default_mods/   |
| mod_graph_editor     | extension    | Narrative editor       | graph_api        | 50       | mods/default/        |
| mod_debug_tools      | extension    | Debug tools            | debug_tools      | 80       | mods/default/        |

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
