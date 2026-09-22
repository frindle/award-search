#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s5-everything-that-renders

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

The target imports `..scheduled_runner` and `..transfer_partners`, which do not
exist in this worktree yet -- so the reference also lands minimal versions of
those two modules (the gate reverts everything, so nothing leaks into sibling
slices), then rewrites scheduled_routes.py so every route that renders returns
TEMPLATES.TemplateResponse.
"""
import pathlib

wt = pathlib.Path(__file__).resolve().parent if len(__argv := __import__("sys").argv) <= 1 else pathlib.Path(__import__("sys").argv[1])

RUNNER = '''"""Scheduled runner: executes an award-program schedule (reference stub)."""


def run_schedule(program):
    return {"program": program, "status": "ok", "flights_found": 3}
'''

PARTNERS = '''"""Transfer partners for award programs (reference stub data)."""

_PARTNERS = [
    {"code": "AA", "name": "American Airlines", "programs": ["AAdvantage"]},
    {"code": "DL", "name": "Delta Air Lines", "programs": ["SkyMiles"]},
]


def list_partners():
    return [dict(p) for p in _PARTNERS]
'''

ROUTES = '''"""Scheduled-routes Web UI routes: transfer partners for award programs."""
from pydantic import BaseModel

from fastapi import APIRouter, HTTPException, Request

from ..scheduled_runner import run_schedule
from ..transfer_partners import list_partners


class RunRequest(BaseModel):
    program: str | None = None

router = APIRouter(prefix="/api/scheduled")

TEMPLATES = None


def init(templates):
    global TEMPLATES
    TEMPLATES = templates


@router.get("/templates")
def scheduled_templates(request: Request):
    if TEMPLATES is None:
        raise HTTPException(status_code=503, detail={"error": "templates not initialized"})
    return TEMPLATES.TemplateResponse("scheduled.html", {"request": request, "templates": []})


@router.get("/partners")
def scheduled_partners(request: Request):
    if TEMPLATES is None:
        raise HTTPException(status_code=503, detail={"error": "templates not initialized"})
    return TEMPLATES.TemplateResponse("scheduled.html", {"request": request, "partners": list_partners()})


@router.get("/partners/{code}")
def scheduled_partner(request: Request, code: str):
    for partner in list_partners():
        if partner["code"].lower() == code.lower():
            return TEMPLATES.TemplateResponse("scheduled.html", {"request": request, "partner": dict(partner)})
    raise HTTPException(status_code=404, detail={"error": "partner not found", "code": code})


@router.post("/run")
def scheduled_run(request: Request, body: RunRequest):
    if not body.program:
        raise HTTPException(status_code=422, detail={"error": "program is required", "code": "invalid_program"})
    result = run_schedule(program=body.program)
    return TEMPLATES.TemplateResponse("scheduled_result.html", {"request": request, "result": result})
'''

(wt / 'src').mkdir(parents=True, exist_ok=True)
(wt / 'src' / 'scheduled_runner.py').write_text(RUNNER)
(wt / 'src' / 'transfer_partners.py').write_text(PARTNERS)
p = wt / 'src' / 'webui' / 'scheduled_routes.py'
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(ROUTES)
print("refimpl applied")
