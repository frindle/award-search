#!/usr/bin/env python3
"""Reference impl for: aw-sched-routes-s1-from-airport-groups-impo

The gate applies this, runs the verify, and reverts it. It proves two things at
once: the task is SATISFIABLE as specified, and the verify actually ENFORCES
the spec (a refimpl that goes green while a "Must contain" literal is absent
means the verify is benign).

Writes the airport_groups data module (list_groups / expand_codes) and adds
the two scheduled-groups routes to src/webui/scheduled_routes.py, preserving
the existing transfer-partner routes.
"""
import pathlib
import sys

wt = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

# --- airport_groups data module (list_groups / expand_codes) ---------------
ag = wt / "src" / "airport_groups.py"
if not ag.exists():
    ag.write_text(
        '"""Airport groups: named sets of airport codes for award programs."""\n'
        "\n"
        "GROUPS = {\n"
        '    "Delta": ["ATL", "DTW", "SLC"],\n'
        '    "United": ["ORD", "IAH", "EWR"],\n'
        '    "Alaska": ["SEA", "ANC"],\n'
        "}\n"
        "\n"
        "\n"
        "def list_groups():\n"
        '    """Return the group names, sorted."""\n'
        "    return sorted(GROUPS)\n"
        "\n"
        "\n"
        "def expand_codes(name):\n"
        '    """Expand a group name to its airport codes; None if unknown."""\n'
        "    for g, codes in GROUPS.items():\n"
        "        if g.lower() == str(name).lower():\n"
        "            return list(codes)\n"
        "    return None\n"
    )

# --- scheduled_routes.py: add the groups routes -----------------------------
p = wt / 'src/webui/scheduled_routes.py'
t = p.read_text()

OLD = """from ..transfer_partners import list_partners"""
NEW = """from ..airport_groups import list_groups, expand_codes
from ..transfer_partners import list_partners"""
assert OLD in t and "list_groups" not in t, \
    "refimpl anchor not found or already applied -- did the target change?"
t = t.replace(OLD, NEW, 1)

ROUTES = '''

@router.get("/groups")
def scheduled_groups():
    return {"groups": [{"name": g, "codes": expand_codes(g)} for g in list_groups()]}


@router.get("/groups/{name}")
def scheduled_group(name: str):
    codes = expand_codes(name)
    if codes is None:
        raise HTTPException(status_code=404, detail={"error": "group not found", "name": name})
    return {"name": name, "codes": codes}
'''
if '"/groups"' not in t:
    t = t.rstrip("\n") + "\n" + ROUTES
p.write_text(t)
print("refimpl applied")
