"""Adversarial fixture for: aw-sched-routes-s4-init

INTEGRATION fixture: drives the real router through fastapi.testclient,
asserting status codes AND response bodies. The sibling modules
(src.transfer_partners, src.scheduled_runner) are stubbed in sys.modules
BEFORE the target is exec'd so relative imports resolve deterministically and
the fake run_schedule keeps POST /run honest -- a plausible-but-wrong impl that
hardcodes responses without touching module state fails case 2 (identity), and
one that appends instead of replacing fails case 3.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import pathlib
import sys
import types


def _pkg(name):
    m = types.ModuleType(name)
    m.__path__ = []
    sys.modules[name] = m
    return m


_pkg("src")
_pkg("src.webui")

_TP = types.ModuleType("src.transfer_partners")
_TP.list_partners = lambda: [
    {"code": "UA", "name": "United"},
    {"code": "DL", "name": "Delta"},
]
sys.modules["src.transfer_partners"] = _TP


def fake_run_schedule(program):
    return {"status": "scheduled", "program": program, "job_id": "job-123"}


_sr = types.ModuleType("src.scheduled_runner")
_sr.run_schedule = fake_run_schedule
sys.modules["src.scheduled_runner"] = _sr

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", pathlib.Path("src/webui/scheduled_routes.py"))
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC so the module is resolvable by name during exec.
sys.modules[spec.name] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.router)
client = TestClient(app)


def _get(path):
    r = client.get(path)
    return (r.status_code, r.json())


CASES = [
    ("before init(), TEMPLATES is the empty list and GET /templates reflects it",
     lambda: (target.TEMPLATES, _get("/api/scheduled/templates")),
     ([], (200, {"templates": []}))),

    ("init(templates) sets the SAME module-level object -- identity, not a copy or local",
     lambda: (lambda ts: target.init(ts) or (target.TEMPLATES is ts, list(target.TEMPLATES)))([{"id": "t1"}, {"id": "t2"}]),
     (True, [{"id": "t1"}, {"id": "t2"}])),

    ("init() REPLACES the templates -- a second call does not append to the first",
     lambda: (lambda a, b: target.init(a) or target.init(b) or list(target.TEMPLATES))([{"id": "a"}], [{"id": "b"}, {"id": "c"}]),
     [{"id": "b"}, {"id": "c"}]),

    ("GET /templates after init() returns the current templates verbatim",
     lambda: (lambda ts: target.init(ts) or _get("/api/scheduled/templates"))([{"id": "t9"}]),
     (200, {"templates": [{"id": "t9"}]})),

    ("regression: GET /partners still returns the partner list and POST /run keeps its 422 shape",
     lambda: (_get("/api/scheduled/partners"),
              (lambda r: (r.status_code, r.json()))(client.post("/api/scheduled/run", json={}))),
     ((200, {"partners": [{"code": "UA", "name": "United"}, {"code": "DL", "name": "Delta"}]}),
      (422, {"detail": {"error": "program is required", "code": "invalid_program"}}))),
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
