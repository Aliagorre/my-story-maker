# core/test.py

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
assert event_bus.subscribe("UNKNOWN", subscribe8), "test8.1 : subscribe8 must not be subscribe"
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
