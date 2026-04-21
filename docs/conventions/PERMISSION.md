\# my-story-maker/docs/conveentions/PERMISSION.md

# **StoryMaker V7 — Permissions Specification**

---

## **1. Introduction**

Permissions define **what a mod is allowed to do**.
They serve to:

* protect the engine from unsafe behavior
* clarify a mod’s intent
* improve auditability and trust
* prepare for a future “safe” or sandboxed mode

In development mode, the core **does not block any permissions**, but it **logs all requested permissions**.
In a future secure mode, some permissions may be restricted or require user approval.

---

## **2. Declaring Permissions**

Permissions are defined in a mod’s `manifest.json`:

```json id="p1"
"permissions": [
  "filesystem_read",
  "filesystem_write",
  "ui"
]
```

If the field is omitted, the mod is considered to request **no explicit permissions**.

---

## **3. Official Permission List**

Below is the complete list of available permissions in StoryMaker V7.

---

### **3.1 `filesystem_read`**

Allows the mod to **read files** from disk.

**Typical uses:**

* loading adventures
* reading configuration files
* loading assets

**Risks:**

* access to sensitive files

---

### **3.2 `filesystem_write`**

Allows the mod to **write files** to disk.

**Typical uses:**

* saving data
* writing logs
* exporting adventures

**Risks:**

* overwriting files
* creating unwanted files

---

### **3.3 `network`**

Allows the mod to perform **network operations**.

**Typical uses:**

* downloading mods
* syncing data
* multiplayer features

**Risks:**

* data exfiltration
* reliance on external systems

---

### **3.4 `ui`**

Allows the mod to create or manage **user interfaces**.

**Typical uses:**

* graphical windows
* terminal interfaces
* visual editors

**Risks:**

* intrusive pop-ups
* excessive UI usage

---

### **3.5 `spawn_process`**

Allows the mod to **launch external processes**.

**Typical uses:**

* opening external tools
* running system scripts

**Risks:**

* execution of unsafe commands

---

### **3.6 `script_eval`**

Allows the mod to **execute dynamic code** (DSLs, scripts, expressions).

**Typical uses:**

* internal scripting engines
* expression evaluation

**Risks:**

* execution of untrusted code

---

### **3.7 `unsafe`**

Special permission that grants **full access**:

* file system (read/write)
* network
* UI
* external processes
* dynamic code execution
* direct system access

This permission should be used **only** for:

* core mods
* advanced tooling
* development environments

It must be explicitly declared:

```json id="p2"
"permissions": ["unsafe"]
```

---

## **4. General Rules**

### **4.1 Development Mode**

* all permissions are allowed
* the core logs requested permissions
* no restrictions are enforced

---

### **4.2 Secure Mode (Future)**

* some permissions may be denied
* some may require user confirmation
* non-compliant mods may be disabled

---

### **4.3 No Implicit Permissions**

There are **no implicit permissions**.
If a mod does not declare a permission, it **must not use it**.

---

### **4.4 Permissions by Mod Type**

| Type           | Recommended Permissions      |
| -------------- | ---------------------------- |
| `core_engine`  | `unsafe`                     |
| `core_default` | depends on responsibility    |
| `extension`    | minimal required permissions |
| `experimental` | explicit and documented      |

---

## **5. Best Practices**

* Request **only the minimum permissions** required
* Clearly explain in the README **why permissions are needed**
* Default mods should be **transparent** about permissions
* External mods should avoid `unsafe` unless strictly necessary

---

## **6. Summary**

| Permission         | Description               |
| ------------------ | ------------------------- |
| `filesystem_read`  | Read files                |
| `filesystem_write` | Write files               |
| `network`          | Network access            |
| `ui`               | Create/manage UI          |
| `spawn_process`    | Launch external processes |
| `script_eval`      | Execute dynamic code      |
| `unsafe`           | Full system access        |
