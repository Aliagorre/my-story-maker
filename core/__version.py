# core/__version.py

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

Segment = Union[int, str]  # int oder "*"

@dataclass(frozen=True)
class Version:
    major: Segment
    minor: Segment
    patch: Segment

    @staticmethod
    def parse(value: str) -> "Version|None":
        raw = value.strip()
        parts = raw.split(".")
        if len(parts) != 3:
            return None
        def parse_segment(s: str) -> Segment:
            s = s.strip()
            if s == "*":
                return "*"
            if not s.isdigit():
                raise ValueError(f"Ungültiger Segmentwert: {s!r}")
            return int(s)
        return Version(*(parse_segment(p) for p in parts))

    def as_tuple(self) -> Tuple[Segment, Segment, Segment]:
        return (self.major, self.minor, self.patch)

class VersionComparator:
    @staticmethod
    def compare(a: Version|None, b: Version|None) -> int:
        if a is None or b is None :
            return 0
        for sa, sb in zip(a.as_tuple(), b.as_tuple()):
            if sa == "*" or sb == "*":
                continue
            if sa < sb: # type: ignore
                return -1
            if sa > sb: # type: ignore
                return 1
        return 0

    @staticmethod
    def equals(a: Version, b: Version) -> bool:
        return VersionComparator.compare(a, b) == 0

@dataclass(frozen=True)
class Condition:
    op: str
    target: Optional[Version] = None

class ConstraintParser:
    @staticmethod
    def parse(expression: str) -> Union[str, List[Condition]]:
        expr = expression.strip()
        if expr == "*":
            return "*"
        if not expr:
            raise ValueError("Leere Constraint-Expression")
        conditions: List[Condition] = []
        for raw_part in expr.split(","):
            part = raw_part.strip()
            if not part:
                raise ValueError(f"Ungültige Constraint-Expression: {expression!r}")
            if part == "*":
                conditions.append(Condition(op="*"))
                continue
            op: Optional[str] = None
            target_str: Optional[str] = None
            for candidate in (">=", "<=", "=", ">", "<"):
                if part.startswith(candidate):
                    op = candidate
                    target_str = part[len(candidate):].strip()
                    break
            if op is None:
                op = "="
                target_str = part.strip()
            if op != "*" and not target_str:
                raise ValueError(f"Fehlende Zielversion in Bedingung: {part!r}")
            target = None if op == "*" else Version.parse(target_str) # type: ignore
            conditions.append(Condition(op=op, target=target))
        return conditions

class ConstraintResolver:
    @staticmethod
    def check_condition(version: Version, condition: Condition) -> bool:
        if condition.op == "*":
            return True
        if condition.target is None:
            raise ValueError("Condition ohne Zielversion")
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
        raise ValueError(f"Unbekannter Operator: {condition.op!r}")
    
    @staticmethod
    def satisfies(version: Version|None, constraints: Union[str, List[Condition]]) -> bool:
        if version is None :
            return False
        if constraints == "*":
            return True
        for condition in constraints:
            if not ConstraintResolver.check_condition(version, condition): # type: ignore
                return False
        return True
