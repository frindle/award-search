"""Adversarial fixture for: aw-sched-routes-s17-get-api-airport-groups-l

INTEGRATION fixture: drives the real router through fastapi.testclient and
asserts status codes AND response bodies. The endpoint under test is
GET /api/airport-groups -> list_groups() from src.airport_groups, so a
plausible-but-wrong implementation (wrong path, wrapped body like
{"groups": [...]}, hardcoded data, or a 500) must fail here while the
reference impl passes.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import sys
import types
from pathlib import Path

# --- load the target module with its relative imports resolved -------------
# scheduled_routes.py does `from ..scheduled_runner import run_schedule` and
# `from ..transfer_partners import list_partners`; those modules are not part
# of this slice, so register lightweight stand-ins under their real dotted
# names BEFORE exec (the import system checks sys.modules first). The fake
# `src` package carries a __path__ so the REAL src.airport_groups still loads
# from disk -- we compare against its actual list_groups(), not a copy.
_SRC = str(Path("src").resolve())

if "src" not in sys.modules:
    _pkg = types.ModuleType("src")
    _pkg.__path__ = [_SRC]
    sys.modules["src"] = _pkg
_webui = types.ModuleType("src.webui")
_webui.__path__ = [str(Path("src/webui").resolve())]
sys.modules.setdefault("src", _pkg)
sys.modules["src.webui"] = _webui

_runner = types.ModuleType("src.scheduled_runner")
_runner.run_schedule = lambda **kw: {}
sys.modules.setdefault("src.scheduled_runner", _runner)
_partners = types.ModuleType("src.transfer_partners")
_partners.list_partners = lambda: []
sys.modules.setdefault("src.transfer_partners", _partners)

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so dataclasses/annotation resolution through
# sys.modules[cls.__module__] would see None and die at IMPORT for a reason
# that has nothing to do with the task.
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

import src.airport_groups as airport_groups  # real module, from disk

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient


def _build_app():
    """Mount every router the target defines (the /api-prefixed one and the
    pre-existing /api/scheduled one) on a bare app."""
    app = FastAPI()
    for name in dir(target):
        obj = getattr(target, name)
        if isinstance(obj, APIRouter):
            app.include_router(obj)
    return app


def _get(path):
    client = TestClient(_build_app())
    r = client.get(path)
    try:
        body = r.json()
    except ValueError:
        body = r.text
    return (r.status_code, body)



CASES = [
    # The endpoint exists at the exact path and returns list_groups() verbatim.
    ("GET /api/airport-groups -> 200 with list_groups() body",
     lambda: _get("/api/airport-groups"),
     (200, airport_groups.list_groups())),

    # Body is a bare JSON array of {code,name,airports} dicts sorted by code --
    # catches a {"groups": [...]} wrapper or hardcoded/unsorted data.
    ("body entries are code/name/airports dicts in sorted order",
     lambda: (lambda b: all(
         isinstance(e, dict) and set(e) == {"code", "name", "airports"}
         for e in b) and [e["code"] for e in b] == sorted(e["code"] for e in b)
     )(_get("/api/airport-groups")[1]),
     True),

    # The JFK group is present with its exact shape (pins real data, not a stub).
    ("JFK group present with name and airports list",
     lambda: next((e for e in _get("/api/airport-groups")[1] if e.get("code") == "JFK"), None),
     {"code": "JFK", "name": "New York (JFK)", "airports": ["JFK"]}),

    # Regression half: the pre-existing /api/scheduled routes must keep working.
    ("regression: GET /api/scheduled/templates still -> 200 {templates: []}",
     lambda: _get("/api/scheduled/templates"),
     (200, {"templates": []})),
]


def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
        print("  A generated scaffold is not a verify. Author the cases in "
              "test_fixture.py.")
        return 1
    fails = 0
    for desc, thunk, want in CASES:
        try:
            got = thunk()
        except Exception as e:
            print("  FAIL {} -- raised {}: {}".format(desc, type(e).__name__, e))
            fails += 1
            continue
        if got != want:
            print("  FAIL {} -- got {!r}, want {!r}".format(desc, got, want))
            fails += 1
    print("  {}/{} case(s) passed".format(len(CASES) - fails, len(CASES)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
