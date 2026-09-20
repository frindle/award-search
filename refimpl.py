#!/usr/bin/env python3
"""Reference impl for: aw-airport-groups-s2-expand-codes

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Write the SIMPLEST change that makes the verify pass. It doubles as your review
reference when the model's diff comes back.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/airport_groups.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''"""Airport group helpers."""
from typing import Iterable, List


def expand_codes(codes: Iterable[str]) -> List[str]:
    """Uppercase each code and drop duplicates, preserving first-seen order."""
    seen = set()
    out = []
    for c in codes:
        u = c.upper()
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out
'''

p.write_text(SOLUTION)
print("refimpl applied")
