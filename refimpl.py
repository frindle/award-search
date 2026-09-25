#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s7-parse-date-ranges

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Appends parse_date_ranges to src/webui/scheduled_routes.py, preserving every
line already landed by earlier slices.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''    return [part.strip() for part in value.split(",") if part.strip()]'''

NEW = r'''    return [part.strip() for part in value.split(",") if part.strip()]


def parse_date_ranges(starts: List[str], ends: List[str]) -> List[Dict]:
    """Pair start/end date strings into {"start": ..., "end": ...} dicts.

    Entries are stripped; blank entries are dropped. Each surviving start is
    paired with the end at the same index, or None when no such end exists.
    Extra ends beyond the number of starts are ignored.
    """
    starts = [s.strip() for s in (starts or []) if s and s.strip()]
    ends = [e.strip() for e in (ends or []) if e and e.strip()]
    ranges = []
    for i, start in enumerate(starts):
        end = ends[i] if i < len(ends) else None
        ranges.append({"start": start, "end": end})
    return ranges'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
