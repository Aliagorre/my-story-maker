# core/default_mods/mod_cmd/main.py

import threading
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import readline

    _HAS_READLINE = True
except ImportError:
    _HAS_READLINE = False


@dataclass
class Command:
    """A leaf node: an executable command with metadata."""

    name: str
    callback: Callable  # fn(args: list[str]) -> None
    description: str
    usage: str
    full_path: str  # slash-separated, e.g. "adventure/editor/open"


class CommandNode:
    """
    One node in the command tree.
    A node can contain both sub-directories (dirs) and leaf commands (commands).
    A name cannot be used for both a sub-directory and a command at the same level.
    """

    def __init__(self, name: str = "", description: str = ""):
        self.name: str = name
        self.description: str = description
        self.dirs: dict[str, "CommandNode"] = {}
        self.commands: dict[str, Command] = {}

    def get_or_create_dir(self, name: str, description: str = "") -> "CommandNode":
        if name not in self.dirs:
            self.dirs[name] = CommandNode(name, description)
        return self.dirs[name]


class CommandRegistry:
    """
    Stores and resolves the full command tree.

    Example tree:
        root
        ├── help            (command)
        ├── quit            (command)
        ├── clear           (command)
        └── adventure/      (dir)
            ├── load        (command)
            ├── save        (command)
            └── editor/     (dir)
                └── open    (command)
    """

    def __init__(self):
        self.root = CommandNode("root")

    # ── registration ──────────────────────────────────────────────────────

    def register(
        self,
        path: str,
        callback: Callable,
        description: str = "",
        usage: str = "",
        dir_description: str = "",
    ) -> bool:
        """
        Register a command at the given slash-separated path.

        Intermediate directories are created automatically.
        Returns False if:
          - path is empty / malformed
          - a command already exists at that path
          - a name at any intermediate level conflicts with an existing command
          - the leaf name conflicts with an existing directory
        """
        parts = [p.strip() for p in path.strip("/").split("/") if p.strip()]
        if not parts:
            return False

        node = self.root
        for part in parts[:-1]:
            if part in node.commands:
                return False  # can't use a command name as a directory
            node = node.get_or_create_dir(part, dir_description)

        cmd_name = parts[-1]
        if cmd_name in node.commands:
            return False  # duplicate command
        if cmd_name in node.dirs:
            return False  # name already used as a directory

        full_path = "/".join(parts)
        node.commands[cmd_name] = Command(
            name=cmd_name,
            callback=callback,
            description=description,
            usage=usage or full_path,
            full_path=full_path,
        )
        return True

    def set_dir_description(self, path: str, description: str) -> bool:
        """Update the description of an existing directory node."""
        parts = [p.strip() for p in path.strip("/").split("/") if p.strip()]
        node = self.root
        for part in parts:
            if part not in node.dirs:
                return False
            node = node.dirs[part]
        node.description = description
        return True

    # ── resolution ────────────────────────────────────────────────────────

    def resolve(self, tokens: list[str]) -> tuple[Optional[Command], list[str], str]:
        """
        Walk tokens through the tree to find a command.

        Returns (command, remaining_args, error_msg).
        On success error_msg is "".
        Commands are matched before directories when both share a name (impossible
        by design, but the rule is explicit).

        Examples:
            ["help"]                   → (help_cmd, [], "")
            ["adventure", "load", "f"] → (load_cmd, ["f"], "")
            ["adventure"]              → (None, [], "Incomplete …  Available: load, save, editor/")
            ["foo"]                    → (None, [], "Unknown: 'foo'. …")
        """
        if not tokens:
            return None, [], "No command given."

        node = self.root
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token in node.commands:
                return node.commands[token], tokens[i + 1 :], ""
            if token in node.dirs:
                node = node.dirs[token]
                i += 1
                continue
            prefix = " ".join(tokens[: i + 1])
            return None, [], f"Unknown: '{prefix}'.{self._hint(node)}"

        prefix = " ".join(tokens)
        return None, [], f"Incomplete command '{prefix}'.{self._hint(node)}"

    # ── completion ────────────────────────────────────────────────────────

    def completions(self, nav_tokens: list[str], partial: str) -> list[str]:
        """
        Return sorted completions for `partial` after navigating `nav_tokens`.

        Directories are suffixed with '/' in the candidate list so the user
        can tell them apart from commands.
        """
        node = self.root
        for token in nav_tokens:
            if token in node.dirs:
                node = node.dirs[token]
            elif token in node.commands:
                return []  # already past a command, nothing to complete
            else:
                return []

        dirs_candidates = [name + "/" for name in sorted(node.dirs.keys())]
        cmd_candidates = sorted(node.commands.keys())
        candidates = dirs_candidates + cmd_candidates
        return [c for c in candidates if c.startswith(partial)]

    # ── private ───────────────────────────────────────────────────────────

    @staticmethod
    def _hint(node: CommandNode) -> str:
        items = [n + "/" for n in sorted(node.dirs.keys())] + sorted(
            node.commands.keys()
        )
        if not items:
            return ""
        return "\n  Available: " + ", ".join(items)


class TabCompleter:
    """
    Plugs into the readline completer API.

    Completion rules:
      - If the line ends with a space, complete the *next* token from the
        current node (all tokens are already-navigated).
      - Otherwise, complete the *partial* last token.
      - Directories are suffixed with '/'; selecting one does NOT add a space
        so the user can keep typing the sub-command immediately.
    """

    def __init__(self, registry: CommandRegistry):
        self._registry = registry
        self._matches: list[str] = []

    def install(self) -> None:
        if not _HAS_READLINE:
            return
        readline.set_completer(self.complete)
        readline.set_completer_delims(" \t\n")
        # On macOS libedit uses a different bind syntax
        if "libedit" in getattr(readline, "__doc__", ""):
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

    def complete(self, text: str, state: int) -> Optional[str]:
        if state == 0:
            self._matches = self._compute(text)
        return self._matches[state] if state < len(self._matches) else None

    def _compute(self, _text: str) -> list[str]:
        if not _HAS_READLINE:
            return []
        line = readline.get_line_buffer()
        tokens = line.split()
        ends_with_space = not line or line[-1] == " "

        if ends_with_space:
            nav_tokens, partial = tokens, ""
        else:
            nav_tokens = tokens[:-1]
            partial = tokens[-1] if tokens else ""

        # readline expects completions that replace `text` (the partial word).
        # Our candidates include the prefix already, so we return them as-is.
        return self._registry.completions(nav_tokens, partial)


class HelpPrinter:
    """
    Formats and prints help output.
    Uses the 'styled_text' service when available, falls back to plain text.
    The service is fetched lazily on every print call so it is available even
    if it was registered after mod_cmd.
    """

    _COL = 28  # column width for the name / label

    def __init__(self, get_styled: Callable):
        self._get_styled = get_styled  # () -> styled_text service | None

    @property
    def _s(self):
        return self._get_styled()

    # ── public ────────────────────────────────────────────────────────────

    def print_root(self, root: CommandNode) -> None:
        """Print the root-level help listing."""
        s = self._s
        out = []

        if root.commands:
            out.append(self._section("Commands", s))
            for name, cmd in sorted(root.commands.items()):
                out.append(self._entry(name, cmd.description, s))

        if root.dirs:
            if out:
                out.append("")
            out.append(self._section("Directories", s))
            for name, node in sorted(root.dirs.items()):
                out.append(self._entry(name + "/", node.description, s))

        if not root.commands and not root.dirs:
            out.append("  No commands registered.")

        out += [
            "",
            "  help <command>       show command details",
            "  help <dir> ...       explore a directory",
        ]
        print("\n".join(out))

    def print_node(self, node: CommandNode, path: list[str]) -> None:
        """Print help for a directory node."""
        s = self._s
        title = " ".join(path) + "/"
        out = [self._heading(title, s), ""]

        if node.commands:
            out.append(self._section("Commands", s))
            for name, cmd in sorted(node.commands.items()):
                out.append(self._entry(name, cmd.description, s))

        if node.dirs:
            if len(out) > 2:
                out.append("")
            out.append(self._section("Directories", s))
            for name, child in sorted(node.dirs.items()):
                out.append(self._entry(name + "/", child.description, s))

        if not node.commands and not node.dirs:
            out.append("  (empty directory)")

        print("\n".join(out))

    def print_command(self, cmd: Command, path: list[str]) -> None:
        """Print detailed help for a single command."""
        s = self._s
        full = " ".join(path)
        out = [self._heading(full, s), ""]

        if cmd.description:
            out += [f"  {cmd.description}", ""]

        out.append(self._section("Usage", s))
        out.append(f"    {cmd.usage}")
        print("\n".join(out))

    def print_error(self, message: str) -> None:
        s = self._s
        print(s.style(message, color="bright_red") if s else message)

    def print_info(self, message: str) -> None:
        s = self._s
        print(s.style(message, color="cyan") if s else message)

    # ── formatting helpers ────────────────────────────────────────────────

    def _heading(self, text: str, s) -> str:
        return s.h2(text) if s else text

    def _section(self, title: str, s) -> str:
        return s.h3(f"  {title}") if s else f"  {title}:"

    def _entry(self, name: str, description: str, s) -> str:
        padded = name.ljust(self._COL)
        label = s.style(padded, styles=["bold"]) if s else padded
        return f"    {label}  {description}" if description else f"    {label}"


class InputLoop:
    """
    Daemon thread that reads lines from stdin and dispatches them.

    The thread is a daemon so the process exits cleanly even if the thread
    is blocked on input() during shutdown.
    """

    def __init__(
        self,
        registry: CommandRegistry,
        log: Callable,
        on_error: Callable,
        prompt: str = "> ",
    ):
        self._registry = registry
        self._log = log
        self._on_error = on_error
        self._prompt = prompt
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="mod_cmd_input"
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self) -> None:
        while self._running:
            try:
                line = input(self._prompt)
            except EOFError:
                break
            except KeyboardInterrupt:
                break

            line = line.strip()
            if not line:
                continue

            tokens = line.split()
            command, args, error = self._registry.resolve(tokens)

            if command is None:
                self._on_error(error)
                continue

            try:
                command.callback(args)
            except SystemExit:
                raise
            except Exception as exc:
                self._log("ERROR", f"[mod_cmd] '{command.full_path}': {exc}")


class CmdInterface:
    """
    Service exposed as 'cmd_interface'.

    Usage from another mod:

        def on_init(self, core):
            cmd = core.get_service("cmd_interface")
            if cmd:
                cmd.register(
                    "adventure/load",
                    self._load,
                    description="Load an adventure from disk.",
                    usage="adventure load <file>",
                    dir_description="Adventure management commands.",
                )

        def _load(self, args):
            if not args:
                print("Usage: adventure load <file>")
                return
            print(f"Loading {args[0]}…")
    """

    def __init__(self, core):
        self._core = core
        self._registry = CommandRegistry()
        self._completer = TabCompleter(self._registry)
        self._help = HelpPrinter(lambda: core.get_service("styled_text"))
        self._loop = InputLoop(
            registry=self._registry,
            log=self._log,
            on_error=self._help.print_error,
        )
        self._register_defaults()

    def register(
        self,
        path: str,
        callback: Callable,
        *,
        description: str = "",
        usage: str = "",
        dir_description: str = "",
    ) -> bool:
        """
        Register a command.

        path            Slash-separated path, e.g. "mydir/subdir/mycommand".
                        Intermediate directories are created automatically.
        callback        Callable receiving args: list[str].
        description     One-line description shown in help listings.
        usage           Usage string, e.g. "adventure load <file> [--dry]".
                        Defaults to the bare path if omitted.
        dir_description Description for newly-created intermediate directories.

        Returns True on success, False if the path conflicts with an existing
        command or directory.
        """
        ok = self._registry.register(
            path, callback, description, usage, dir_description
        )
        if not ok:
            self._log("WARNING", f"[mod_cmd] could not register '{path}'")
        return ok

    def set_dir_description(self, path: str, description: str) -> bool:
        """
        Set or update the description of a directory node.
        Useful when multiple mods share a namespace and only one knows the
        right description.
        """
        return self._registry.set_dir_description(path, description)

    def start(self) -> None:
        self._completer.install()
        self._loop.start()

    def stop(self) -> None:
        self._loop.stop()

    def _register_defaults(self) -> None:
        self._registry.register(
            "help",
            self._cmd_help,
            description="Show commands and directories. 'help <path>' for details.",
            usage="help [path ...]",
        )
        self._registry.register(
            "quit",
            self._cmd_quit,
            description="Shut down the engine.",
            usage="quit",
        )
        self._registry.register(
            "clear",
            self._cmd_clear,
            description="Clear the terminal screen.",
            usage="clear",
        )

    def _cmd_help(self, args: list[str]) -> None:
        """
        help                 → root listing
        help <dir>           → listing for that directory
        help <dir> <subdir>  → listing for nested directory
        help <command>       → command detail
        help <dir> <command> → command detail (namespaced)
        """
        if not args:
            self._help.print_root(self._registry.root)
            return

        node = self._registry.root
        path: list[str] = []

        for i, part in enumerate(args):
            # Directories take priority over commands when navigating a path
            if part in node.dirs:
                path.append(part)
                node = node.dirs[part]
            elif part in node.commands:
                self._help.print_command(node.commands[part], path + [part])
                return
            else:
                prefix = " ".join(args[: i + 1])
                self._help.print_error(f"Unknown: '{prefix}'.")
                return

        # Consumed all args navigating directories → show node listing
        self._help.print_node(node, path)

    def _cmd_quit(self, _args):
        self._core.shutdown_event.set()

    def _cmd_clear(self, _args: list[str]) -> None:
        # ANSI: erase entire screen + move cursor to top-left
        print("\033[2J\033[H", end="", flush=True)

    def _log(self, level: str, message: str) -> None:
        self._core.log(level, message)


class Mod:
    MOD_NAME = "mod_cmd"

    def on_load(self, core):
        self.core = core
        self._interface = CmdInterface(core)
        core.register_service("cmd_interface", self._interface)

    def on_init(self, core):
        # styled_text is fetched lazily by HelpPrinter; nothing to do here.
        pass

    def on_ready(self, event):
        # event is the ENGINE_READY dict (not core).
        self._interface.start()

    def on_shutdown(self, core):
        self._interface.stop()
