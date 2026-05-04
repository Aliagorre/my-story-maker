# mods/mod_error_and_log/main.py

from datetime import datetime
from pathlib import Path

LOG_FILE = Path("engine.log")


def on_load(core):
    """Subscribe to LOG_EVENT as early as possible so no log is missed."""
    core.subscribe("LOG_EVENT", handle_log)
    core.subscribe("ERROR_EVENT", handle_error)
    core.log("INFO", "[mod_error_and_log] loaded")


def on_init(core):
    """Initialize the log file once all mods are discovered."""
    try:
        LOG_FILE.write_text("=== Engine Log Start ===\n", encoding="utf-8")
    except Exception as e:
        core.log("ERROR", "Failed to initialize log file", exception=str(e))


def on_ready(core):
    core.log("INFO", "[mod_error_and_log] ready")


def on_shutdown(core):
    core.log("INFO", "[mod_error_and_log] shutdown")


def handle_log(event):
    _write_log(event, is_error=False)


def handle_error(event):
    _write_log(event, is_error=True)


def _write_log(event, is_error: bool):
    """
    Format and persist a LOG_EVENT to stdout and engine.log.
    Silently ignores write failures to avoid log→error→log infinite loops.
    """
    payload = event["payload"]
    level = payload.get("level", "ERROR" if is_error else "INFO")
    message = payload.get("message", "")
    context = payload.get("context", {})
    source = event.get("source", "?")

    timestamp = datetime.fromtimestamp(event["timestamp"]).strftime("%H:%M:%S")
    prefix = "ERROR" if is_error else level

    line = f"[{timestamp}] [{prefix}] [{source}] {message}"

    if context:
        ctx = " ".join(f"{k}={v}" for k, v in context.items())
        line += f" ({ctx})"

    print(line)

    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass  # cannot log a logging failure — silence is intentional
