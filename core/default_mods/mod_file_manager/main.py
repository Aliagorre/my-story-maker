# mods/default/mod_file_manager/main.py

"""
mod_file_manager — filesystem operations for StoryMaker V7.

Service  : 'file_manager'  (FileService)
Commands : files/ ls · cd · pwd · cat · create · mkdir · rename
                  delete · copy · edit · run · find · info · tree

All paths are resolved relative to the working directory (cwd), which
starts at the process's cwd and can be changed with 'files cd'.
Absolute paths are always accepted.

Service API (for other mods)
─────────────────────────────
    svc = core.get_service("file_manager")

    content, err = svc.read("story.txt")
    ok, err      = svc.write("story.txt", content)
    ok, err      = svc.create("new.txt")
    ok, err      = svc.append("log.txt", "line\n")
    ok, err      = svc.delete("old.txt")
    ok, err      = svc.rename("a.txt", "b.txt")
    ok, err      = svc.copy("a.txt", "backup/a.txt")
    ok, err      = svc.mkdir("saves")
    entries, err = svc.listdir("saves")   # → list[FileEntry]
    info, err    = svc.info("story.txt")  # → dict
    paths        = svc.find("*.py")       # → list[Path]
    rc, out, err = svc.execute("script.py", ["--arg"])
    ok, err      = svc.edit("story.txt")
    cwd          = svc.get_cwd()          # → Path
    ok, path     = svc.set_cwd("saves")
    path         = svc.resolve("rel/path")
"""

import datetime
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from resources.LOG_LEVELS import ERROR, WARNING

MOD_NAME = "mod_file_manager"

_CAT_WARN_LINES = 200  # warn and truncate above this
_CAT_AUTO_LIMIT = 100  # auto-limit for large files
_TREE_DEFAULT_DEPTH = 3


# ══════════════════════════════════════════════════════════════════ Data


@dataclass
class FileEntry:
    name: str
    path: Path
    is_dir: bool
    size: int  # bytes (0 for dirs)
    modified: float  # unix timestamp
    perms: str  # e.g. "drwxr-xr-x"


# ══════════════════════════════════════════════════════════════════ File Service


class FileService:
    """
    Pure file-system operations.  All methods return (result, error_msg).
    error_msg is "" on success.
    """

    def __init__(self, log):
        self._log = log
        self._cwd = Path.cwd().resolve()

    # ── working directory ─────────────────────────────────────────────────

    def get_cwd(self) -> Path:
        return self._cwd

    def set_cwd(self, path) -> tuple[bool, str]:
        p = self._resolve(path)
        if not p.exists():
            return False, f"'{p}' does not exist."
        if not p.is_dir():
            return False, f"'{p}' is not a directory."
        self._cwd = p
        return True, str(p)

    def resolve(self, path) -> Path:
        return self._resolve(path)

    # ── read ──────────────────────────────────────────────────────────────

    def read(self, path) -> tuple[Optional[str], str]:
        p = self._resolve(path)
        try:
            return p.read_text(encoding="utf-8", errors="replace"), ""
        except IsADirectoryError:
            return None, f"'{p.name}' is a directory."
        except FileNotFoundError:
            return None, f"'{p}' not found."
        except PermissionError:
            return None, f"Permission denied: '{p}'."
        except Exception as exc:
            return None, str(exc)

    # ── write / create / append ───────────────────────────────────────────

    def write(self, path, content: str) -> tuple[bool, str]:
        p = self._resolve(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return True, ""
        except PermissionError:
            return False, f"Permission denied: '{p}'."
        except Exception as exc:
            return False, str(exc)

    def create(self, path, content: str = "") -> tuple[bool, str]:
        p = self._resolve(path)
        if p.exists():
            return False, f"'{p.name}' already exists."
        return self.write(p, content)

    def append(self, path, content: str) -> tuple[bool, str]:
        p = self._resolve(path)
        try:
            with p.open("a", encoding="utf-8") as f:
                f.write(content)
            return True, ""
        except PermissionError:
            return False, f"Permission denied: '{p}'."
        except Exception as exc:
            return False, str(exc)

    # ── delete ────────────────────────────────────────────────────────────

    def delete(self, path) -> tuple[bool, str]:
        p = self._resolve(path)
        if not p.exists():
            return False, f"'{p}' does not exist."
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return True, ""
        except PermissionError:
            return False, f"Permission denied: '{p}'."
        except Exception as exc:
            return False, str(exc)

    # ── rename / copy ─────────────────────────────────────────────────────

    def rename(self, src, dst) -> tuple[bool, str]:
        s = self._resolve(src)
        d = self._resolve(dst)
        if not s.exists():
            return False, f"'{s}' does not exist."
        if d.exists():
            return False, f"'{d}' already exists. Choose a different name."
        try:
            s.rename(d)
            return True, ""
        except Exception as exc:
            return False, str(exc)

    def copy(self, src, dst) -> tuple[bool, str]:
        s = self._resolve(src)
        d = self._resolve(dst)
        if not s.exists():
            return False, f"'{s}' does not exist."
        if d.exists():
            return False, f"Destination '{d}' already exists."
        try:
            if s.is_dir():
                shutil.copytree(s, d)
            else:
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s, d)
            return True, ""
        except PermissionError:
            return False, f"Permission denied."
        except Exception as exc:
            return False, str(exc)

    # ── directory ─────────────────────────────────────────────────────────

    def mkdir(self, path) -> tuple[bool, str]:
        p = self._resolve(path)
        if p.exists():
            return False, f"'{p.name}' already exists."
        try:
            p.mkdir(parents=True)
            return True, ""
        except PermissionError:
            return False, f"Permission denied: '{p}'."
        except Exception as exc:
            return False, str(exc)

    def listdir(self, path=None) -> tuple[list[FileEntry], str]:
        p = self._resolve(path) if path else self._cwd
        if not p.exists():
            return [], f"'{p}' does not exist."
        if not p.is_dir():
            return [], f"'{p}' is not a directory."
        try:
            entries = []
            for child in p.iterdir():
                try:
                    st = child.stat()
                    entries.append(
                        FileEntry(
                            name=child.name,
                            path=child,
                            is_dir=child.is_dir(),
                            size=0 if child.is_dir() else st.st_size,
                            modified=st.st_mtime,
                            perms=stat.filemode(st.st_mode),
                        )
                    )
                except PermissionError:
                    entries.append(
                        FileEntry(
                            name=child.name,
                            path=child,
                            is_dir=child.is_dir(),
                            size=0,
                            modified=0.0,
                            perms="?????????",
                        )
                    )
            # Dirs first, then alphabetical
            entries.sort(key=lambda e: (not e.is_dir, e.name.lower()))
            return entries, ""
        except PermissionError:
            return [], f"Permission denied: '{p}'."
        except Exception as exc:
            return [], str(exc)

    # ── info ──────────────────────────────────────────────────────────────

    def info(self, path) -> tuple[Optional[dict], str]:
        p = self._resolve(path)
        if not p.exists():
            return None, f"'{p}' does not exist."
        try:
            st = p.stat()
            return {
                "name": p.name,
                "path": str(p),
                "type": "directory" if p.is_dir() else "file",
                "size": st.st_size,
                "modified": st.st_mtime,
                "created": getattr(st, "st_birthtime", st.st_ctime),
                "perms": stat.filemode(st.st_mode),
                "extension": (p.suffix.lower() or "(none)") if not p.is_dir() else None,
            }, ""
        except Exception as exc:
            return None, str(exc)

    def exists(self, path) -> bool:
        return self._resolve(path).exists()

    def is_dir(self, path) -> bool:
        return self._resolve(path).is_dir()

    # ── find ──────────────────────────────────────────────────────────────

    def find(self, pattern: str, base=None) -> list[Path]:
        root = self._resolve(base) if base else self._cwd
        if not root.is_dir():
            return []
        try:
            return sorted(root.rglob(pattern))
        except Exception:
            return []

    # ── execute / edit ────────────────────────────────────────────────────

    def execute(self, path, args: list[str] = []) -> tuple[int, str, str]:
        """Run a file and return (returncode, stdout, stderr)."""
        p = self._resolve(path)
        if not p.exists():
            return -1, "", f"'{p}' does not exist."
        if not p.is_file():
            return -1, "", f"'{p}' is not a file."
        cmd = self._build_cmd(p, args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self._cwd),
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Execution timed out (30 s)."
        except FileNotFoundError as exc:
            return -1, "", f"Interpreter not found: {exc}"
        except Exception as exc:
            return -1, "", str(exc)

    def edit(self, path) -> tuple[bool, str]:
        """Open path in the user's preferred editor (blocking)."""
        p = self._resolve(path)
        editor = self._find_editor()
        if editor is None:
            return False, "No editor found. Set the $EDITOR environment variable."
        try:
            subprocess.run([editor, str(p)])
            return True, ""
        except Exception as exc:
            return False, str(exc)

    # ── private ───────────────────────────────────────────────────────────

    def _resolve(self, path) -> Path:
        if path is None:
            return self._cwd
        p = Path(str(path))
        return p.resolve() if p.is_absolute() else (self._cwd / p).resolve()

    @staticmethod
    def _find_editor() -> Optional[str]:
        for env_var in ("EDITOR", "VISUAL"):
            if val := os.environ.get(env_var):
                return val
        for candidate in ("nano", "vi", "vim", "notepad"):
            if shutil.which(candidate):
                return candidate
        return None

    @staticmethod
    def _build_cmd(path: Path, args: list[str]) -> list[str]:
        ext = path.suffix.lower()
        interpreters = {
            ".py": [sys.executable],
            ".sh": [shutil.which("bash") or shutil.which("sh") or "sh"],
            ".bash": [shutil.which("bash") or "bash"],
            ".js": [shutil.which("node") or shutil.which("nodejs") or "node"],
            ".rb": [shutil.which("ruby") or "ruby"],
            ".php": [shutil.which("php") or "php"],
        }
        prefix = interpreters.get(ext)
        if prefix and prefix[0]:
            return prefix + [str(path)] + args
        return [str(path)] + args  # direct execution


# ══════════════════════════════════════════════════════════════════ Display


class FileDisplay:
    """Pretty-prints directory listings, file content, and metadata."""

    _KB = 1_024
    _MB = _KB * 1_024
    _GB = _MB * 1_024

    def __init__(self, get_styled):
        self._get = get_styled

    @property
    def _s(self):
        return self._get()

    # ── ls ────────────────────────────────────────────────────────────────

    def print_ls(self, entries: list[FileEntry], directory: Path) -> None:
        s = self._s
        print()
        print(s.h2(f"  {directory}") if s else f"  {directory}")

        if not entries:
            empty = "  (empty directory)"
            print(s.style(empty, color="bright_black") if s else empty)
            print()
            return

        dirs = [e for e in entries if e.is_dir]
        files = [e for e in entries if not e.is_dir]

        name_width = max((len(e.name) + (1 if e.is_dir else 0)) for e in entries)
        name_width = max(name_width, 20)

        if files:
            size_width = max(len(self._fmt_size(e.size)) for e in files)
            size_width = max(size_width, 6)
        else:
            size_width = 6

        print()
        if dirs:
            for e in dirs:
                self._print_dir_row(e, name_width, s)

        if dirs and files:
            print()

        if files:
            for e in files:
                self._print_file_row(e, name_width, size_width, s)

        n_items = len(entries)
        total = sum(e.size for e in files)
        parts = [f"{n_items} item{'s' if n_items != 1 else ''}"]
        if dirs:
            parts.append(f"{len(dirs)} dir{'s' if len(dirs) != 1 else ''}")
        if files:
            parts.append(f"{len(files)} file{'s' if len(files) != 1 else ''}")
            parts.append(self._fmt_size(total) + " total")
        footer = "  " + "  ·  ".join(parts)
        print()
        print(s.style(footer, color="bright_black") if s else footer)
        print()

    def _print_dir_row(self, e: FileEntry, name_width: int, s) -> None:
        name = (e.name + "/").ljust(name_width + 2)
        if s:
            name = s.style(name, color="bright_cyan", styles=["bold"])
            date = s.style(self._fmt_date(e.modified), color="bright_black")
            print(f"    {name}  {date}")
        else:
            print(f"    {name}  {self._fmt_date(e.modified)}")

    def _print_file_row(
        self, e: FileEntry, name_width: int, size_width: int, s
    ) -> None:
        name = e.name.ljust(name_width + 1)
        size = self._fmt_size(e.size).rjust(size_width)
        date = self._fmt_date(e.modified)
        if s:
            name = s.style(name, color="white")
            size = s.style(size, color="bright_black")
            date = s.style(date, color="bright_black")
        print(f"    {name}  {size}  {date}")

    # ── cat ───────────────────────────────────────────────────────────────

    def print_cat(
        self,
        content: str,
        path: Path,
        from_line: int = 1,
        to_line: Optional[int] = None,
    ) -> None:
        s = self._s
        lines = content.splitlines()
        total = len(lines)

        to_line = to_line or total
        from_line = max(1, from_line)
        to_line = min(to_line, total)

        if from_line > to_line:
            self.err(f"Invalid range {from_line}–{to_line} (file has {total} lines).")
            return

        shown = lines[from_line - 1 : to_line]
        range_label = (
            f"lines {from_line}–{to_line} of {total}"
            if (from_line != 1 or to_line != total)
            else f"{total} line{'s' if total != 1 else ''}"
        )
        header = f"  {path}  ({range_label})"
        print()
        print(s.h3(header) if s else header)
        print()

        n_width = len(str(to_line))
        for i, line in enumerate(shown, start=from_line):
            lineno = str(i).rjust(n_width)
            if s:
                lineno = s.style(lineno, color="bright_black")
            print(f"  {lineno}  {line}")
        print()

    # ── info ──────────────────────────────────────────────────────────────

    def print_info(self, info: dict) -> None:
        s = self._s
        print()
        print(s.h2(f"  {info['name']}") if s else f"  {info['name']}")
        print()

        fields: list[tuple[str, str]] = [
            ("Path", info["path"]),
            ("Type", info["type"]),
            ("Size", f"{self._fmt_size(info['size'])}  ({info['size']:,} bytes)"),
            ("Permissions", info["perms"]),
            ("Modified", self._fmt_date(info["modified"], full=True)),
            ("Created", self._fmt_date(info["created"], full=True)),
        ]
        if info.get("extension") is not None:
            fields.insert(2, ("Extension", info["extension"]))

        for label, value in fields:
            lbl = label.ljust(14)
            if s:
                lbl = s.style(lbl, color="cyan")
            print(f"    {lbl}  {value}")
        print()

    # ── find ──────────────────────────────────────────────────────────────

    def print_find(self, results: list[Path], pattern: str, base: Path) -> None:
        s = self._s
        print()
        header = f"  find '{pattern}'  in  {base}"
        print(s.h3(header) if s else header)
        print()

        if not results:
            msg = "  No matches found."
            print(s.style(msg, color="bright_black") if s else msg)
        else:
            for p in results:
                try:
                    rel = p.relative_to(base)
                except ValueError:
                    rel = p
                is_d = p.is_dir()
                text = str(rel) + ("/" if is_d else "")
                if s:
                    line = (
                        s.style(f"  {text}", color="bright_cyan")
                        if is_d
                        else f"  {text}"
                    )
                else:
                    line = f"  {text}"
                print(line)
            count = f"\n  {len(results)} result{'s' if len(results) != 1 else ''}"
            print(s.style(count, color="bright_black") if s else count)
        print()

    # ── tree ──────────────────────────────────────────────────────────────

    def print_tree(self, root: Path, max_depth: int = _TREE_DEFAULT_DEPTH) -> None:
        s = self._s
        print()
        label = str(root) + "/"
        print(s.h2(f"  {label}") if s else f"  {label}")
        self._tree_recurse(root, prefix="", depth=0, max_depth=max_depth, s=s)
        print()

    def _tree_recurse(
        self, path: Path, prefix: str, depth: int, max_depth: int, s
    ) -> None:
        if depth > max_depth:
            faint = "  " + prefix + "  …"
            print(s.style(faint, color="bright_black") if s else faint)
            return
        try:
            entries = sorted(
                path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower())
            )
        except PermissionError:
            denied = f"  {prefix}  [permission denied]"
            print(s.style(denied, color="bright_red") if s else denied)
            return

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            extension = "    " if is_last else "│   "

            if entry.is_dir():
                name = entry.name + "/"
                if s:
                    name = s.style(name, color="bright_cyan", styles=["bold"])
                print(f"  {prefix}{connector}{name}")
                self._tree_recurse(entry, prefix + extension, depth + 1, max_depth, s)
            else:
                print(f"  {prefix}{connector}{entry.name}")

    # ── feedback ──────────────────────────────────────────────────────────

    def ok(self, msg: str) -> None:
        s = self._s
        line = f"  ✓  {msg}"
        print(s.style(line, color="bright_green") if s else line)

    def err(self, msg: str) -> None:
        s = self._s
        line = f"  ✗  {msg}"
        print(s.style(line, color="bright_red") if s else line)

    def warn(self, msg: str) -> None:
        s = self._s
        line = f"  !  {msg}"
        print(s.style(line, color="yellow") if s else line)

    def info(self, msg: str) -> None:
        s = self._s
        line = f"  →  {msg}"
        print(s.style(line, color="cyan") if s else line)

    # ── formatting helpers ────────────────────────────────────────────────

    def _fmt_size(self, size: int) -> str:
        if size < self._KB:
            return f"{size} B"
        if size < self._MB:
            return f"{size / self._KB:.1f} KB"
        if size < self._GB:
            return f"{size / self._MB:.1f} MB"
        return f"{size / self._GB:.2f} GB"

    @staticmethod
    def _fmt_date(ts: float, full: bool = False) -> str:
        if not ts:
            return "—"
        dt = datetime.datetime.fromtimestamp(ts)
        fmt = "%Y-%m-%d %H:%M:%S" if full else "%Y-%m-%d %H:%M"
        return dt.strftime(fmt)


# ══════════════════════════════════════════════════════════════════ Commands


class _FileCommands:
    def __init__(self, svc: FileService, display: FileDisplay, core):
        self._svc = svc
        self._display = display
        self._core = core

    def register_all(self) -> None:
        cmd = self._core.get_service("cmd_interface")
        if cmd is None:
            return

        _DIR = "files"
        _DESC = "File system operations."

        defs = [
            ("ls", self._cmd_ls, "List directory contents.", f"{_DIR} ls [path]"),
            ("cd", self._cmd_cd, "Change working directory.", f"{_DIR} cd <path>"),
            ("pwd", self._cmd_pwd, "Print current working directory.", f"{_DIR} pwd"),
            (
                "cat",
                self._cmd_cat,
                "Display file contents with line numbers.",
                f"{_DIR} cat <file> [--from N] [--to N]",
            ),
            (
                "create",
                self._cmd_create,
                "Create a new empty file.",
                f"{_DIR} create <path>",
            ),
            (
                "mkdir",
                self._cmd_mkdir,
                "Create a new directory.",
                f"{_DIR} mkdir <path>",
            ),
            (
                "rename",
                self._cmd_rename,
                "Rename or move a file / directory.",
                f"{_DIR} rename <src> <dst>",
            ),
            (
                "delete",
                self._cmd_delete,
                "Delete a file or directory.",
                f"{_DIR} delete <path> [--confirm]",
            ),
            (
                "copy",
                self._cmd_copy,
                "Copy a file or directory.",
                f"{_DIR} copy <src> <dst>",
            ),
            ("edit", self._cmd_edit, "Open a file in $EDITOR.", f"{_DIR} edit <file>"),
            (
                "run",
                self._cmd_run,
                "Execute a file (.py .sh .js …).",
                f"{_DIR} run <file> [args …]",
            ),
            (
                "find",
                self._cmd_find,
                "Search recursively by name pattern.",
                f"{_DIR} find <pattern> [base_path]",
            ),
            (
                "info",
                self._cmd_info,
                "Show detailed file / directory info.",
                f"{_DIR} info <path>",
            ),
            (
                "tree",
                self._cmd_tree,
                "Display a recursive directory tree.",
                f"{_DIR} tree [path] [--depth N]",
            ),
        ]
        for name, cb, description, usage in defs:
            cmd.register(
                f"{_DIR}/{name}",
                cb,
                description=description,
                usage=usage,
                dir_description=_DESC,
            )

    # ── handlers ──────────────────────────────────────────────────────────

    def _cmd_ls(self, args: list[str]) -> None:
        path = args[0] if args else None
        target = self._svc.resolve(path) if path else self._svc.get_cwd()
        entries, error = self._svc.listdir(target)
        if error:
            self._display.err(error)
            return
        self._display.print_ls(entries, target)

    def _cmd_cd(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files cd <path>")
            return
        ok, msg = self._svc.set_cwd(args[0])
        if ok:
            self._display.info(f"cwd → {msg}")
        else:
            self._display.err(msg)

    def _cmd_pwd(self, _args: list[str]) -> None:
        self._display.info(str(self._svc.get_cwd()))

    def _cmd_cat(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files cat <file> [--from N] [--to N]")
            return

        path = args[0]
        from_line = 1
        to_line = None
        i = 1
        while i < len(args):
            flag = args[i]
            if flag in ("--from", "--to") and i + 1 < len(args):
                try:
                    val = int(args[i + 1])
                except ValueError:
                    self._display.err(f"'{args[i + 1]}' is not a valid line number.")
                    return
                if flag == "--from":
                    from_line = val
                else:
                    to_line = val
                i += 2
            else:
                i += 1

        content, error = self._svc.read(path)
        if error:
            self._display.err(error)
            return

        total = content.count("\n") + 1
        if total > _CAT_WARN_LINES and to_line is None and from_line == 1:
            self._display.warn(
                f"File has {total} lines — showing first {_CAT_AUTO_LIMIT}. "
                "Use --from / --to for a specific range."
            )
            to_line = _CAT_AUTO_LIMIT

        self._display.print_cat(content, self._svc.resolve(path), from_line, to_line)

    def _cmd_create(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files create <path>")
            return
        ok, error = self._svc.create(args[0])
        if ok:
            self._display.ok(f"Created: {self._svc.resolve(args[0])}")
        else:
            self._display.err(error)

    def _cmd_mkdir(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files mkdir <path>")
            return
        ok, error = self._svc.mkdir(args[0])
        if ok:
            self._display.ok(f"Directory created: {self._svc.resolve(args[0])}")
        else:
            self._display.err(error)

    def _cmd_rename(self, args: list[str]) -> None:
        if len(args) < 2:
            self._display.err("Usage: files rename <src> <dst>")
            return
        ok, error = self._svc.rename(args[0], args[1])
        if ok:
            src = self._svc.resolve(args[1])  # resolved destination (new name)
            self._display.ok(f"Renamed → {src}")
        else:
            self._display.err(error)

    def _cmd_delete(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files delete <path> [--confirm]")
            return
        path = args[0]
        confirm = "--confirm" in args
        target = self._svc.resolve(path)

        if not self._svc.exists(path):
            self._display.err(f"'{target}' does not exist.")
            return

        if not confirm:
            kind = (
                "directory (and all its contents)" if self._svc.is_dir(path) else "file"
            )
            self._display.warn(
                f"About to permanently delete {kind}:\n"
                f"    {target}\n"
                f"  Run again with --confirm to proceed."
            )
            return

        ok, error = self._svc.delete(path)
        if ok:
            self._display.ok(f"Deleted: {target}")
        else:
            self._display.err(error)

    def _cmd_copy(self, args: list[str]) -> None:
        if len(args) < 2:
            self._display.err("Usage: files copy <src> <dst>")
            return
        ok, error = self._svc.copy(args[0], args[1])
        if ok:
            src = self._svc.resolve(args[0])
            dst = self._svc.resolve(args[1])
            self._display.ok(f"Copied: {src}  →  {dst}")
        else:
            self._display.err(error)

    def _cmd_edit(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files edit <file>")
            return
        ok, error = self._svc.edit(args[0])
        if not ok:
            self._display.err(error)

    def _cmd_run(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files run <file> [args …]")
            return
        path = args[0]
        file_args = args[1:]
        target = self._svc.resolve(path)
        self._display.info(f"Running: {target}")

        rc, stdout, stderr = self._svc.execute(path, file_args)
        s = self._display._s

        if stdout:
            print(stdout, end="")
        if stderr:
            print(s.style(stderr, color="bright_red") if s else stderr, end="")

        status = f"Exit code: {rc}"
        (self._display.ok if rc == 0 else self._display.err)(status)

    def _cmd_find(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files find <pattern> [base_path]")
            return
        pattern = args[0]
        base = self._svc.resolve(args[1]) if len(args) > 1 else self._svc.get_cwd()
        results = self._svc.find(pattern, base)
        self._display.print_find(results, pattern, base)

    def _cmd_info(self, args: list[str]) -> None:
        if not args:
            self._display.err("Usage: files info <path>")
            return
        data, error = self._svc.info(args[0])
        if error:
            self._display.err(error)
            return
        self._display.print_info(data)

    def _cmd_tree(self, args: list[str]) -> None:
        path_arg = None
        max_depth = _TREE_DEFAULT_DEPTH
        i = 0
        while i < len(args):
            if args[i] == "--depth" and i + 1 < len(args):
                try:
                    max_depth = int(args[i + 1])
                except ValueError:
                    self._display.err(f"Invalid depth: '{args[i + 1]}'")
                    return
                i += 2
            else:
                path_arg = args[i]
                i += 1

        root = self._svc.resolve(path_arg) if path_arg else self._svc.get_cwd()
        if not root.exists():
            self._display.err(f"'{root}' does not exist.")
            return
        if not root.is_dir():
            self._display.err(f"'{root}' is not a directory.")
            return
        self._display.print_tree(root, max_depth)


# ══════════════════════════════════════════════════════════════════ Mod


class Mod:
    MOD_NAME = "mod_file_manager"

    def on_load(self, core):
        self._core = core
        get_styled = lambda: core.get_service("styled_text")
        self._service = FileService(core.log)
        self._display = FileDisplay(get_styled)
        self._cmds = _FileCommands(self._service, self._display, core)
        core.register_service("file_manager", self._service)

    def on_init(self, core):
        self._cmds.register_all()

    def on_ready(self, event):
        pass

    def on_shutdown(self, core):
        pass
