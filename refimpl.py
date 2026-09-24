#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s6-parse-csv

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds `parse_csv` to src/webui/scheduled_routes.py and preserves everything
already in the file (prior slices' routes stay untouched).
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

assert "def parse_csv" not in t, "refimpl already applied -- target changed?"

OLD_IMPORTS = r'''from pydantic import BaseModel'''
NEW_IMPORTS = r'''from typing import List, Optional

from pydantic import BaseModel'''
assert OLD_IMPORTS in t, "refimpl anchor (imports) not found -- did the target change?"
t = t.replace(OLD_IMPORTS, NEW_IMPORTS, 1)

ANCHOR = r'''    return run_schedule(program=body.program)'''
ADD = ANCHOR + '''


def parse_csv(value: Optional[str]) -> List[str]:
    """Split a comma-separated value into stripped, non-empty parts."""
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]'''
assert ANCHOR in t, "refimpl anchor (end of file) not found -- did the target change?"
t = t.replace(ANCHOR, ADD, 1)

p.write_text(t)
print("refimpl applied")
