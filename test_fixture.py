"""Adversarial fixture for: aw-sched-routes-s10-get-scheduled-sched-id-e

INTEGRATION fixture: drives the real router through FastAPI's TestClient and
asserts status codes AND response bodies. The template engine is stubbed to a
JSON echo of (template name, context) so cases can assert exactly what the
route passed to the renderer -- including mode='edit' vs 'new'.

The target does relative imports (`..scheduled_runner`, `..transfer_partners`),
so it must be loaded inside a package context. The parent packages are stubbed
WITHOUT executing their real __init__ (src/__init__.py pulls in cli deps), and
the two sibling modules this worktree does not ship are stubbed too.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent


def _stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


pkg_src = _stub("src")
pkg_src.__path__ = [str(ROOT / "src")]
pkg_webui = _stub("src.webui")
pkg_webui.__path__ = [str(ROOT / "src" / "webui")]
_stub("src.scheduled_runner", run_schedule=lambda **kw: {"ran": kw})
_stub("src.transfer_partners", list_partners=lambda: [])

# REGISTER BEFORE EXEC so the module has a sys.modules entry under its real name.
spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", str(ROOT / "src" / "webui" / "scheduled_routes.py"))
target = importlib.util.module_from_spec(spec)
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


class FakeTemplates:
    """Render as a JSON echo of the template name + context (minus `request`),
    so cases assert on exactly what the route handed to the renderer."""

    def TemplateResponse(self, name, context):
        payload = {"template": name}
        for k, v in context.items():
            if k != "request":
                payload[k] = v
        return JSONResponse(payload)


app = FastAPI()
app.include_router(target.router)
target.init(FakeTemplates())
client = TestClient(app)

SEED = {
    "s-1": {
        "id": "s-1",
        "name": "JFK-LAX business",
        "origins": ["JFK"],
        "destinations": ["LAX"],
        "cabins": ["business"],
        "programs": ["united"],
    },
}


def _seed():
    target.set_schedules(SEED)


def _get(path):
    r = client.get(path)
    return {"status": r.status_code, "body": r.json()}


FULL_SCHEDULE_S1 = {
    "id": "s-1",
    "name": "JFK-LAX business",
    "origins": ["JFK"],
    "destinations": ["LAX"],
    "date_ranges": [],
    "cabins": ["business"],
    "programs": ["united"],
    "transfer_partners": [],
    "filters": {"airlines": [], "max_points": None, "max_taxes": None},
    "interval_hours": 6,
    "notify_pushover": False,
    "enabled": True,
}

EMPTY_SCHEDULE = {
    "id": None,
    "name": "",
    "origins": [],
    "destinations": [],
    "date_ranges": [],
    "cabins": [],
    "programs": [],
    "transfer_partners": [],
    "filters": {"airlines": [], "max_points": None, "max_taxes": None},
    "interval_hours": 6,
    "notify_pushover": False,
    "enabled": True,
}


CASES = [
    # Runs FIRST, before any set_schedules call: exercises the module-level
    # SCHEDULES store in its initial (empty) state. If the `SCHEDULES`
    # declaration is missing, the route handler raises NameError -> 500, and
    # this case fails even though later cases would re-create the global via
    # set_schedules and pass.
    ("unseeded store: unknown sched_id on a fresh module still gets a clean 404 (not 500)",
     lambda: _get("/api/scheduled/scheduled/ghost/edit"),
     {"status": 404, "body": {
         "detail": {"error": "schedule not found", "sched_id": "ghost"},
     }}),

    ("GET /api/scheduled/s-1/edit renders scheduled_edit.html with the loaded schedule and mode='edit'",
     lambda: (_seed(), _get("/api/scheduled/scheduled/s-1/edit"))[1],
     {"status": 200, "body": {
         "template": "scheduled_edit.html",
         "mode": "edit",
         "schedule": FULL_SCHEDULE_S1,
         "programs": [],
         "partners": [],
         "error": None,
     }}),

    ("unknown sched_id -> 404 with the schedule-not-found detail (not a 500)",
     lambda: (_seed(), _get("/api/scheduled/scheduled/nope/edit"))[1],
     {"status": 404, "body": {
         "detail": {"error": "schedule not found", "sched_id": "nope"},
     }}),

    ("sparse schedule (empty dict) still renders with fully defaulted normalized shape",
     lambda: (target.set_schedules({"s-2": {}}), _get("/api/scheduled/scheduled/s-2/edit"))[1],
     {"status": 200, "body": {
         "template": "scheduled_edit.html",
         "mode": "edit",
         "schedule": EMPTY_SCHEDULE,
         "programs": [],
         "partners": [],
         "error": None,
     }}),

    ("regression: GET /api/scheduled/new still renders mode='new' with the empty schedule",
     lambda: (_seed(), _get("/api/scheduled/scheduled/new"))[1],
     {"status": 200, "body": {
         "template": "scheduled_edit.html",
         "mode": "new",
         "schedule": EMPTY_SCHEDULE,
         "programs": [],
         "partners": [],
         "error": None,
     }}),
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
