# main.py 

import time

from core.core_api import CoreAPI
from core.event_bus import EventBus
from core.mod_loader import ModLoader
from core.service_registry import ServiceRegistry
from EVENTS import ENGINE_TICK, LOG_EVENT

event_bus = EventBus(
    log=lambda name, message: event_bus.emit({
        "name": LOG_EVENT,
        "source": "core",
        "payload": {"type":name,"message":message},
        "timestamp": int(time.time())
    }), 
    emit_error=lambda e, p: event_bus.emit({
    "name": e,
    "source": "core",
    "payload": p,
    "timestamp": int(time.time())
}))

service_registry = ServiceRegistry(
    log=lambda name, message: event_bus.emit({
        "name": LOG_EVENT,
        "source": "core",
        "payload": {"type":name,"message":message},
        "timestamp": int(time.time())
    }), 
    emit_error=lambda e, p: event_bus.emit({
    "name": e,
    "source": "core",
    "payload": p,
    "timestamp": int(time.time())
}))

core = CoreAPI(
    event_bus=event_bus,
    service_registry=service_registry,
    mod_storage=None,  
    log=lambda name, message: event_bus.emit({
        "name": LOG_EVENT,
        "source": "core",
        "payload": {"type":name,"message":message},
        "timestamp": int(time.time())
    })
)

mod_loader = ModLoader(
    core=core,
    log=lambda name, message: event_bus.emit({
        "name": LOG_EVENT,
        "source": "core",
        "payload": {"type":name,"message":message},
        "timestamp": int(time.time())
    }),
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

