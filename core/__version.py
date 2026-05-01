# core/__version.py

from dataclasses import dataclass
from typing import List, Optional, Union

Segment = Union[int, str]  # int or "*"


@dataclass(frozen=True)
class Version:
    major: Segment
    minor: Segment
    patch: Segment

    @staticmethod
    def parse(value: str) -> "Version | None":
        """Parse a dotted version string such as '1.2.3' or '1.*.3'.

        Each segment must be a non-negative integer or the wildcard '*'.
        Returns None when the string is malformed.
        Already-parsed Version objects are returned unchanged.
        """
        if isinstance(value, Version):
            return value
        raw = value.strip()
        parts = raw.split(".")
        if len(parts) != 3:
            return None
        parsed: list[Segment] = []
        for part in parts:
            part = part.strip()
            if part == "*":
                parsed.append("*")
            elif part.isdigit():
                parsed.append(int(part))  # convert to int — the earlier code
            else:  # only reassigned a local variable
                return None
        return Version(*parsed)

    def as_tuple(self) -> tuple[Segment, Segment, Segment]:
        """Return the version as a (major, minor, patch) tuple."""
        return (self.major, self.minor, self.patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


class VersionComparator:
    @staticmethod
    def compare(a: "Version | None", b: "Version | None") -> int:
        """Compare two versions segment by segment.

        Wildcards ('*') are skipped and treated as equal to anything.
        Returns -1 if a < b, 0 if a == b, 1 if a > b.
        Returns 0 when either argument is None.
        """
        if a is None or b is None:
            return 0
        for sa, sb in zip(a.as_tuple(), b.as_tuple()):
            if sa == "*" or sb == "*":
                continue
            if sa < sb:  # type: ignore[operator]
                return -1
            if sa > sb:  # type: ignore[operator]
                return 1
        return 0

    @staticmethod
    def equals(a: "Version", b: "Version") -> bool:
        """Return True when both versions compare as equal."""
        return VersionComparator.compare(a, b) == 0


@dataclass(frozen=True)
class Condition:
    """A single constraint condition with an operator and an optional target version."""

    op: str
    target: Optional["Version"] = None


class ConstraintParser:
    @staticmethod
    def parse(expression: str) -> "str | List[Condition] | None":
        """Parse a constraint expression into a list of Conditions.

        Accepts '*' (match everything) or comma-separated conditions such as
        '>=1.2.0,<2.0.0', '=1.*.*', or plain '1.2.3' (implicitly '=').
        Returns '*' for the wildcard, a list of Condition objects on success,
        or None when the expression is empty or malformed.
        """
        expr = expression.strip()
        if expr == "*":
            return "*"
        if not expr:
            return None
        conditions: List[Condition] = []
        for raw_part in expr.split(","):
            part = raw_part.strip()
            if not part:
                return None
            if part == "*":
                conditions.append(Condition(op="*"))
                continue
            op: Optional[str] = None
            target_str: Optional[str] = None
            for candidate in (">=", "<=", "=", ">", "<"):
                if part.startswith(candidate):
                    op = candidate
                    target_str = part[len(candidate) :].strip()
                    break
            if op is None:
                op = "="
                target_str = part.strip()
            if op != "*" and not target_str:
                return None
            target = None if op == "*" else Version.parse(target_str)  # type: ignore[arg-type]
            conditions.append(Condition(op=op, target=target))
        return conditions


class ConstraintResolver:
    @staticmethod
    def check_condition(version: "Version", condition: Condition) -> bool:
        """Return True when the version satisfies a single Condition."""
        if condition.op == "*":
            return True
        if condition.target is None:
            return False
        cmp = VersionComparator.compare(version, condition.target)
        if condition.op == "=":
            return cmp == 0
        if condition.op == ">":
            return cmp == 1
        if condition.op == "<":
            return cmp == -1
        if condition.op == ">=":
            return cmp in (0, 1)
        if condition.op == "<=":
            return cmp in (0, -1)
        return False

    @staticmethod
    def satisfies(
        version: "Version | None",
        constraints: "str | List[Condition] | None",
    ) -> bool:
        """Return True when the version satisfies every constraint.

        Returns False when either argument is None.
        The wildcard constraint '*' always returns True.
        """
        if version is None or constraints is None:
            return False
        if constraints == "*":
            return True
        for condition in constraints:  # type: ignore[union-attr]
            if not ConstraintResolver.check_condition(version, condition):  # type: ignore
                return False
        return True
