#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s3-from-scheduled-runner-im

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Writes the SIMPLEST change that makes the verify pass: adds the
`from ..scheduled_runner import run_schedule` import to the existing
scheduled_routes.py and a POST /api/scheduled/run route that calls it,
preserving everything already in the file. Also materialises a minimal
src/scheduled_runner.py so the relative import resolves (the fixture stubs
it anyway; this keeps `python3 -c "import src.webui.scheduled_routes"`
honest). Revert deletes it because it is untracked.
"""
import pathlib

wt = pathlib.Path(__file__).resolve().parent
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD_IMPORTS = """from fastapi import APIRouter, HTTPException

from ..transfer_partners import list_partners
"""
NEW_IMPORTS = """from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

from ..scheduled_runner import run_schedule
from ..transfer_partners import list_partners
"""
assert OLD_IMPORTS in t, "refimpl anchor not found -- did the target change?"
t = t.replace(OLD_IMPORTS, NEW_IMPORTS, 1)

NEW_ROUTE = '''

class RunRequest(BaseModel):
    program: str | None = None


@router.post("/run")
def scheduled_run(body: RunRequest):
    if not body.program or not isinstance(body.program, str):
        raise HTTPException(status_code=422, detail={"error": "program is required", "code": "invalid_program"})
    return run_schedule(program=body.program)
'''
if '"/run"' not in t:
    t = t.rstrip() + "\n" + NEW_ROUTE

runner = wt / 'src/scheduled_runner.py'
if not runner.is_file():
    runner.write_text(
        '"""Scheduled runner (reference stub for the harness gate)."""\n\n\n'
        'def run_schedule(program: str) -> dict:\n'
        '    return {"status": "scheduled", "program": program}\n')

p.write_text(t)
print("refimpl applied")
