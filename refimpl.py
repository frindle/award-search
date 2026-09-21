#!/usr/bin/env python3
"""Reference impl for: aw-airport-groups-s4-list-groups

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds `list_groups()` to src/airport_groups.py, preserving everything earlier
slices landed in this file. Idempotent: if the function is already present it
is a no-op.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/airport_groups.py'
t = p.read_text()

FUNC = '''

def list_groups() -> List[Dict]:
    return [
        {"code": code, "name": AIRPORT_GROUPS[code]["name"], "airports": [code]}
        for code in sorted(AIRPORT_GROUPS)
    ]
'''

if "def list_groups" not in t:
    if not t.endswith("\n"):
        t += "\n"
    p.write_text(t + FUNC)
print("refimpl applied")
