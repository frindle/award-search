#!/usr/bin/env python3
"""Reference impl for: aw-alert-filters-s2-normalize-airlines

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
p = wt / 'src/alert_filters.py'
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''from typing import List


def normalize_airlines(value) -> List[str]:
    """Normalize an airline filter value into uppercase IATA codes.

    Accepts a list/tuple of codes, a single code string, or None; returns the
    stripped, uppercased non-empty codes in order, [] when there are none.
    Non-string entries are skipped; any other input type raises TypeError.
    """
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        raise TypeError("normalize_airlines expects a list, str or None")
    codes = []
    for item in items:
        if not isinstance(item, str):
            continue
        code = item.strip().upper()
        if code:
            codes.append(code)
    return codes
'''

p.write_text(SOLUTION)
print("refimpl applied")
