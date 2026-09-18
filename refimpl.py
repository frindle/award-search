#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s2-from-transfer-partners-i

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES the
spec (a refimpl that goes green while a "Must contain" literal is absent means
the verify is benign).

Writes the complete solution into src/webui/scheduled_routes.py. The data
module src/transfer_partners.py already exists in the worktree (baseline), so
only the target file is written here.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
p = wt / "src/webui/scheduled_routes.py"
p.parent.mkdir(parents=True, exist_ok=True)

SOLUTION = '''"""Scheduled-routes API router: transfer-partner endpoints for the Web UI."""
from fastapi import APIRouter, HTTPException

from ..transfer_partners import list_partners

router = APIRouter(prefix="/api/scheduled", tags=["scheduled"])


@router.get("/partners")
def scheduled_partners():
    """Transfer partners available on scheduled routes."""
    return {"partners": list_partners()}


@router.get("/partners/{code}")
def scheduled_partner(code: str):
    for partner in list_partners():
        if partner["code"].lower() == code.lower():
            return partner
    raise HTTPException(status_code=404, detail={"error": "partner not found", "code": code})
'''

p.write_text(SOLUTION)
print("refimpl applied")
