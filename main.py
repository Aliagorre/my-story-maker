# main.py

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
        print()  # retour à la ligne propre
        pass  # Ctrl+C: suppress asyncio's re-raised KeyboardInterrupt
