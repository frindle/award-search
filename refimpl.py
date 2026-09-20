#!/usr/bin/env python3
"""Reference impl for: aw-sched-runner-s8-module-constants-default

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Adds the three module constants to src/scheduled_runner.py right after the
import block, preserving everything already in the file. Idempotent: if a
constant is already present it is left untouched.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/scheduled_runner.py'
t = p.read_text()

CONSTS = [
    "DEFAULT_POLL_MINUTES = 15.0",
    "MAX_LEGS_PER_RUN = 60",
    "NOTIFIED_KEYS_CAP = 500",
]

missing = [c for c in CONSTS if not any(
    line.strip().startswith(c.split(" = ")[0]) and "=" in line
    for line in t.splitlines()
)]
if missing:
    # Anchor on the last import line so the constants land right after the
    # import block, before select_results.
    lines = t.splitlines(keepends=True)
    anchor_idx = max(i for i, ln in enumerate(lines) if ln.startswith("from ."))
    insert_at = anchor_idx + 1
    block = "\n\n" + "\n".join(missing) + "\n"
    # If the next line is already blank, don't double up.
    if lines[insert_at].strip() == "":
        block = "\n" + "\n".join(missing) + "\n"
    new_t = "".join(lines[:insert_at]) + block + "".join(lines[insert_at:])
    p.write_text(new_t)
print("refimpl applied")
