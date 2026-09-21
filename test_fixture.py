"""Adversarial fixture for: scheduled_routes

Integration fixture: drives the real FastAPI app through TestClient, asserting
status codes AND response bodies. The target module must expose an APIRouter
plus init(templates) that stores the Jinja2Templates instance; the routes back
the existing scheduled.html / scheduled_edit.html / scheduled_result.html
templates.

Each case: (description, callable_returning_actual, expected)
"""
import sys
import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("target", 'src/webui/scheduled_routes.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
spec.loader.exec_module(target)

# Redirect persistence away from the real credentials/ dir before any route runs.
_TMP_STORE = Path(tempfile.mkdtemp(prefix="sched_fixture_")) / "scheduled.json"
target.STORE_PATH = _TMP_STORE

from fastapi.testclient import TestClient  # noqa: E402
import src.webui.app as app_module  # noqa: E402

# app.py does not wire this module up yet (that's a separate, not-yet-landed
# slice); wire it here so the fixture can exercise the routes standalone.
target.init(app_module.templates)
app_module.app.include_router(target.router)


def _case_list_page():
    c = TestClient(app_module.app, follow_redirects=False)
    r = c.get("/scheduled")
    return (r.status_code, "Scheduled Award Searches" in r.text)


def _case_invalid_airport():
    c = TestClient(app_module.app, follow_redirects=False)
    r = c.post("/scheduled/save", data={
        "origins": "JFKK", "destinations": "LAX", "interval_hours": "6"})
    return (r.status_code, "Invalid airport code" in r.text)


def _case_save_roundtrip():
    c = TestClient(app_module.app, follow_redirects=False)
    r1 = c.post("/scheduled/save", data={
        "origins": "JFK, LGA", "destinations": "LAX",
        "date_ranges": "2026-03-01; 2026-04-01-2026-04-15",
        "interval_hours": "12"})
    r2 = c.get("/scheduled")
    return (r1.status_code, "/scheduled?saved=1" in r1.headers.get("location", ""),
            r2.status_code, "JFK" in r2.text and "LAX" in r2.text)


def _case_bad_date_range():
    c = TestClient(app_module.app, follow_redirects=False)
    r = c.post("/scheduled/save", data={
        "origins": "JFK", "destinations": "LAX", "date_ranges": "not-a-date"})
    return (r.status_code, "Invalid date range" in r.text)


def _case_unknown_edit():
    c = TestClient(app_module.app, follow_redirects=False)
    r = c.get("/scheduled/sched_doesnotexist/edit")
    return (r.status_code, "/scheduled?error=not_found" in r.headers.get("location", ""))


CASES = [
    ("GET /scheduled renders the list page (200, scheduled.html body)", _case_list_page, (200, True)),
    ("POST /scheduled/save with an invalid airport code re-renders the form with an error, not a 500", _case_invalid_airport, (200, True)),
    ("POST /scheduled/save with a valid payload redirects to the saved page and the schedule appears on the list", _case_save_roundtrip, (303, True, 200, True)),
    ("POST /scheduled/save with a malformed date range is rejected with an error message", _case_bad_date_range, (200, True)),
    ("GET /scheduled/unknown-id/edit is a 303 redirect to the error page, not a 500", _case_unknown_edit, (303, True)),
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
