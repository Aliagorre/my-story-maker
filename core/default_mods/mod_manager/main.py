# mods/default/mod_manager/main.py

"""
mod_manager — runtime mod lifecycle management.

Service : 'mod_manager'  (ModManagerService)
Commands: mods status | enable <name> | disable <name> | info <name>

Rules enforced on disable
─────────────────────────
• Core mods (type core_engine / core_default) are protected.
• mod_manager cannot disable itself.
• If any enabled mod declares the target as a required dependency,
  the operation is refused and the blockers are listed.

Rules enforced on enable
─────────────────────────
• All declared dependencies must be present and enabled.
• Installed dep version must satisfy the constraint from the manifest.
• Conflicts declared by the target mod and by other enabled mods
  are both checked.

Handler clean-up on disable
────────────────────────────
All event handlers are removed by matching either:
  1. handler.mod_name == mod_name  (Handler declared with explicit mod_name)
  2. handler.func.__self__ is instance  (bound method on the mod instance)
This covers handlers registered with or without a Handler wrapper.
"""

import importlib.util
import sys
import time
from typing import Optional

from core.__version import ConstraintResolver
from resources.LOG_LEVELS import ERROR, WARNING

MOD_NAME = "mod_manager"

_PROTECTED_TYPES = {"core_engine", "core_default"}


class ModDisplay:
    """Pretty-prints mod status tables and detail sheets."""

    _W_NAME = 30
    _W_VER = 8
    _W_TYPE = 14

    def __init__(self, get_styled):
        self._get = get_styled

    @property
    def _s(self):
        return self._get()

    # ── status table ──────────────────────────────────────────────────────

    def print_status(self, storage) -> None:
        s = self._s
        entries = [
            (name, storage.states.get(name, "unknown"), storage.manifests[name])
            for name in sorted(storage.manifests.keys())
        ]
        enabled = [e for e in entries if e[1] == "enable"]
        disabled = [e for e in entries if e[1] != "enable"]

        title = f"Mods  ({len(enabled)} enabled, {len(disabled)} disabled)"
        print()
        print("  " + (s.h2(title) if s else title))

        if enabled:
            print()
            hdr = "  ENABLED"
            print(s.h3(hdr) if s else hdr)
            for name, state, manifest in enabled:
                self._row(name, True, manifest, s)

        if disabled:
            print()
            hdr = "  DISABLED"
            print(s.h3(hdr) if s else hdr)
            for name, state, manifest in disabled:
                self._row(name, False, manifest, s)
        print()

    def _row(self, name: str, enabled: bool, manifest: dict, s) -> None:
        icon = "✓" if enabled else "✗"
        version = str(manifest.get("version", "?"))
        type_ = manifest.get("type", "?")
        priority = str(manifest.get("priority", "?"))
        desc = manifest.get("description", "")

        name_col = name.ljust(self._W_NAME)
        ver_col = version.ljust(self._W_VER)
        type_col = type_.ljust(self._W_TYPE)

        if s:
            if enabled:
                icon = s.style(icon, color="bright_green", styles=["bold"])
                name_col = s.style(name_col, styles=["bold"])
                ver_col = s.style(ver_col, color="bright_black")
                type_col = s.style(type_col, color="bright_black")
            else:
                icon = s.style(icon, color="bright_red")
                name_col = s.style(name_col, color="bright_black")
                ver_col = s.style(ver_col, color="bright_black")
                type_col = s.style(type_col, color="bright_black")

        prio = s.style(f"p:{priority}", color="bright_black") if s else f"p:{priority}"
        line = f"    {icon}  {name_col}  {ver_col}  {type_col}  {prio}"
        if desc:
            line += f"  {s.style(desc, color='bright_black') if s else desc}"
        print(line)

    # ── detail sheet ──────────────────────────────────────────────────────

    def print_info(self, name: str, storage) -> None:
        s = self._s
        manifest = storage.manifests.get(name)
        if manifest is None:
            self.err(f"No manifest for '{name}' (manifest may have failed validation).")
            return

        state = storage.states.get(name, "unknown")
        print()
        print(s.h1(f"  {name}") if s else f"  {name}")
        print()

        fields: list[tuple[str, str]] = [
            ("State", ("✓ enabled" if state == "enable" else "✗ disabled")),
            ("Version", str(manifest.get("version", "?"))),
            ("Type", manifest.get("type", "?")),
            ("Priority", str(manifest.get("priority", "?"))),
        ]
        for opt in ("description", "author", "license"):
            if manifest.get(opt):
                fields.append((opt.capitalize(), manifest[opt]))

        for label, value in fields:
            lbl = label.ljust(14)
            if s:
                lbl = s.style(lbl, color="cyan")
            print(f"    {lbl}  {value}")

        # requires
        requires = manifest.get("requires", {})
        if requires:
            print()
            print(s.h3("    Requires") if s else "    Requires:")
            for dep, constraint in requires.items():
                dep_state = storage.states.get(dep, "missing")
                ok = dep_state == "enable"
                icon = "✓" if ok else "✗"
                constraint_str = str(constraint) if constraint != "*" else "*"
                if s:
                    color = "bright_green" if ok else "bright_red"
                    icon = s.style(icon, color=color)
                print(f"      {icon}  {dep.ljust(28)} {constraint_str}")

        # conflicts
        conflicts = manifest.get("conflicts", {})
        if conflicts:
            print()
            print(s.h3("    Conflicts") if s else "    Conflicts:")
            for target, constraint in conflicts.items():
                print(f"      ✗  {target.ljust(28)} {constraint}")

        # errors
        errors = storage.errors.get(name, [])
        if errors:
            print()
            print(s.h3("    Errors") if s else "    Errors:")
            for err in errors:
                line = f"      • {err}"
                print(s.style(line, color="bright_red") if s else line)

        # path
        path = storage.paths.get(name)
        if path:
            print()
            lbl = "Path".ljust(14)
            if s:
                lbl = s.style(lbl, color="bright_black")
            print(f"    {lbl}  {path}")

        print()

    # ── feedback ──────────────────────────────────────────────────────────

    def ok(self, msg: str) -> None:
        s = self._s
        line = f"  ✓  {msg}"
        print(s.style(line, color="bright_green") if s else line)

    def err(self, msg: str) -> None:
        s = self._s
        line = f"  ✗  {msg}"
        print(s.style(line, color="bright_red") if s else line)

    def warn(self, msg: str) -> None:
        s = self._s
        line = f"  !  {msg}"
        print(s.style(line, color="yellow") if s else line)


class _RuntimeLoader:
    """
    Imports and instantiates a single mod entrypoint at runtime.
    Mirrors the logic of DynamicLoader / EntrypointLoader / ModInstantiator
    without touching ModStorage.
    """

    def __init__(self, log):
        self._log = log

    def load(self, mod_name: str, entrypoint) -> Optional[object]:
        try:
            if not entrypoint.exists() or entrypoint.suffix != ".py":
                self._log(ERROR, f"[mod_manager] entrypoint missing: {entrypoint}")
                return None

            # Unique module name avoids collisions with previous imports.
            uid = int(time.monotonic() * 1_000_000)
            module_name = f"_rt_{mod_name}_{uid}"
            spec = importlib.util.spec_from_file_location(module_name, entrypoint)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)  # type: ignore[union-attr]

            if not hasattr(module, "Mod") or not isinstance(module.Mod, type):
                self._log(ERROR, f"[mod_manager] no 'Mod' class in {entrypoint}")
                return None

            instance = module.Mod()
            for hook in ("on_load", "on_init", "on_ready", "on_shutdown"):
                if not callable(getattr(instance, hook, None)):
                    self._log(
                        ERROR, f"[mod_manager] missing hook '{hook}' in {mod_name}"
                    )
                    return None

            return instance

        except Exception as exc:
            self._log(ERROR, f"[mod_manager] import error for '{mod_name}': {exc}")
            return None


class ModManagerService:
    """
    Runtime mod lifecycle management.
    Registered as service 'mod_manager'.

    Usage from another mod
    ──────────────────────
        svc = core.get_service("mod_manager")
        ok, msg = svc.enable("mod_example")
        ok, msg = svc.disable("mod_example")
        states  = svc.list_all()   # → {"mod_name": "enable"|"disable", …}
    """

    def __init__(self, core, log):
        self._core = core
        self._log = log
        self._loader = _RuntimeLoader(log)

    # ── public API ────────────────────────────────────────────────────────

    def list_all(self) -> dict[str, str]:
        """Return {mod_name: state} for every known mod."""
        storage = self._storage()
        return {m: storage.states.get(m, "unknown") for m in storage.manifests}

    def enable(self, mod_name: str) -> tuple[bool, str]:
        """
        Enable a disabled mod.
        Runs the full on_load → on_init → on_ready sequence.
        Returns (True, success_msg) or (False, error_msg).
        """
        storage = self._storage()

        if mod_name not in storage.manifests:
            return False, (
                f"'{mod_name}' has no valid manifest. "
                "(Mod may have been rejected during startup.)"
            )
        if storage.states.get(mod_name) == "enable":
            return False, f"'{mod_name}' is already enabled."

        manifest = storage.manifests[mod_name]

        err = self._check_deps(mod_name, manifest, storage)
        if err:
            return False, err

        err = self._check_conflicts(mod_name, manifest, storage)
        if err:
            return False, err

        # Import & instantiate
        path = storage.paths.get(mod_name)
        if path is None:
            return False, f"No path on disk recorded for '{mod_name}'."
        entrypoint = path / manifest["entrypoint"]
        instance = self._loader.load(mod_name, entrypoint)
        if instance is None:
            return False, "Import or instantiation failed (check logs)."

        # on_load
        try:
            instance.on_load(self._core)
        except Exception as exc:
            return False, f"on_load raised: {exc}"

        # Commit to storage before on_init so that services registered in
        # on_load are already available to other mods queried during on_init.
        storage.instances[mod_name] = instance
        storage.states[mod_name] = "enable"
        if mod_name not in storage.load_order:
            storage.load_order.append(mod_name)

        # on_init
        try:
            instance.on_init(self._core)
        except Exception as exc:
            # Roll back: shutdown what was set up, then mark disabled.
            self._safe_shutdown(mod_name, instance, storage)
            return False, f"on_init raised: {exc}"

        # on_ready  — ENGINE_READY has already fired; call directly.
        try:
            instance.on_ready(self._synthetic_ready_event())
        except Exception as exc:
            self._log(WARNING, f"[mod_manager] on_ready error for '{mod_name}': {exc}")
            # on_ready failure keeps the mod enabled (matches engine policy).

        return True, f"'{mod_name}' enabled."

    def disable(self, mod_name: str) -> tuple[bool, str]:
        """
        Disable an active mod.
        Calls on_shutdown and removes all event subscriptions.
        Returns (True, success_msg) or (False, error_msg).
        """
        storage = self._storage()

        if mod_name == MOD_NAME:
            return False, "mod_manager cannot disable itself."
        if mod_name not in storage.manifests:
            return False, f"Unknown mod: '{mod_name}'."
        if storage.states.get(mod_name) != "enable":
            return False, f"'{mod_name}' is not currently enabled."

        manifest = storage.manifests[mod_name]
        if manifest.get("type") in _PROTECTED_TYPES:
            return False, (
                f"'{mod_name}' is a {manifest['type']} mod and cannot be disabled."
            )

        # Guard: other enabled mods that depend on this one.
        blockers = [
            other
            for other in storage.manifests
            if storage.states.get(other) == "enable"
            and other != mod_name
            and mod_name in storage.dependencies.get(other, [])
        ]
        if blockers:
            names = ", ".join(f"'{b}'" for b in sorted(blockers))
            return False, (
                f"Cannot disable: {names} "
                f"depend{'s' if len(blockers) == 1 else ''} on '{mod_name}'."
            )

        instance = storage.instances.get(mod_name)
        self._safe_shutdown(mod_name, instance, storage)
        return True, f"'{mod_name}' disabled."

    # ── internal ──────────────────────────────────────────────────────────

    def _storage(self):
        return self._core._mod_storage

    def _check_deps(self, mod_name: str, manifest: dict, storage) -> Optional[str]:
        for dep, constraint in manifest.get("requires", {}).items():
            if dep not in storage.manifests:
                return f"Missing dependency: '{dep}'."
            if storage.states.get(dep) != "enable":
                return f"Dependency '{dep}' is disabled."
            dep_version = storage.manifests[dep]["version"]
            if not ConstraintResolver.satisfies(dep_version, constraint):
                return (
                    f"Dependency '{dep}' v{dep_version} "
                    f"does not satisfy constraint {constraint}."
                )
        return None

    def _check_conflicts(self, mod_name: str, manifest: dict, storage) -> Optional[str]:
        our_version = manifest["version"]

        # Conflicts declared by the mod being enabled
        for target, constraint in manifest.get("conflicts", {}).items():
            if (
                target in storage.manifests
                and storage.states.get(target) == "enable"
                and ConstraintResolver.satisfies(
                    storage.manifests[target]["version"], constraint
                )
            ):
                return f"'{mod_name}' conflicts with enabled mod '{target}'."

        # Conflicts declared by already-enabled mods against this one
        for other, other_manifest in storage.manifests.items():
            if storage.states.get(other) != "enable":
                continue
            for conflict_target, constraint in other_manifest.get(
                "conflicts", {}
            ).items():
                if conflict_target == mod_name and ConstraintResolver.satisfies(
                    our_version, constraint
                ):
                    return f"Enabled mod '{other}' conflicts with '{mod_name}'."
        return None

    def _safe_shutdown(self, mod_name: str, instance, storage) -> None:
        """Call on_shutdown, remove handlers, and mark mod as disabled."""
        if instance is not None:
            try:
                instance.on_shutdown(self._core)
            except Exception as exc:
                self._log(
                    WARNING, f"[mod_manager] on_shutdown error for '{mod_name}': {exc}"
                )
            self._remove_handlers(instance, mod_name)

        storage.states[mod_name] = "disable"
        storage.instances[mod_name] = None

    def _remove_handlers(self, instance, mod_name: str) -> None:
        """
        Strip every event handler that belongs to this mod instance from the
        event bus.  Two criteria, either of which qualifies for removal:
          1. handler.mod_name == mod_name
          2. handler.func.__self__ is instance  (bound method on the instance)
        """
        bus = self._core.get_event_bus()
        for event_name in list(bus._events.keys()):
            bus._events[event_name] = [
                h
                for h in bus._events[event_name]
                if not (
                    h.mod_name == mod_name
                    or getattr(h.func, "__self__", None) is instance
                )
            ]

    @staticmethod
    def _synthetic_ready_event() -> dict:
        return {
            "name": "ENGINE_READY",
            "source": "core",
            "payload": {},
            "timestamp": int(time.time()),
        }


class _ModCommands:
    def __init__(self, svc: ModManagerService, display: ModDisplay, core):
        self._svc = svc
        self._display = display
        self._core = core

    def register_all(self) -> None:
        cmd = self._core.get_service("cmd_interface")
        if cmd is None:
            return

        _DIR = "mods"
        _DESC = "Mod lifecycle management."

        defs = [
            (
                "status",
                self._cmd_status,
                "List all mods and their current state.",
                f"{_DIR} status",
            ),
            (
                "enable",
                self._cmd_enable,
                "Enable a disabled mod.",
                f"{_DIR} enable <mod_name>",
            ),
            (
                "disable",
                self._cmd_disable,
                "Disable an active mod.",
                f"{_DIR} disable <mod_name>",
            ),
            (
                "info",
                self._cmd_info,
                "Show full details about a mod.",
                f"{_DIR} info <mod_name>",
            ),
        ]
        for name, cb, description, usage in defs:
            cmd.register(
                f"{_DIR}/{name}",
                cb,
                description=description,
                usage=usage,
                dir_description=_DESC,
            )

    # ── handlers ──────────────────────────────────────────────────────────

    def _cmd_status(self, _args) -> None:
        self._display.print_status(self._core._mod_storage)

    def _cmd_enable(self, args) -> None:
        if not args:
            self._display.err("Usage: mods enable <mod_name>")
            return
        ok, msg = self._svc.enable(args[0])
        (self._display.ok if ok else self._display.err)(msg)

    def _cmd_disable(self, args) -> None:
        if not args:
            self._display.err("Usage: mods disable <mod_name>")
            return
        ok, msg = self._svc.disable(args[0])
        (self._display.ok if ok else self._display.err)(msg)

    def _cmd_info(self, args) -> None:
        if not args:
            self._display.err("Usage: mods info <mod_name>")
            return
        self._display.print_info(args[0], self._core._mod_storage)


class Mod:
    MOD_NAME = "mod_manager"

    def on_load(self, core):
        self._core = core
        get_styled = lambda: core.get_service("styled_text")
        self._display = ModDisplay(get_styled)
        self._service = ModManagerService(core, core.log)
        self._cmds = _ModCommands(self._service, self._display, core)
        core.register_service("mod_manager", self._service)

    def on_init(self, core):
        self._cmds.register_all()

    def on_ready(self, event):
        pass

    def on_shutdown(self, core):
        pass
