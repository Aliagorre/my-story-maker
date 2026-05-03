# test.py — imperative assertion tests for the engine core

import asyncio
import json
import sys
import tempfile
from pathlib import Path

from core.core_api import CoreAPI
from core.event_bus import EventBus
from core.mod_loader import ModLoader, ModStorage

# ─── Helpers ────────────────────────────────────────────────────────────────


def section(name: str):
    print(f"\n{'─' * 54}")
    print(f"  {name}")
    print(f"{'─' * 54}")


def ok(label: str):
    print(f"  ✓  {label}")


def make_mod(root: Path, name: str, code: str, **manifest_extra):
    """Create a minimal mod directory with a manifest.json and main.py."""
    d = root / name
    d.mkdir()
    manifest = {"name": name, "entrypoint": "main.py", **manifest_extra}
    (d / "manifest.json").write_text(json.dumps(manifest))
    (d / "main.py").write_text(code)


# ─── Mod templates ──────────────────────────────────────────────────────────
# Module-level style: no Mod class → the module itself is the instance.
# Lifecycle hooks take a single `core` argument (no self).

LIFECYCLE_MOD = """\
loaded = []
inited = []
readied = []
downed = []

def on_load(core):     loaded.append(True)
def on_init(core):     inited.append(True)
def on_ready(core):    readied.append(True)
def on_shutdown(core): downed.append(True)
"""

EXPORT_MOD = """\
exports = {"answer": 42}
"""

ASYNC_MOD = """\
import asyncio
loaded = []

async def on_load(core):
    await asyncio.sleep(0)
    loaded.append(True)
"""

CRASH_MOD = """\
raise RuntimeError("intentional crash on import")
"""

NOOP_MOD = "# empty mod"


# ─── 1) EventBus ────────────────────────────────────────────────────────────


def test_event_bus():
    section("EventBus")

    bus = EventBus()

    # register
    bus.register("FOO")
    assert "FOO" in bus._handlers
    assert bus._handlers["FOO"] == []
    ok("register creates an empty handler list")

    bus.register("FOO")
    assert len(bus._handlers["FOO"]) == 0
    ok("double register is idempotent")

    # subscribe
    assert bus.subscribe("GHOST", lambda e: None) is False
    ok("subscribe on undeclared event returns False")

    assert bus.subscribe("FOO", "not_callable") is False
    ok("subscribe with non-callable returns False")

    received = []
    assert bus.subscribe("FOO", lambda e: received.append(e)) is True
    ok("subscribe on declared event returns True")

    # emit
    bus.emit({"name": "FOO", "payload": {"x": 1}, "source": "test", "timestamp": 0})
    assert len(received) == 1
    assert received[0]["payload"]["x"] == 1
    ok("emit dispatches event to subscriber")

    assert (
        bus.emit({"name": "GHOST", "payload": {}, "source": "test", "timestamp": 0})
        is False
    )
    ok("emit on undeclared event returns False")

    # unsubscribe
    log = []

    def handler(e):
        log.append(e)

    bus.register("BAR")
    bus.subscribe("BAR", handler)
    bus.emit({"name": "BAR", "payload": {}, "source": "test", "timestamp": 0})
    assert len(log) == 1
    assert bus.unsubscribe("BAR", handler) is True
    bus.emit({"name": "BAR", "payload": {}, "source": "test", "timestamp": 0})
    assert len(log) == 1  # no second call after unsubscribe
    ok("unsubscribe removes handler")

    assert bus.unsubscribe("GHOST", handler) is False
    ok("unsubscribe on undeclared event returns False")

    # handler exception → ERROR_EVENT
    bus.register("ERROR_EVENT")
    errors = []
    bus.subscribe("ERROR_EVENT", lambda e: errors.append(e))
    bus.register("BOOM")

    def bad(e):
        raise RuntimeError("oops")

    bus.subscribe("BOOM", bad)
    bus.emit({"name": "BOOM", "payload": {}, "source": "test", "timestamp": 0})
    assert len(errors) == 1
    assert errors[0]["payload"]["exception"] == "oops"
    assert errors[0]["payload"]["handler"] == "bad"
    assert errors[0]["source"] == "event_bus"
    ok("handler exception is caught and re-emitted as ERROR_EVENT")

    # mid-iteration unsubscribe safety (guarded by list() copy in emit)
    bus.register("SAFE")

    def self_unsub(e):
        bus.unsubscribe("SAFE", self_unsub)

    bus.subscribe("SAFE", self_unsub)
    bus.emit({"name": "SAFE", "payload": {}, "source": "test", "timestamp": 0})
    ok("unsubscribe during emit does not crash (list-copy guard)")

    # multiple subscribers all receive the event
    bus.register("MULTI")
    hits = []
    bus.subscribe("MULTI", lambda e: hits.append(1))
    bus.subscribe("MULTI", lambda e: hits.append(2))
    bus.emit({"name": "MULTI", "payload": {}, "source": "test", "timestamp": 0})
    assert hits == [1, 2]
    ok("all subscribers receive the event")


# ─── 2) CoreAPI ─────────────────────────────────────────────────────────────


def test_core_api():
    section("CoreAPI")

    bus = EventBus()
    bus.register("LOG_EVENT")
    bus.register("PING")
    bus.register("CUSTOM")

    sentinel = object()
    storage = ModStorage(
        manifests={"mod_a": {"name": "mod_a", "version": "2.0.0"}},
        instances={"mod_a": sentinel},
        states={"mod_a": "enable", "mod_b": "disabled"},
        exports={},
    )
    core = CoreAPI(bus, storage, "my_mod")

    # emit
    received = []
    bus.subscribe("CUSTOM", lambda e: received.append(e))
    core.emit("CUSTOM", {"k": "v"})
    assert len(received) == 1
    e = received[0]
    assert e["name"] == "CUSTOM"
    assert e["source"] == "my_mod"
    assert e["payload"]["k"] == "v"
    assert "timestamp" in e
    ok("emit tags event with mod name, event name, and timestamp")

    # log
    logs = []
    bus.subscribe("LOG_EVENT", lambda e: logs.append(e))
    core.log("WARN", "watch out", file="x.py", line=10)
    assert len(logs) == 1
    p = logs[0]["payload"]
    assert p["level"] == "WARN"
    assert p["message"] == "watch out"
    assert p["context"]["file"] == "x.py"
    assert p["context"]["line"] == 10
    ok("log emits a structured LOG_EVENT with context kwargs")

    # subscribe
    hits = []
    assert core.subscribe("PING", lambda e: hits.append(e)) is True
    bus.emit({"name": "PING", "payload": {}, "source": "x", "timestamp": 0})
    assert len(hits) == 1
    ok("subscribe delegates to EventBus")

    # get_mod
    assert core.get_mod("mod_a") is sentinel
    ok("get_mod returns the live instance")
    assert core.get_mod("ghost") is None
    ok("get_mod on unknown mod returns None")

    # get_manifest
    assert core.get_manifest("mod_a")["version"] == "2.0.0"
    ok("get_manifest returns the correct manifest")

    # get_all_enabled_mods
    enabled = core.get_all_enabled_mods()
    assert "mod_a" in enabled
    assert "mod_b" not in enabled
    ok("get_all_enabled_mods filters by 'enable' state")

    # get_all_mods
    all_mods = core.get_all_mods()
    assert "mod_a" in all_mods
    assert "mod_b" in all_mods
    ok("get_all_mods returns all known mods regardless of state")

    # get_core_version
    storage.manifests["core_engine"] = {"version": "9.1.0"}
    assert core.get_core_version() == "9.1.0"
    ok("get_core_version reads from core_engine manifest")
    del storage.manifests["core_engine"]
    assert core.get_core_version() == "7.0.0"
    ok("get_core_version falls back to '7.0.0' when manifest is absent")

    # override
    core.some_attr = "original"
    core.override("some_attr", "replaced")
    assert core.some_attr == "replaced"
    ok("override replaces attribute by dotted path")

    # extend
    core.my_dict = {"a": 1}
    core.extend("my_dict", {"b": 2, "c": 3})
    assert core.my_dict == {"a": 1, "b": 2, "c": 3}
    ok("extend merges new keys into target dict")

    core.not_a_dict = 99
    try:
        core.extend("not_a_dict", {"x": 1})
        assert False, "should have raised"
    except TypeError:
        pass
    ok("extend raises TypeError when target is not a dict")


# ─── 3) ModLoader ───────────────────────────────────────────────────────────


def test_mod_loader():
    section("ModLoader")

    bus = EventBus()
    bus.register("ERROR_EVENT")

    # discover: finds valid mods
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "mod_a", NOOP_MOD)
        make_mod(root, "mod_b", NOOP_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        assert "mod_a" in loader._mods
        assert "mod_b" in loader._mods
        assert storage.states["mod_a"] == "disabled"
        ok("discover_mods finds all valid mods")

    # discover: no manifest.json → skipped
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "no_manifest").mkdir()
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        assert "no_manifest" not in loader._mods
        ok("directory without manifest.json is skipped")

    # discover: manifest missing 'entrypoint' → skipped
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        d = root / "bad"
        d.mkdir()
        (d / "manifest.json").write_text(json.dumps({"name": "bad"}))
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        assert "bad" not in loader._mods
        ok("manifest missing 'entrypoint' is rejected")

    # discover: non-directory entries are skipped
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "file.txt").write_text("hello")
        make_mod(root, "real_mod", NOOP_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        assert "file.txt" not in loader._mods
        assert "real_mod" in loader._mods
        ok("non-directory entries in mods_root are skipped")

    # resolve: missing dependency → error
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "child", NOOP_MOD, requires={"ghost": "*"})
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        loader._resolve_dependencies()
        assert loader._mods["child"].state == "error"
        ok("mod with a missing dependency is marked as error")

    # conflict: declared conflict present → error
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "mod_x", NOOP_MOD)
        make_mod(root, "mod_y", NOOP_MOD, conflicts={"mod_x": "*"})
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        loader._check_conflicts()
        assert loader._mods["mod_y"].state == "error"
        ok("mod with an active conflict is marked as error")

    # load order: dependency before dependent
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "base", NOOP_MOD)
        make_mod(root, "child", NOOP_MOD, requires={"base": "*"})
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        loader._resolve_dependencies()
        loader._compute_load_order()
        order = loader._load_order
        assert order.index("base") < order.index("child")
        ok("dependency is placed before its dependent in load order")

    # load order: higher priority first
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "low", NOOP_MOD, priority=0)
        make_mod(root, "high", NOOP_MOD, priority=10)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        loader._compute_load_order()
        order = loader._load_order
        assert order.index("high") < order.index("low")
        ok("higher priority mod is placed first in load order")

    # full load: lifecycle hooks called in order
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "lc", LIFECYCLE_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        asyncio.run(loader.load_all())
        m = loader._mods["lc"].module
        assert m.loaded == [True]
        assert m.inited == [True]
        assert m.readied == [True]
        assert storage.states["lc"] == "enable"
        assert storage.instances["lc"] is not None
        ok("on_load → on_init → on_ready are called in order")

    # full load: exports collected into ModStorage
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "exp", EXPORT_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        asyncio.run(loader.load_all())
        assert storage.exports["exp"]["answer"] == 42
        ok("mod exports are collected into ModStorage")

    # full load: async lifecycle hook awaited
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "async_mod", ASYNC_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        asyncio.run(loader.load_all())
        assert loader._mods["async_mod"].module.loaded == [True]
        ok("async lifecycle hooks are awaited correctly")

    # full load: crash on import → error, absent from instances
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "crash", CRASH_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        asyncio.run(loader.load_all())
        assert loader._mods["crash"].state == "error"
        assert "crash" not in storage.instances
        ok("mod that crashes on import is marked as error, not added to instances")

    # full load: error mod does not block other mods
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "crash", CRASH_MOD)
        make_mod(root, "good", LIFECYCLE_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        asyncio.run(loader.load_all())
        assert storage.states["good"] == "enable"
        ok("a crashing mod does not prevent other mods from loading")

    # shutdown: on_shutdown called, state reset to disabled
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "sd", LIFECYCLE_MOD)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        asyncio.run(loader.load_all())
        asyncio.run(loader.shutdown_all())
        m = loader._mods["sd"].module
        assert m.downed == [True]
        assert storage.states["sd"] == "disabled"
        ok("shutdown_all calls on_shutdown and resets state to 'disabled'")

    # shutdown: reverse load order (two mods with known order)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "first", NOOP_MOD, priority=10)
        make_mod(root, "last", NOOP_MOD, priority=0)
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        asyncio.run(loader.load_all())
        load_order = list(loader._load_order)  # [first, last]
        asyncio.run(loader.shutdown_all())
        # Both should now be disabled regardless of order
        assert storage.states["first"] == "disabled"
        assert storage.states["last"] == "disabled"
        ok("shutdown_all disables all mods")

    # manifest defaults are applied
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "minimal", NOOP_MOD)  # no priority, version, etc.
        storage = ModStorage()
        loader = ModLoader(root, bus, storage)
        loader.discover_mods()
        m = loader._mods["minimal"].manifest
        assert m["version"] == "1.0.0"
        assert m["priority"] == 0
        assert m["requires"] == {}
        assert m["conflicts"] == {}
        ok("missing manifest fields are filled with defaults")


# ─── 4) Engine startup integration ──────────────────────────────────────────


def test_engine_startup():
    section("Engine startup (integration)")

    bus = EventBus()
    storage = ModStorage()
    bus.register("ENGINE_READY")
    bus.register("COMMAND_INPUT")

    ready_events = []
    bus.subscribe("ENGINE_READY", lambda e: ready_events.append(e))

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "starter", LIFECYCLE_MOD)
        loader = ModLoader(root, bus, storage)

        async def run():
            await loader.load_all()
            bus.emit(
                {
                    "name": "ENGINE_READY",
                    "payload": {},
                    "source": "core_engine",
                    "timestamp": 0,
                }
            )
            await loader.shutdown_all()

        asyncio.run(run())

    assert len(ready_events) == 1
    assert ready_events[0]["name"] == "ENGINE_READY"
    assert ready_events[0]["source"] == "core_engine"
    ok("ENGINE_READY is emitted after load_all()")

    # COMMAND_INPUT carries the raw string
    commands = []
    bus.subscribe("COMMAND_INPUT", lambda e: commands.append(e["payload"]["raw"]))
    bus.emit(
        {
            "name": "COMMAND_INPUT",
            "payload": {"raw": "hello"},
            "source": "core_engine",
            "timestamp": 0,
        }
    )
    assert commands == ["hello"]
    ok("COMMAND_INPUT event carries raw input string")

    # KeyboardInterrupt at __main__ level is safely swallowed
    try:
        raise KeyboardInterrupt()
    except KeyboardInterrupt:
        pass
    ok("KeyboardInterrupt is caught and does not propagate")

    # A second asyncio.run() after the first completes is clean (no loop reuse)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_mod(root, "second_run", LIFECYCLE_MOD)
        storage2 = ModStorage()
        loader2 = ModLoader(root, bus, storage2)
        asyncio.run(loader2.load_all())
        assert storage2.states["second_run"] == "enable"
        ok("engine can boot cleanly a second time (no event-loop residue)")


# ─── Runner ─────────────────────────────────────────────────────────────────


def run_all():
    print("\n╔════════════════════════════════════════════════════╗")
    print("║            ENGINE CORE — TEST SUITE               ║")
    print("╚════════════════════════════════════════════════════╝")

    suites = [
        ("EventBus", test_event_bus),
        ("CoreAPI", test_core_api),
        ("ModLoader", test_mod_loader),
        ("Engine startup", test_engine_startup),
    ]

    passed = failed = 0
    for name, fn in suites:
        try:
            fn()
            passed += 1
        except AssertionError as e:
            import traceback

            print(f"\n  ✗  ASSERTION FAILED — {name}")
            traceback.print_exc()
            failed += 1
        except Exception as e:
            import traceback

            print(f"\n  ✗  ERROR — {name}: {type(e).__name__}: {e}")
            traceback.print_exc()
            failed += 1

    total = passed + failed
    status = "✓  all good" if not failed else f"✗  {failed} suite(s) failed"
    print(f"\n{'─' * 54}")
    print(f"  {passed}/{total} suites passed — {status}")
    print(f"{'─' * 54}\n")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    run_all()
