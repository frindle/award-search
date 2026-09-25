"""Adversarial fixture for: aw-sched-routes-s16-render-scheduled-result

Integration fixture: drives the real router through fastapi.testclient,
asserting status codes AND rendered HTML bodies. The route under test must
render 'scheduled_result.html' with {request, schedule, results}:

  * happy path -- a schedule WITH last_results renders each row's values
    (a wrong impl that drops `results` from the context fails here)
  * empty results -- still 200 and shows the template's "no availability"
    branch (an impl that 500s or skips rendering on [] fails here)
  * unknown schedule id -- 404 with the standard error shape, NOT a 500
  * regression -- an existing route (/api/scheduled/templates) still works

Each case: (description, callable_returning_actual, expected)
"""
import sys
import types
import importlib.util

# The target uses RELATIVE imports (`from ..scheduled_runner import ...`), so it
# must be loaded inside a real package context -- loading it as a bare top-level
# module raises "attempted relative import with no known parent package". Build
# synthetic `src` and `src.webui` packages pointing at the on-disk dirs, then load
# scheduled_routes under its dotted name. The two sibling modules it imports are
# not part of this slice, so stub them in sys.modules first.
for _name in ("src.scheduled_runner", "src.transfer_partners"):
    if _name not in sys.modules:
        _mod = types.ModuleType(_name)
        sys.modules[_name] = _mod
sys.modules["src.scheduled_runner"].run_schedule = lambda **kw: []
sys.modules["src.transfer_partners"].list_partners = lambda: []

for _pkg, _path in (("src", "src"), ("src.webui", "src/webui")):
    if _pkg not in sys.modules:
        _pm = types.ModuleType(_pkg)
        _pm.__path__ = [_path]
        sys.modules[_pkg] = _pm

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", 'src/webui/scheduled_routes.py',
    submodule_search_locations=None)
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["src.webui.scheduled_routes"] = target
spec.loader.exec_module(target)

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from starlette.templating import Jinja2Templates  # noqa: E402


def _formatnumber(value):
    if value is None:
        return "0"
    return f"{value:,}"


_templates = Jinja2Templates(directory="src/webui/templates", autoescape=True)
_templates.env.filters["formatnumber"] = _formatnumber

# init() takes a Jinja2Templates instance (the same object app.py passes in);
# the module's TEMPLATES.TemplateResponse calls then render real templates.
target.init(_templates)
target.set_schedules({
    "s1": {
        "id": "s1",
        "name": "JFK-LAX saver",
        "origins": ["JFK"],
        "destinations": ["LAX"],
        "last_results": [
            {"date": "2026-10-01", "origin": "JFK", "destination": "LAX",
             "cabin": "business", "source": "AA", "airlines": ["AA"],
             "cost": 12345, "taxes": 12.5, "seats": 3, "direct": True,
             "booking_url": "https://example.com/book/abc"},
        ],
    },
    "s-empty": {
        "id": "s-empty",
        "name": "",
        "origins": ["SFO"],
        "destinations": ["SEA"],
        "last_results": [],
    },
})

app = FastAPI()
app.include_router(target.router)
client = TestClient(app, raise_server_exceptions=False)


# The harness compares got == want per case. For body-content checks we return
# a tuple of (status, *booleans) so the comparison stays exact and readable in
# failure output.


def _result_case(path):
    resp = client.get(path)
    text = resp.text
    return (resp.status_code,
            "JFK" in text, "LAX" in text, "business" in text,
            "12,345" in text, "$12.50" in text, "direct" in text,
            "example.com/book/abc" in text)


def _empty_case(path):
    resp = client.get(path)
    return (resp.status_code,
            "No availability matched this schedule's alert limits." in resp.text)


def _missing_case(path):
    resp = client.get(path)
    return (resp.status_code,
            "schedule not found" in resp.text and "nope-404" in resp.text)


def _regression_case():
    # /partners returns plain data (list_partners is stubbed to []), so this
    # pins that the router still serves its existing JSON routes untouched.
    resp = client.get("/api/scheduled/partners")
    return (resp.status_code, resp.json())


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    ("happy path: 200 + every results-row value rendered from context",
     lambda: _result_case("/api/scheduled/s1/result"),
     (200, True, True, True, True, True, True, True)),

    ("empty last_results: still 200 and shows the no-availability branch",
     lambda: _empty_case("/api/scheduled/s-empty/result"),
     (200, True)),

    ("unknown schedule id -> 404 with standard error shape, not a 500",
     lambda: _missing_case("/api/scheduled/nope-404/result"),
     (404, True)),

    ("regression: existing /api/scheduled/partners JSON route still works",
     lambda: _regression_case(),
     (200, {"partners": []})),
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
