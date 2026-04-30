# core/__version.py

from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

Segment = Union[int, str]  # int or "*"

@dataclass(frozen=True)
class Version:
    major: Segment
    minor: Segment
    patch: Segment

    @staticmethod
    def parse(value: str) -> "Version|None":
        """
return version object from value
return None in error
        """
        if isinstance(value, Version) :
            return value
        raw = value.strip()
        parts = raw.split(".")
        if len(parts) != 3:
            return None
        for part in parts :
            part = part.strip()
            if part != "*" :
                if part.isdigit() :
                    part = int(part)
                else :
                    return None
        return Version(*parts)

    def as_tuple(self) -> Tuple[Segment, Segment, Segment]:
        """
return segment of version
        """
        return (self.major, self.minor, self.patch)
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

class VersionComparator:
    @staticmethod
    def compare(a: Version|None, b: Version|None) -> int:
        """
return diff between version
        """
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
    def parse(expression: str) -> Union[str, List[Condition]]|None:
        """
parse expression to condition
        """
        expr = expression.strip()
        if expr == "*":
            return "*"
        if not expr:
            return None # raise ValueError("Leere Constraint-Expression")
        conditions: List[Condition] = []
        for raw_part in expr.split(","):
            part = raw_part.strip()
            if not part:
                return None # raise ValueError(f"Ungültige Constraint-Expression: {expression!r}")
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
                return None # raise ValueError(f"Fehlende Zielversion in Bedingung: {part!r}")
            target = None if op == "*" else Version.parse(target_str) # type: ignore
            conditions.append(Condition(op=op, target=target))
        return conditions

class ConstraintResolver:
    @staticmethod
    def check_condition(version: Version, condition: Condition) -> bool:
        """
return True if version match the condition
        """
        if condition.op == "*":
            return True
        if condition.target is None:
            print("correct me in __version.py")
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
        print("correct me in __version.py")
        return False
    
    @staticmethod
    def satisfies(version: Version|None, constraints: Union[str, List[Condition]]|None) -> bool:
        if version is None or constraints is None :
            return False
        if constraints == "*":
            return True
        for condition in constraints:
            if not ConstraintResolver.check_condition(version, condition): # type: ignore
                return False
        return True
