#!/usr/bin/env python3
"""Reference impl for: aw-app-wiring-s3-from-import-scheduled-ro

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

The wiring target `from . import scheduled_routes` only works if the module it
imports exists in this worktree. It does not yet (it lands on the sibling slice
branch), so this reference also materialises the two modules the route depends
on -- src/transfer_partners.py and src/webui/scheduled_routes.py -- matching
the canonical content from the slice chain, then adds the import line to
src/webui/app.py. The DISPATCHED model is told only to edit app.py; if the
modules are missing in its tree it must create them too (TASK.md says so).
"""
import pathlib

wt = pathlib.Path(__file__).resolve().parent
if len(__import__("sys").argv) > 1:
    wt = pathlib.Path(__import__("sys").argv[1])

TRANSFER_PARTNERS = '''\
"""Transfer-partner lookup for award programs (scheduled-routes UI)."""


def list_partners():
    """Return the transfer partners as a list of {code, name} dicts."""
    return [
        {"code": "AA", "name": "American Airlines"},
        {"code": "AC", "name": "Air Canada"},
        {"code": "AS", "name": "Alaska Airlines"},
        {"code": "DL", "name": "Delta Air Lines"},
    ]
'''

SCHEDULED_ROUTES = '''\
"""Scheduled-routes Web UI routes: transfer partners for award programs."""
from fastapi import APIRouter, HTTPException

from ..transfer_partners import list_partners

router = APIRouter(prefix="/api/scheduled")


@router.get("/partners")
def scheduled_partners():
    return {"partners": list_partners()}


@router.get("/partners/{code}")
def scheduled_partner(code: str):
    for partner in list_partners():
        if partner["code"].lower() == code.lower():
            return dict(partner)
    raise HTTPException(status_code=404, detail={"error": "partner not found", "code": code})
'''

app_path = wt / 'src/webui/app.py'
t = app_path.read_text()

if 'from . import scheduled_routes' in t:
    print("refimpl applied (import already present)")
else:
    anchor = "from ..deeplinks import flight_links, seats_aero_url"
    assert anchor in t, "app.py anchor not found -- did the target change?"
    app_path.write_text(t.replace(anchor, anchor + "\nfrom . import scheduled_routes", 1))

tp = wt / 'src/transfer_partners.py'
if not tp.exists():
    tp.write_text(TRANSFER_PARTNERS)

sr = wt / 'src/webui/scheduled_routes.py'
if not sr.exists():
    sr.write_text(SCHEDULED_ROUTES)

print("refimpl applied")
