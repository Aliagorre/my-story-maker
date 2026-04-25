# core/test.py

import asyncio
import tempfile
from pathlib import Path

from core.__manifest import (
    ManifestModule,
    ManifestProcessor,
    ManifestReader,
    ManifestValidator,
)
from core.__mod_storage import ModStorage
from core.__version import (
    ConstraintParser,
    ConstraintResolver,
    Version,
    VersionComparator,
)
from core.event_bus import EventBus
from core.service_registry import ServiceRegistry

# ============================
# Test ServiceRegistry 
# ============================

def mocks_log(type, message) -> None :
    print(f"[{type}] {message}")
def mocks_emit(event, payload) -> None : 
    print(f"[{event}] {payload}")

service_registry = ServiceRegistry(mocks_log, mocks_emit)

assert service_registry.register("test1", "instance1"), "test1.1 not pass : test1 must be registered"
assert service_registry.exists("test1")               , "test1.2 not pass : test1 must exist"
assert service_registry.get("test1") == "instance1"   , "test1.3 not pass : expect 'instance1'"

assert service_registry.register("test2", "instance2.1")    , "test2.1 not pass : test2 must be registered"
assert not service_registry.register("test2", "instance2.2"), "test2.2 not pass : duplicate must not be registered"
print("test2.3 : go see the logs")
print("test2.4 : go see the events")
assert service_registry.get("test2") == "instance2.1"       , "test2.5 not pass : duplicate must not shadow the first one"

assert service_registry.get("unknown") is None , "test3.1 not pass : expect nothing"
print("test3.2 : go see the logs")

assert service_registry.unregister("test1")      , "test4.1 not pass : test1 must be removed"
assert service_registry.unregister("test2")      , "test4.2 not pass : test2 must be removed"
assert not service_registry.unregister("unknown"), "test4.3 not pass : unknown should not exist"
print("test4.4 : go see the logs")

assert service_registry.register("test5_1", "instance5.1"), "test5.1 not pass : test5_1 must be registered"
assert service_registry.register("test5_2", "instance5.2"), "test5.2 not pass : test5_2 must be registered"
assert service_registry.register("test5_3", "instance5.3"), "test5.3 not pass : test5_3 must be registered"
print(service_registry.list_services())
assert service_registry.list_services() == ['test5_1', 'test5_2', 'test5_3'], "test5.1 not pass : bad list return"


assert not service_registry.register("Test6.1", "instance6"), "test6.1 not pass : test6.1 must not be register because of snake_case"
assert not service_registry.register("test6.2", None)       , "test6.2 not pass : test6.2 must not be register because of None instance"

# ============================
# Test EventBus 
# ============================

event_bus = EventBus(mocks_log, mocks_emit)
def subscribe7() : print("subscribe7")
assert event_bus.subscribe("MOD_ERROR", subscribe7), "test7.1 : subscribe7 must be subscribe"
print("test7.2 : go see the logs")

def subscribe8() : print("subscribe8")
assert not event_bus.subscribe("UNKNOWN", subscribe8), "test8.1 : subscribe8 must not be subscribe"
print("test8.2 : go see the logs")

assert event_bus.emit({"name":"MOD_ERROR","source":"test","payload":{},"timestamp": 0}),"test9.1 : must print subscribe7"

def subscribe10() : raise Exception("Intentional error")
assert event_bus.subscribe("MOD_ERROR", subscribe10), "test10.1 : subscribe10 must be subscribe"
assert event_bus.emit({"name":"MOD_ERROR","source":"test","payload":{},"timestamp": 0}),"test10.2 : must print subscribe7 and an error logged"
print("test10.3 : go see the events")

assert event_bus.unsubscribe("MOD_ERROR", subscribe10)   , "test 11.1 : subscribe10 must unsubscribe"
assert event_bus.unsubscribe("MOD_ERROR", subscribe7)    , "test 11.2 : subscribe7 must unsubscribe"
assert not event_bus.unsubscribe("MOD_ERROR", subscribe8), "test 11.3 : unknown handlers can't unsubscribe"
print("test11.4 : go see the logs")

async def async_handler(event):
    print("async handler OK")

event_bus.subscribe("MOD_ERROR", async_handler)

async def test_async():
    event = {"name":"MOD_ERROR","source":"test","payload":{},"timestamp":0}
    event_bus.emit(event)
    await asyncio.sleep(0.1)

asyncio.run(test_async())

# ============================
# Test ModStorage 
# ============================

mod_storage = ModStorage()

assert mod_storage.manifests == {}
assert mod_storage.states == {}
assert mod_storage.instances == {}
assert mod_storage.paths == {}
assert mod_storage.errors == {}
assert mod_storage.dependencies == {}
assert mod_storage.conflicts == {}
assert mod_storage.load_order == []

mod_storage.manifests["mod_test"] = {"name": "mod_test"}
mod_storage.states["mod_test"] = "enable"
mod_storage.instances["mod_test"] = object()
mod_storage.paths["mod_test"] = Path("mods/mod_test")
mod_storage.errors["mod_test"] = []
mod_storage.dependencies["mod_test"] = ["mod_core"]
mod_storage.conflicts["mod_test"] = []
mod_storage.load_order.append("mod_test")

assert mod_storage.manifests["mod_test"]["name"] == "mod_test"
assert mod_storage.states["mod_test"] == "enable"
assert isinstance(mod_storage.instances["mod_test"], object)
assert mod_storage.paths["mod_test"] == Path("mods/mod_test")
assert mod_storage.dependencies["mod_test"] == ["mod_core"]
assert mod_storage.load_order == ["mod_test"]
assert mod_storage.load_order == ["mod_test"]
assert mod_storage.load_order == ["mod_test"]

# ============================
# Version
# ============================

assert VersionComparator.compare(Version.parse("1.*.3"), Version.parse("1.4.3")) == 0
assert VersionComparator.compare(Version.parse("1.2.0"), Version.parse("1.3.0")) == -1

c1 = ConstraintParser.parse(">=1.2.0,<2.0.0")
assert ConstraintResolver.satisfies(Version.parse("1.5.3"), c1)
assert not ConstraintResolver.satisfies(Version.parse("2.0.0"), c1)

c2 = ConstraintParser.parse("*")
assert ConstraintResolver.satisfies(Version.parse("9.9.9"), c2)

c3 = ConstraintParser.parse("=1.*.*")
assert ConstraintResolver.satisfies(Version.parse("1.4.2"), c3)
assert not ConstraintResolver.satisfies(Version.parse("2.0.0"), c3)

c4 = ConstraintParser.parse("1.2.3")
assert ConstraintResolver.satisfies(Version.parse("1.2.3"), c4)
assert not ConstraintResolver.satisfies(Version.parse("1.2.4"), c4)


# ==========================
# Manifest
# ==========================

with tempfile.TemporaryDirectory() as tmp:
    tmp_dir = Path(tmp)

    # 1. ManifestReader

    mod_dir = tmp_dir / "mod_reader"
    mod_dir.mkdir()
    manifest_file = mod_dir / "manifest.json"
    manifest_file.write_text('{"name": "mod_test", "version": "1.0.0"}')
    result = ManifestReader.read(mod_dir)
    assert isinstance(result, dict)
    assert result["name"] == "mod_test"
    manifest_file.write_text("{ invalid json }")
    result = ManifestReader.read(mod_dir)
    assert result == {}
    manifest_file.write_text('["a"]')
    result = ManifestReader.read(mod_dir)
    assert result == {}

    # 2. ManifestValidator

    valid_dir = tmp_dir / "mod_valid"
    valid_dir.mkdir()
    (valid_dir / "main.py").write_text("")

    valid_manifest = {
        "name": "mod_valid",
        "version": "1.0.0",
        "entrypoint": "main.py",
        "type": "default",
        "priority": 1,
        "requires": {},
        "conflicts": {},
        "permissions": []
    }

    errors = ManifestValidator.validate(valid_manifest, valid_dir)
    assert errors == []

    errors = ManifestValidator.validate({}, valid_dir)
    assert "miss name" in errors
    assert "miss version" in errors
    assert "miss entrypoint" in errors
    assert "miss type" in errors
    assert "miss priority" in errors
    assert "miss requires " in errors
    assert "miss conflicts" in errors
    assert "miss permissions" in errors

    invalid_manifest = {
        "name": 123,
        "version": 1,
        "entrypoint": "main.py",
        "type": "unknown",
        "priority": "high",
        "requires": [],
        "conflicts": [],
        "permissions": {}
    }

    errors = ManifestValidator.validate(invalid_manifest, valid_dir)
    assert "name isn't str" in errors
    assert "version isn't str" in errors
    assert "unknown type don't exist" in errors
    assert "priority isn't int" in errors
    assert "requires isn't dict" in errors
    assert "conflicts isn't dict" in errors
    assert "permissions isn't list" in errors

    bad_manifest = valid_manifest.copy()
    bad_manifest["entrypoint"] = "missing.py"
    errors = ManifestValidator.validate(bad_manifest, valid_dir)
    assert any("don't exist" in e for e in errors)

    # 3. ManifestProcessor

    storage = ModStorage()

    ManifestProcessor.store("mod_a", valid_manifest, storage, [])
    assert storage.states["mod_a"] == "enable"
    ManifestProcessor.store("mod_b", valid_manifest, storage, ["error"])
    assert storage.states["mod_b"] == "disable"
    m = valid_manifest.copy()
    m["active"] = False
    ManifestProcessor.store("mod_c", m, storage, [])
    assert storage.states["mod_c"] == "disable"
    m["active"] = True
    ManifestProcessor.store("mod_d", m, storage, [])
    assert storage.states["mod_d"] == "enable"
    m["active"] = "off"
    ManifestProcessor.store("mod_e", m, storage, [])
    assert storage.states["mod_e"] == "disable"
    m["active"] = "random"
    ManifestProcessor.store("mod_f", m, storage, [])
    assert storage.states["mod_f"] == "enable"

    # 4. ManifestModule (integration)

    logs = []
    emitted = []
    storage = ModStorage()
    mod1 = tmp_dir / "mod1"
    mod1.mkdir()
    (mod1 / "main.py").write_text("")
    (mod1 / "manifest.json").write_text("""
    {
        "name": "mod_mod1",
        "version": "1.0.0",
        "entrypoint": "main.py",
        "type": "default",
        "priority": 1,
        "requires": {},
        "conflicts": {},
        "permissions": []
    }
    """)
    mod2 = tmp_dir / "mod2"
    mod2.mkdir()
    (mod2 / "manifest.json").write_text("{ invalid json }")
    storage.states["mod1"] = "discovered"
    storage.paths["mod1"] = mod1
    storage.states["mod2"] = "discovered"
    storage.paths["mod2"] = mod2
    module = ManifestModule(mocks_log, mocks_emit)
    module.run_manifest_pipeline(storage)

    assert storage.states["mod1"] == "enable"
    assert storage.states["mod2"] == "disable"
    assert "mod1" in storage.manifests
    assert len(emitted) >= 1

print("ALL TESTS PASSED")
