# core/test.py

import asyncio
import shutil
import tempfile
from pathlib import Path

from core.__dependency import DependencyModule
from core.__dynamic_loader import DynamicLoader
from core.__lifecycle import InitExecutor, ReadyExecutor, ShutdownExecutor
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

# =========================
# Dependency
# =========================


def make_mod(name, version, requires=None, conflicts=None, priority=0):
    return {
        "name": name,
        "version": Version.parse(version),
        "requires": {
            k: ConstraintParser.parse(v)
            for k, v in (requires or {}).items()
        },
        "conflicts": {
            k: ConstraintParser.parse(v)
            for k, v in (conflicts or {}).items()
        },
        "priority": priority
    }

#  DEPENDENCY OK

storage = ModStorage()
storage.manifests = {
    "A": make_mod("A", "1.0.0", {"B": "*"}),
    "B": make_mod("B", "1.0.0")}
storage.states = {"A": "enable","B": "enable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
assert storage.states["A"] == "enable"
assert storage.states["B"] == "enable"
assert "A" in storage.load_order
assert "B" in storage.load_order

# MISSING DEPENDENCY

errors.clear()
storage = ModStorage()
storage.manifests = {"A": make_mod("A", "1.0.0", {"B": "*"})}
storage.states = {"A": "enable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
assert storage.states["A"] == "disable"
assert any(e[0] == "MOD_DEPENDENCY_ERROR" for e in errors)

# DISABLED DEPENDENCY

errors.clear()
storage = ModStorage()
storage.manifests = {
    "A": make_mod("A", "1.0.0", {"B": "*"}),
    "B": make_mod("B", "1.0.0")}
storage.states = {"A": "enable","B": "disable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
assert storage.states["A"] == "disable"

# VERSION INCOMPATIBLE

errors.clear()
storage = ModStorage()
storage.manifests = {
    "A": make_mod("A", "1.0.0", {"B": ">=2.0.0"}),
    "B": make_mod("B", "1.0.0")}
storage.states = {"A": "enable","B": "enable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
assert storage.states["A"] == "disable"

# CONFLICT

errors.clear()
storage = ModStorage()
storage.manifests = {
    "A": make_mod("A", "1.0.0", conflicts={"B": "*"}),
    "B": make_mod("B", "1.0.0")}
storage.states = {"A": "enable","B": "enable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
assert storage.states["A"] == "disable"
assert any(e[0] == "MOD_CONFLICT" for e in errors)

#  CYCLE DETECTION

errors.clear()
storage = ModStorage()
storage.manifests = {
    "A": make_mod("A", "1.0.0", {"B": "*"}),
    "B": make_mod("B", "1.0.0", {"A": "*"})}
storage.states = {"A": "enable","B": "enable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
assert storage.states["A"] == "disable"
assert storage.states["B"] == "disable"

#  TOPO ORDER

storage = ModStorage()
storage.manifests = {
    "A": make_mod("A", "1.0.0", {"B": "*"}),
    "B": make_mod("B", "1.0.0", {"C": "*"}),
    "C": make_mod("C", "1.0.0")
}
storage.states = {"A": "enable","B": "enable","C": "enable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
order = storage.load_order
assert order.index("C") < order.index("B")
assert order.index("B") < order.index("A")

#  PRIORITY (SANS CASSER TOPO)

storage = ModStorage()
storage.manifests = {
    "A": make_mod("A", "1.0.0", {"B": "*"}, priority=10),
    "B": make_mod("B", "1.0.0", priority=0)}
storage.states = {"A": "enable","B": "enable"}
DependencyModule(mocks_log, mocks_emit).run(storage)
order = storage.load_order
# B doit rester avant A (dépendance)
assert order.index("B") < order.index("A")


# =========================
# DUMMY CORE + STORAGE
# =========================

class DummyCore:
    def __init__(self):
        self.events = []

    def emit(self, event, payload):
        self.events.append((event, payload))

    def subscribe(self, *args, **kwargs):
        pass

    def register_service(self, *args, **kwargs):
        pass

    def get_service(self, *args, **kwargs):
        return None

    def get_manifest(self, *args, **kwargs):
        return None

    def log(self, *args, **kwargs):
        pass

logs = []
errors = []
events = []

def log(level, msg):
    logs.append((level, msg))

def emit_error(event, payload):
    errors.append((event, payload))

def emit(event, payload):
    events.append((event, payload))

def write_mod(tmpdir, name, code):
    mod_dir = tmpdir / name
    mod_dir.mkdir()
    file = mod_dir / "main.py"
    file.write_text(code)
    return mod_dir

def make_manifest():
    return {
        "entrypoint": "main.py",
        "version": Version.parse("1.0.0")
    }

tmp = Path(tempfile.mkdtemp())

try:

    # 1. SUCCESS LOAD

    storage = ModStorage()
    core = DummyCore()
    code = """
class Mod:
    def on_load(self, core): pass
    def on_init(self): pass
    def on_ready(self): pass
    def on_shutdown(self): pass
"""
    path = write_mod(tmp, "mod_ok", code)
    storage.paths["mod_ok"] = path
    storage.manifests["mod_ok"] = make_manifest()
    storage.states["mod_ok"] = "enable"
    storage.load_order = ["mod_ok"]
    DynamicLoader(core, log, emit_error, emit).run_dynamic_loading(storage)
    assert storage.instances["mod_ok"] is not None
    assert any(e[0] == "MOD_LOADED" for e in events)

    # 2. ENTRYPOINT MISSING

    storage = ModStorage()
    events.clear()
    storage.paths["mod_bad"] = tmp
    storage.manifests["mod_bad"] = {"entrypoint": "missing.py", "version": Version.parse("1.0.0")}
    storage.states["mod_bad"] = "enable"
    storage.load_order = ["mod_bad"]
    DynamicLoader(core, log, emit_error, emit).run_dynamic_loading(storage)
    assert storage.states["mod_bad"] == "disable"
    assert storage.instances.get("mod_bad") is None

    # 3. INVALID CLASS NAME

    storage = ModStorage()
    code = """
class NotMod:
    pass
"""
    path = write_mod(tmp, "mod_noclass", code)
    storage.paths["mod_noclass"] = path
    storage.manifests["mod_noclass"] = make_manifest()
    storage.states["mod_noclass"] = "enable"
    storage.load_order = ["mod_noclass"]
    DynamicLoader(core, log, emit_error, emit).run_dynamic_loading(storage)
    assert storage.states["mod_noclass"] == "disable"

    # 4. BAD CONSTRUCTOR

    storage = ModStorage()
    code = """
class Mod:
    def __init__(self, x): pass
    def on_load(self, core): pass
    def on_init(self): pass
    def on_ready(self): pass
    def on_shutdown(self): pass
"""
    path = write_mod(tmp, "mod_ctor", code)
    storage.paths["mod_ctor"] = path
    storage.manifests["mod_ctor"] = make_manifest()
    storage.states["mod_ctor"] = "enable"
    storage.load_order = ["mod_ctor"]
    DynamicLoader(core, log, emit_error, emit).run_dynamic_loading(storage)
    assert storage.states["mod_ctor"] == "disable"

    # 5. MISSING HOOK

    storage = ModStorage()
    code = """
class Mod:
    def on_load(self, core): pass
"""
    path = write_mod(tmp, "mod_hook", code)
    storage.paths["mod_hook"] = path
    storage.manifests["mod_hook"] = make_manifest()
    storage.states["mod_hook"] = "enable"
    storage.load_order = ["mod_hook"]
    DynamicLoader(core, log, emit_error, emit).run_dynamic_loading(storage)
    assert storage.states["mod_hook"] == "disable"

    # 6. on_load EXCEPTION

    storage = ModStorage()

    code = """
class Mod:
    def on_load(self, core): raise Exception("fail")
    def on_init(self): pass
    def on_ready(self): pass
    def on_shutdown(self): pass
"""
    path = write_mod(tmp, "mod_crash", code)
    storage.paths["mod_crash"] = path
    storage.manifests["mod_crash"] = make_manifest()
    storage.states["mod_crash"] = "enable"
    storage.load_order = ["mod_crash"]
    DynamicLoader(core, log, emit_error, emit).run_dynamic_loading(storage)
    assert storage.states["mod_crash"] == "disable"

    # 7. MULTI MOD LOAD ORDER

    storage = ModStorage()
    events.clear()
    code = """
class Mod:
    def on_load(self, core): pass
    def on_init(self): pass
    def on_ready(self): pass
    def on_shutdown(self): pass
"""
    path1 = write_mod(tmp, "mod1", code)
    path2 = write_mod(tmp, "mod2", code)
    storage.paths["mod1"] = path1
    storage.paths["mod2"] = path2
    storage.manifests["mod1"] = make_manifest()
    storage.manifests["mod2"] = make_manifest()
    storage.states["mod1"] = "enable"
    storage.states["mod2"] = "enable"
    storage.load_order = ["mod1", "mod2"]
    DynamicLoader(core, log, emit_error, emit).run_dynamic_loading(storage)
    assert storage.instances["mod1"] is not None
    assert storage.instances["mod2"] is not None
    loaded = [e[1]["mod"] for e in events if e[0] == "MOD_LOADED"]
    assert loaded == ["mod1", "mod2"]
finally:
    shutil.rmtree(tmp)

# =========================
# DUMMY CORE + STORAGE
# =========================

logs = []
errors = []
events = []

# DUMMY MODS
class GoodMod:
    def __init__(self):
        self.init_called = False
        self.shutdown_called = False
    def on_load(self, core): pass
    def on_init(self, core):
        self.init_called = True
    def on_ready(self): pass
    def on_shutdown(self, core):
        self.shutdown_called = True

class CrashInitMod(GoodMod):
    def on_init(self, core):
        raise Exception("init fail")
class CrashShutdownMod(GoodMod):
    def on_shutdown(self, core):
        raise Exception("shutdown fail")

# 1. INIT SUCCESS

storage = ModStorage()
core = DummyCore()
mod = GoodMod()
storage.instances["A"] = mod
storage.states["A"] = "enable"
storage.errors["A"] = []
storage.load_order = ["A"]
InitExecutor(core, log, emit_error, emit).run_on_init(storage)
assert mod.init_called is True
assert any(e[0] == "MOD_INITIALIZED" for e in events)

# 2. INIT FAILURE

errors.clear()
events.clear()
storage = ModStorage()
mod = CrashInitMod()
storage.instances["A"] = mod
storage.states["A"] = "enable"
storage.errors["A"] = []
storage.load_order = ["A"]
InitExecutor(core, log, emit_error, emit).run_on_init(storage)
assert storage.states["A"] == "disable"
assert storage.instances["A"] is None
assert any(e[0] == "MOD_ERROR" for e in errors)
assert "on_init failed" in storage.errors["A"]

# 3. SKIP NONE INSTANCE

storage = ModStorage()
storage.instances["A"] = None
storage.states["A"] = "enable"
storage.errors["A"] = []
storage.load_order = ["A"]
InitExecutor(core, log, emit_error, emit).run_on_init(storage)
# rien ne doit se passer
assert True

# 4. ENGINE_READY EVENT

events.clear()
ReadyExecutor.run_on_ready(emit)
assert any(e[0] == "ENGINE_READY" for e in events)

# 5. SHUTDOWN SUCCESS

storage = ModStorage()
mod = GoodMod()
storage.instances["A"] = mod
storage.states["A"] = "enable"
storage.load_order = ["A"]
ShutdownExecutor(core, log).run_on_shutdown(storage)
assert mod.shutdown_called is True

# 6. SHUTDOWN FAILURE (NO CRASH)

logs.clear()
storage = ModStorage()
mod = CrashShutdownMod()
storage.instances["A"] = mod
storage.states["A"] = "enable"
storage.load_order = ["A"]
ShutdownExecutor(core, log).run_on_shutdown(storage)
# ne doit pas planter
assert True

# 7. SHUTDOWN ORDER (REVERSED)

order = []
class TrackMod(GoodMod):
    def __init__(self, name):
        self.name = name

    def on_shutdown(self, core):
        order.append(self.name)

storage = ModStorage()
storage.instances["A"] = TrackMod("A")
storage.instances["B"] = TrackMod("B")
storage.states["A"] = "enable"
storage.states["B"] = "enable"
storage.load_order = ["A", "B"]
ShutdownExecutor(core, log).run_on_shutdown(storage)
assert order == ["B", "A"]

# 8. DISABLED MOD SKIPPED

order.clear()
storage = ModStorage()
storage.instances["A"] = TrackMod("A")
storage.instances["B"] = TrackMod("B")
storage.states["A"] = "disable"
storage.states["B"] = "enable"
storage.load_order = ["A", "B"]
ShutdownExecutor(core, log).run_on_shutdown(storage)
assert order == ["B"]

print("ALL TESTS PASSED")
