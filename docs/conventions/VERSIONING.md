\# my-story-maker/docs/conventions/VERSIONING.md

# **StoryMaker V7 — Versioning Conventions**

---

## **1. Introduction**

StoryMaker V7 uses **strict Semantic Versioning (SemVer)** for:

* the core
* core mods
* default mods
* all compatible external mods

The goal is to ensure:

* backward compatibility
* core stability
* predictable updates
* clear dependency management between mods

---

## **2. Version Format**

The official format is:

```id="v1"
MAJOR.MINOR.PATCH
```

Examples:

* `1.0.0`
* `2.3.1`
* `0.9.4`

---

## **3. Version Numbering**

### **3.1 MAJOR**

Incremented when:

* breaking changes are introduced
* major structural changes occur
* core behavior is significantly altered
* public APIs are removed or modified incompatibly

Examples:

* changes to the event system
* redesign of the mod loader
* modification of the manifest format

---

### **3.2 MINOR**

Incremented when:

* backward-compatible features are added
* new events are introduced
* new services are added
* internal improvements do not break compatibility

Examples:

* adding a new lifecycle hook
* introducing an optional service
* adding a non-mandatory event

---

### **3.3 PATCH**

Incremented when:

* bugs are fixed
* internal optimizations are made
* minor improvements are implemented
* documentation is updated

No visible behavioral changes should occur.

---

## **4. Core Versioning**

The core follows strict SemVer:

* **MAJOR** changes must remain rare
* **MINOR** increments reflect new capabilities
* **PATCH** increments address fixes and improvements

The core must remain **stable** and **predictable**.

---

## **5. Mod Versioning**

Each mod maintains its own independent version.

### **5.1 Rules**

* Increment **MAJOR** when breaking internal APIs or services
* Increment **MINOR** when adding backward-compatible features
* Increment **PATCH** when fixing bugs

---

### **5.2 Declared Compatibility**

In the manifest, a mod may define dependencies:

```json id="v2"
"requires": {
    "mod_script_engine": ">=1.2.0,<2.0.0"
}
```

Supported operators:

* `>=`
* `<=`
* `>`
* `<`
* `=`
* `*` (any version)
* combinations using commas

---

### **5.3 Declared Conflicts**

A mod may define conflicts:

```json id="v3"
"conflicts": {
    "mod_old_logger": "*"
}
```

or:

```json id="v4"
"conflicts": {
    "mod_graph": "<1.5.0"
}
```

---

## **6. Core Mods Versioning**

Core mods follow the same rules as standard mods, with additional constraints:

* must remain **aligned with the core**
* should avoid breaking changes
* should remain compatible across multiple minor core versions

---

## **7. Default Mods Versioning**

Default mods:

* may evolve more rapidly
* may introduce experimental features
* must still follow strict SemVer
* must clearly declare dependencies

---

## **8. External Mods Versioning**

External mods must:

* follow strict SemVer
* declare dependencies explicitly
* avoid undocumented breaking changes
* use reasonable version ranges

---

## **9. Version Resolution**

The core enforces strict version resolution:

* unmet version requirements → mod is disabled
* detected conflicts → mod is disabled
* multiple versions of the same mod → error
* incompatible core mod → critical error

---

## **10. Summary**

| Element      | Rule                          |
| ------------ | ----------------------------- |
| Format       | `MAJOR.MINOR.PATCH`           |
| MAJOR        | Breaking changes              |
| MINOR        | Backward-compatible additions |
| PATCH        | Bug fixes                     |
| Mods         | Independent versioning        |
| Dependencies | SemVer ranges                 |
| Conflicts    | Explicitly declared           |
| Core         | Stable, rare MAJOR changes    |
