"""Adversarial fixture for: aw-sched-routes-s19-get-api-scheduled-sched

>>> THE ONE THING THE GENERATOR CANNOT WRITE FOR YOU <<<

CASES is empty and the verify FAILS until you fill it in. That is deliberate.
A generator can emit a verify that DISCRIMINATES (fails at baseline, passes on
a fix). It cannot decide whether the verify is RELEVANT -- whether it tests the
property the task actually asked for. A benign case passes broken work.

Pick inputs that separate "did the job" from "made the test go green":
  * the exact boundary the defect is about, and one on each side of it
  * the degenerate inputs (missing key, None, empty, wrong type) that must NOT
    raise
  * at least one case that a plausible WRONG fix would fail
  * the regression half: things that already work and must keep working

Each case: (description, callable_returning_actual, expected)

This is a web service, so the cases drive the REAL app through TestClient:
status codes AND response bodies. The target uses relative imports, so it is
loaded as its real package module; only sibling modules that do not exist in
this slice are stubbed before import (they are unrelated to this route).
"""
import sys
import types

sys.path.insert(0, ".")  # worktree root == cwd when verify.sh runs us

for _name, _attrs in {
    "src.scheduled_runner": {"run_schedule": lambda **kw: {}},
    "src.transfer_partners": {"list_partners": lambda: []},
}.items():
    try:
        __import__(_name)
    except Exception:
        _mod = types.ModuleType(_name)
        for _k, _v in _attrs.items():
            setattr(_mod, _k, _v)
        sys.modules[_name] = _mod

import src.webui.scheduled_routes as target  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def _app():
    app = FastAPI()
    app.include_router(target.router)
    return TestClient(app)


def _seed(schedules):
    target.set_schedules(dict(schedules))


SCHED_A = {
    "id": "sched-a",
    "name": "Transatlantic",
    "origins": ["JFK", "LAX"],
    "destinations": ["LHR"],
    "date_ranges": [{"start": "2026-05-01", "end": "2026-05-31"}],
    "programs": ["united", "delta"],
}

SCHED_B = {
    "id": "sched-b",
    "name": "No explicit programs",
    "origins": ["SFO"],
    "destinations": ["NRT"],
    "date_ranges": [{"start": "2026-06-15", "end": None}],
    "programs": [],
}


def _preview(sched_id):
    r = _app().get("/api/scheduled/{}/preview".format(sched_id))
    return (r.status_code, r.json())


def case_happy():
    _seed({"sched-a": dict(SCHED_A)})
    return _preview("sched-a")


def case_fallback_programs():
    _seed({"sched-b": dict(SCHED_B)})
    return _preview("sched-b")


from src.search.programs.base import load_programs_config as _lpc  # noqa: E402

WANT_FALLBACK = (200, {
    "legs": [{"origin": "SFO", "destination": "NRT",
              "start_date": "2026-06-15", "end_date": None}],
    "leg_count": 1,
    "programs": sorted(_lpc().keys()),
})


def case_not_found():
    _seed({"sched-a": dict(SCHED_A)})
    return _preview("does-not-exist")


def case_regression_templates():
    target.init([])
    r = _app().get("/api/scheduled/templates")
    return (r.status_code, r.json())



CASES = [
    ("2 origins x 1 destination x 1 date range -> exact legs, leg_count=2, own programs",
     case_happy,
     (200, {
         "legs": [
             {"origin": "JFK", "destination": "LHR",
              "start_date": "2026-05-01", "end_date": "2026-05-31"},
             {"origin": "LAX", "destination": "LHR",
              "start_date": "2026-05-01", "end_date": "2026-05-31"},
         ],
         "leg_count": 2,
         "programs": ["delta", "united"],
     })),
    ("empty programs -> falls back to every configured program id",
     case_fallback_programs,
     WANT_FALLBACK),
    ("unknown sched_id -> 404 with 'schedule not found' detail, not a 500",
     case_not_found,
     (404, {"detail": {"error": "schedule not found", "sched_id": "does-not-exist"}})),
    ("regression: existing GET /api/scheduled/templates still works",
     case_regression_templates,
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
