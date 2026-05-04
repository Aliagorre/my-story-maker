# mods/mod_cmd/main.py

commands: dict = {}  # name → {"callback": fn, "description": str, "source": mod_name}
_core = None  # stored at on_load so bare command functions can emit events


def on_load(core):
    """Subscribe to command registration and input, then register built-ins."""
    global _core
    _core = core
    core.subscribe("REGISTER_COMMAND", register_command)
    core.subscribe("COMMAND_INPUT", execute_command)
    _register_builtin("help", "Show available commands", cmd_help)
    _register_builtin("clear", "Clear the screen", cmd_clear)
    _register_builtin("quit", "Quit the engine", cmd_quit)
    _register_builtin("reload", "reload [mod]  Reload one mod or all mods", cmd_reload)
    core.log("INFO", "[mod_cmd] loaded")


def on_ready(core):
    core.log("INFO", "[mod_cmd] ready")


# --- Registration ---


def register_command(event):
    """
    Handle a REGISTER_COMMAND event from any mod.
    Expected payload: {name: str, callback: callable, description?: str}
    Other mods use this because they cannot import mod_cmd directly —
    the event bus is the only inter-mod communication channel.
    """
    payload = event["payload"]
    commands[payload["name"]] = {
        "callback": payload["callback"],
        "description": payload.get("description", ""),
        "source": event["source"],
    }


def _register_builtin(name: str, description: str, callback):
    """Register a built-in command directly, without going through the event bus."""
    commands[name] = {
        "callback": callback,
        "description": description,
        "source": "mod_cmd",
    }


# --- Execution ---


def execute_command(event):
    """Parse and dispatch a COMMAND_INPUT event to the matching command handler."""
    parts = event["payload"]["raw"].split()
    if not parts:
        return
    name, args = parts[0], parts[1:]
    if name not in commands:
        print(f"Unknown command: {name}")
        return
    try:
        commands[name]["callback"](args)
    except Exception as e:
        print(f"Error in command '{name}': {e}")


# --- Built-in commands ---


def cmd_help(args):
    """Print all registered commands, grouped by source mod."""
    print("Available commands:\n")
    by_mod: dict = {}
    for name, info in commands.items():
        by_mod.setdefault(info["source"], []).append((name, info["description"]))
    for mod_name, cmds in by_mod.items():
        print(f"[{mod_name}]")
        for name, desc in sorted(cmds):
            print(f"  {name:<12} {desc}")
        print()


def cmd_clear(args):
    print("\033[2J\033[H", end="")  # ANSI: clear screen and move cursor to top-left


def cmd_quit(args):
    raise KeyboardInterrupt()  # caught by main.py's command loop → clean shutdown


def cmd_reload(args):
    """
    Emit RELOAD_MOD <name> or RELOAD_ALL.
    main.py handles these events asynchronously via asyncio.create_task().
    """
    if args:
        name = args[0]
        if name not in _core.get_all_mods():  # type:ignore
            print(f"Unknown mod: {name}")
            return
        print(f"Reloading {name}…")
        _core.emit("RELOAD_MOD", {"name": name})  # type:ignore
    else:
        print("Reloading all mods…")
        _core.emit("RELOAD_ALL", {})  # type:ignore
