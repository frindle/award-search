#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s17-get-api-airport-groups-l

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
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

# 1) import list_groups from the airport-groups module (preserve existing imports).
OLD_IMPORTS = r"""from ..scheduled_runner import run_schedule
from ..transfer_partners import list_partners"""
NEW_IMPORTS = OLD_IMPORTS + "\nfrom ..airport_groups import list_groups"
assert OLD_IMPORTS in t, "import anchor not found -- did the target change?"
t = t.replace(OLD_IMPORTS, NEW_IMPORTS, 1)

# 2) add GET /api/airport-groups on a new /api-prefixed router (the existing
#    `router` is prefixed /api/scheduled, so it cannot serve this path).
OLD_ANCHOR = r'''@router.get("/partners")
def scheduled_partners():'''
NEW_BLOCK = r'''api_router = APIRouter(prefix="/api")


@api_router.get("/airport-groups")
def airport_groups_list():
    return list_groups()


@router.get("/partners")
def scheduled_partners():'''
assert OLD_ANCHOR in t, "route anchor not found -- did the target change?"
t = t.replace(OLD_ANCHOR, NEW_BLOCK, 1)

p.write_text(t)
print("refimpl applied")
