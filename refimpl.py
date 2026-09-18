#!/usr/bin/env python3
"""Reference impl for: aw-airport-groups-s1-is-group

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

This is a creation task: src/airport_groups.py starts as a one-line stub, so
the simplest correct move is to write the complete solution file.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / "src/airport_groups.py"
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''\
"""Airport group codes -- city codes that fan out to several airports.

A *group* code (NYC, LON, PAR) stands for a set of member airports; a single
airport code (JFK, LAX) is never a group.
"""

GROUPS = {
    "NYC": ("JFK", "LGA", "EWR"),
    "LON": ("LHR", "STN", "LGW"),
    "PAR": ("CDG", "ORY"),
}


def is_group(code: str) -> bool:
    """Return True if `code` names a known airport group, else False.

    Matching is case-insensitive and ignores surrounding whitespace; non-string
    input (None, numbers) returns False instead of raising.
    """
    if not isinstance(code, str):
        return False
    return code.strip().upper() in GROUPS
'''

p.write_text(SOLUTION)
print("refimpl applied")
