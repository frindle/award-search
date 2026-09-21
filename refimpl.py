#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s4-init

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Writes the SIMPLEST change that makes the verify pass: appends a module-level
`TEMPLATES = []`, an `init(templates)` setter, and a GET /api/scheduled/templates
route to the existing scheduled_routes.py, preserving everything already in the
file (imports, RunRequest, /partners routes, /run route). The fixture stubs
src.transfer_partners and src.scheduled_runner anyway; this keeps the target's
relative imports honest for direct `python3 -c "import ..."` checks.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

NEW_BLOCK = '''

TEMPLATES = []


def init(templates):
    """Set the module-level TEMPLATES to the given list of templates."""
    global TEMPLATES
    TEMPLATES = templates


@router.get("/templates")
def scheduled_templates():
    return {"templates": TEMPLATES}
'''

if "def init(templates):" not in t:
    t = t.rstrip() + "\n" + NEW_BLOCK

p.write_text(t)
print("refimpl applied")
