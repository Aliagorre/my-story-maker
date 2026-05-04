# main.py

import asyncio
from pathlib import Path

from core.event_bus import EventBus
from core.mod_loader import ModLoader, ModStorage


async def main():
    """Boot the engine, run the command loop, then shut down cleanly."""
    event_bus = EventBus()
    mod_storage = ModStorage()
    loader = ModLoader(Path(__file__).parent / "mods", event_bus, mod_storage)
    await loader.load_all()

    # Register and wire reload events — must happen after load_all()
    # so the loop is running and asyncio.create_task() is available.
    event_bus.register("RELOAD_MOD")
    event_bus.register("RELOAD_ALL")

    def handle_reload_mod(event):
        """Schedule an async single-mod reload without blocking the event bus."""
        name = event["payload"]["name"]
        asyncio.create_task(loader.reload_mod(name))

    def handle_reload_all(event):
        """Schedule an async full reload without blocking the event bus."""

        async def _reload_all():
            await loader.shutdown_all()
            await loader.load_all()

        asyncio.create_task(_reload_all())

    event_bus.subscribe("RELOAD_MOD", handle_reload_mod)
    event_bus.subscribe("RELOAD_ALL", handle_reload_all)

    event_bus.emit(
        {
            "name": "ENGINE_READY",
            "payload": {},
            "source": "core_engine",
            "timestamp": 0,
        }
    )
    while True:
        try:
            line = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if line.strip():
            event_bus.emit(
                {
                    "name": "COMMAND_INPUT",
                    "payload": {"raw": line},
                    "source": "core_engine",
                    "timestamp": 0,
                }
            )
    await loader.shutdown_all()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Ctrl+C: suppress asyncio's re-raised KeyboardInterrupt
