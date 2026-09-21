#!/usr/bin/env python3
"""Reference impl for: aw-alert-filters-s5-describe-filters

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Appends describe_filters to src/alert_filters.py, preserving everything the
earlier slices landed in this file.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/alert_filters.py'
t = p.read_text()

NEW = '''

def describe_filters(filters: Optional[Dict]) -> str:
    """Short human summary of a filter dict, e.g. "airlines UA,NH".

    None or an empty dict means no filters and yields "(no filters)".
    Otherwise each key is rendered as "<key> <codes>" where the codes are
    normalize_airlines(value) joined with "," (an empty code list renders
    just the bare key), and pairs are joined in insertion order with "; ".
    """
    if not filters:
        return "(no filters)"
    parts = []
    for key, value in filters.items():
        codes = normalize_airlines(value)
        parts.append(key + (" " + ",".join(codes) if codes else ""))
    return "; ".join(parts)
'''

if "def describe_filters" in t:
    print("refimpl already applied")
else:
    p.write_text(t.rstrip("\n") + "\n" + NEW)
print("refimpl applied")
