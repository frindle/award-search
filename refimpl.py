#!/usr/bin/env python3
"""Reference impl for: aw-airport-groups-s3-group-label

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/airport_groups.py'
t = p.read_text()

OLD = '''def expand_codes(codes: Iterable[str]) -> List[str]:'''
NEW = '''AIRPORT_GROUPS = {
    "JFK": {"name": "New York (JFK)"},
    "LHR": {"name": "London (LHR)"},
}


def group_label(code: str) -> str:
    return AIRPORT_GROUPS[code]['name'] if code in AIRPORT_GROUPS else code


def expand_codes(codes: Iterable[str]) -> List[str]:'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
