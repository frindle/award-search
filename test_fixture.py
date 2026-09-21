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


def _case_unknown_toggle():
    c = TestClient(app_module.app, follow_redirects=False)
    r = c.post("/scheduled/sched_doesnotexist/toggle")
    return (r.status_code, "/scheduled?error=not_found" in r.headers.get("location", ""))


def _case_unknown_delete():
    c = TestClient(app_module.app, follow_redirects=False)
    r = c.post("/scheduled/sched_doesnotexist/delete")
    return (r.status_code, "/scheduled?error=not_found" in r.headers.get("location", ""))


def _case_unknown_run():
    c = TestClient(app_module.app, follow_redirects=False)
    r = c.post("/scheduled/sched_doesnotexist/run")
    return (r.status_code, "/scheduled?error=not_found" in r.headers.get("location", ""))


def _case_lifecycle():
    # Exercises create -> edit page -> update -> toggle -> delete against a
    # single schedule, so the id-lookup, mutation and persistence paths for
    # each of those routes actually run (not just the unknown-id branches).
    c = TestClient(app_module.app, follow_redirects=False)
    target.STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if target.STORE_PATH.exists():
        target.STORE_PATH.unlink()

    r1 = c.post("/scheduled/save", data={
        "origins": "SFO", "destinations": "NRT",
        "date_ranges": "2026-05-01",
        "interval_hours": "24",
        "filter_airlines": "UA, NH",
        "max_points": "60000",
        "max_taxes": "50",
    })
    schedules = target._load_schedules()
    sid = schedules[0]["id"] if schedules else None

    r_edit = c.get(f"/scheduled/{sid}/edit") if sid else None
    edit_ok = bool(r_edit is not None and r_edit.status_code == 200
                   and "SFO" in r_edit.text and "60000" in r_edit.text)

    r_update = c.post("/scheduled/save", data={
        "id": sid or "",
        "origins": "SFO", "destinations": "HND",
        "interval_hours": "12",
    })
    updated = target._load_schedules()
    update_ok = bool(sid and any(
        s["id"] == sid and s["destinations"] == ["HND"] for s in updated))

    r_toggle = c.post(f"/scheduled/{sid}/toggle") if sid else None
    toggled = target._load_schedules()
    toggle_ok = bool(sid and any(
        s["id"] == sid and s["enabled"] is False for s in toggled))

    r_delete = c.post(f"/scheduled/{sid}/delete") if sid else None
    remaining = target._load_schedules()
    delete_ok = bool(sid and not any(s["id"] == sid for s in remaining))

    return (r1.status_code, edit_ok, update_ok, r_toggle is not None and r_toggle.status_code == 303,
            toggle_ok, r_delete is not None and r_delete.status_code == 303, delete_ok)


def _case_malformed_store():
    # The store file can hold a dict without a "schedules" list (e.g. an old
    # format or partial write) or a non-list/non-dict value; both must fall
    # back to an empty schedule set rather than crashing the list route.
    c = TestClient(app_module.app, follow_redirects=False)
    target.STORE_PATH.parent.mkdir(parents=True, exist_ok=True)

    target.STORE_PATH.write_text('{"other": "x"}')
    r_dict_no_key = c.get("/scheduled")

    target.STORE_PATH.write_text('"not-a-list-or-dict"')
    r_bad_type = c.get("/scheduled")

    target.STORE_PATH.unlink()
    return (r_dict_no_key.status_code, r_bad_type.status_code)


CASES = [
    ("GET /scheduled renders the list page (200, scheduled.html body)", _case_list_page, (200, True)),
    ("POST /scheduled/save with an invalid airport code re-renders the form with an error, not a 500", _case_invalid_airport, (200, True)),
    ("POST /scheduled/save with a valid payload redirects to the saved page and the schedule appears on the list", _case_save_roundtrip, (303, True, 200, True)),
    ("POST /scheduled/save with a malformed date range is rejected with an error message", _case_bad_date_range, (200, True)),
    ("GET /scheduled/unknown-id/edit is a 303 redirect to the error page, not a 500", _case_unknown_edit, (303, True)),
    ("POST /scheduled/unknown-id/toggle is a 303 redirect to the error page, not a 500", _case_unknown_toggle, (303, True)),
    ("POST /scheduled/unknown-id/delete is a 303 redirect to the error page, not a 500", _case_unknown_delete, (303, True)),
    ("POST /scheduled/unknown-id/run is a 303 redirect to the error page, not a 500", _case_unknown_run, (303, True)),
    ("create -> edit -> update -> toggle -> delete lifecycle actually mutates the store",
     _case_lifecycle, (303, True, True, True, True, True, True)),
    ("a store file with no schedules list, or a non-list/non-dict value, degrades to an empty list instead of a 500",
     _case_malformed_store, (200, 200)),
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
