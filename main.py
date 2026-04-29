# main.py — Point d’entrée StoryMaker V7

import time

from core.core_api import CoreAPI
from core.event_bus import EventBus
from core.mod_loader import ModLoader
from core.service_registry import ServiceRegistry
from EVENTS import ENGINE_TICK
from LOG_LEVELS import INFO


def logger(level, message):
    now = time.strftime("%H:%M:%S")
    print(f"[{level}] [{now}] [core] {message}")

event_bus = EventBus(log=logger, emit_error=lambda e, p: event_bus.emit({
    "name": e,
    "source": "core",
    "payload": p,
    "timestamp": int(time.time())
}))

service_registry = ServiceRegistry(log=logger, emit_error=lambda e, p: event_bus.emit({
    "name": e,
    "source": "core",
    "payload": p,
    "timestamp": int(time.time())
}))

core = CoreAPI(
    event_bus=event_bus,
    service_registry=service_registry,
    mod_storage=None,  # sera injecté par ModLoader
    log=logger
)

mod_loader = ModLoader(
    core=core,
    log=logger,
    emit=lambda name, payload: event_bus.emit({
        "name": name,
        "source": "core",
        "payload": payload,
        "timestamp": int(time.time())
    }),
    emit_error=lambda e, p: event_bus.emit({
        "name": e,
        "source": "core",
        "payload": p,
        "timestamp": int(time.time())
    })
)

# Injection du mod_storage dans CoreAPI
core._mod_storage = mod_loader.mod_storage

mod_loader.load_all()


while True:
    event_bus.emit({
        "name": ENGINE_TICK,
        "source": "core",
        "payload": {},
        "timestamp": int(time.time())
    })
    time.sleep(0.1)

