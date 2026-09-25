#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s20-program-choices-a-module

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Adds PROGRAM_CHOICES -- a module-level list of {'id','name'} dicts covering
every seats.aero program in config/programs.yml -- to
src/webui/scheduled_routes.py, preserving everything already there.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = r'''TEMPLATES = []'''
NEW = r'''PROGRAM_CHOICES = [
    {"id": program_id, "name": config.get("name") or program_id}
    for program_id, config in load_programs_config().items()
]

TEMPLATES = []'''

assert OLD in t, "refimpl anchor not found -- did the target change?"
p.write_text(t.replace(OLD, NEW, 1))
print("refimpl applied")
