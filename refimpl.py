#!/usr/bin/env python3
"""Reference impl for: aw-alert-filters-s3-passes-filters

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
t = p.read_text()

# First: extend the typing import to cover Dict/Optional used by the new
# signature, preserving List from the earlier slice.
t = t.replace(
    "from typing import List",
    "from typing import Dict, List, Optional", 1)

# Anchor on the tail of normalize_airlines (landed by an earlier slice) so we
# ADD passes_filters without touching any existing code.
OLD = """    codes = []
    for entry in items:
        if not isinstance(entry, str):
            continue
        code = entry.strip().upper()
        if code:
            codes.append(code)
    return codes"""

NEW = OLD + '''


def passes_filters(result: Dict, filters: Optional[Dict]) -> bool:
    """Return True iff `result` satisfies every filter in `filters`.

    None or an empty dict means "no filters" and always passes. Otherwise
    every key of `filters` must be present in `result`, and the two values
    compared as lists of normalized IATA codes via normalize_airlines:
    case-insensitive, whitespace-stripped, order-sensitive. A missing key or
    a value mismatch returns False; no exception is raised for degenerate
    inputs (None filters, empty dicts, absent keys).
    """
    if not filters:
        return True
    for key, want in filters.items():
        if key not in result:
            return False
        if normalize_airlines(result[key]) != normalize_airlines(want):
            return False
    return True'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
