"""Evaluate the range syntax described by this task."""

import re
from typing import List, Optional, Tuple


Core = Tuple[int, int, int]
Version = Tuple[Core, Optional[Tuple[str, ...]]]
Constraint = Tuple[str, Version]
_NUMBER = r"(?:0|[1-9][0-9]*)"
_PART = rf"(?:{_NUMBER}|[xX*])"
_PARTIAL = re.compile(
    rf"({_PART})(?:\.({_PART}))?(?:\.({_PART}))?"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
_COMPARATOR = re.compile(r"(>=|<=|[=><^~])?(.+)")


def _parse_partial(text: str) -> Tuple[Version, int]:
    match = _PARTIAL.fullmatch(text)
    if match is None:
        raise ValueError(f"invalid version: {text!r}")
    numbers = []
    unset = False
    for part in match.group(1, 2, 3):
        if part is None or part in ("x", "X", "*"):
            unset = True
        elif unset:
            raise ValueError(f"number after wildcard: {text!r}")
        else:
            numbers.append(int(part))
    count = len(numbers)
    prerelease = match.group(4)
    if prerelease is not None and count != 3:
        raise ValueError(f"prerelease requires a full version: {text!r}")
    core = tuple(numbers + [0] * (3 - count))
    return (core, tuple(prerelease.split(".")) if prerelease else None), count


def _compare(left: Version, right: Version) -> int:
    if left[0] != right[0]:
        return 1 if left[0] > right[0] else -1
    a, b = left[1], right[1]
    if a is None or b is None:
        return (a is None) - (b is None)
    for x, y in zip(a, b):
        if x.isdigit() and y.isdigit():
            x, y = int(x), int(y)
        elif x.isdigit() != y.isdigit():
            return -1 if x.isdigit() else 1
        if x != y:
            return 1 if x > y else -1
    return (len(a) > len(b)) - (len(a) < len(b))


def _bump(core: Core, index: int) -> Version:
    parts = list(core)
    parts[index] += 1
    parts[index + 1:] = [0] * (2 - index)
    return tuple(parts), None


def _compile(text: str) -> Tuple[List[Constraint], Optional[Core]]:
    match = _COMPARATOR.fullmatch(text)
    if match is None:
        raise ValueError(f"invalid comparator: {text!r}")
    operator = match.group(1) or "="
    version, count = _parse_partial(match.group(2))
    core, prerelease = version
    admission = core if prerelease is not None else None
    upper = _bump(core, count - 1) if count else None
    if operator in (">=", "<"):
        constraints = [(operator, version)]
    elif operator == ">":
        if count == 3:
            constraints = [(">", version)]
        else:
            constraints = [(">=", upper)] if upper else [("<", version)]
    elif operator == "<=":
        if count == 3:
            constraints = [("<=", version)]
        else:
            constraints = [("<", upper)] if upper else []
    elif operator == "=" and count == 3:
        constraints = [("=", version)]
    else:
        if operator == "~" and count:
            upper = _bump(core, min(count - 1, 1))
        elif operator == "^" and count:
            index = next((i for i in range(count) if core[i]), count - 1)
            upper = _bump(core, index)
        constraints = [(">=", version), ("<", upper)] if upper else []
    return constraints, admission


def _matches(version: Version, constraint: Constraint) -> bool:
    operator, bound = constraint
    comparison = _compare(version, bound)
    return {
        "=": comparison == 0,
        ">": comparison > 0,
        ">=": comparison >= 0,
        "<": comparison < 0,
        "<=": comparison <= 0,
    }[operator]


def satisfies(version: str, range_: str) -> bool:
    """Return whether a full version satisfies a valid range.

    Invalid input raises ValueError, including invalid alternatives that would
    otherwise be hidden by a matching earlier alternative.
    """
    parsed, count = _parse_partial(version)
    if count != 3:
        raise ValueError(f"expected a full version: {version!r}")
    sets = []
    for alternative in range_.strip().split("||"):
        tokens = alternative.split()
        if not tokens:
            raise ValueError(f"empty comparator set: {range_!r}")
        sets.append([_compile(token) for token in tokens])
    for comparators in sets:
        admitted = parsed[1] is None or any(
            admission == parsed[0] for _, admission in comparators
        )
        if admitted and all(
            _matches(parsed, constraint)
            for constraints, _ in comparators
            for constraint in constraints
        ):
            return True
    return False
