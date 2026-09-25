"""Adversarial fixture for: aw-sched-routes-s11-preserves-created-at-las

Integration fixture: drives the real router through fastapi.testclient,
asserting status codes AND response bodies. The property under test: an edit
(POST /api/scheduled/{sched_id}) PRESERVES created_at/last_checked/
last_results/notified_keys from the existing record while applying submitted
fields. A naive "replace the record with the body" impl passes none of these.

The target module uses relative imports (..scheduled_runner, ..transfer_partners),
so those two modules are stubbed in sys.modules BEFORE exec -- the fixture only
exercises the routes it tests and never calls into them.
"""
import sys
import importlib.util
from types import ModuleType

# The target uses relative imports (..scheduled_runner, ..transfer_partners),
# so it must load INSIDE a package. Register bare parent packages and stub the
# two sibling modules in sys.modules BEFORE exec -- no filesystem writes, and
# the fixture never calls into those siblings.
for _pkg in ("src", "src.webui"):
    if _pkg not in sys.modules:
        _m = ModuleType(_pkg)
        _m.__path__ = []  # mark as a package so relative imports resolve
        sys.modules[_pkg] = _m
for _name, _attr in (("src.scheduled_runner", "run_schedule"),
                     ("src.transfer_partners", "list_partners")):
    if _name not in sys.modules:
        _mod = ModuleType(_name)
        setattr(_mod, _attr, lambda *a, **k: None)
        sys.modules[_name] = _mod

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", 'src/webui/scheduled_routes.py')
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


def _app_with(schedule):
    app = FastAPI()
    app.include_router(target.router)
    target.SCHEDULES.clear()
    if schedule is not None:
        target.SCHEDULES["sched_1"] = dict(schedule)
    return TestClient(app)


BASE_RECORD = {
    "id": "sched_1",
    "name": "old name",
    "origins": ["JFK"],
    "destinations": ["LHR"],
    "date_ranges": [{"start": "2026-05-01", "end": None}],
    "cabins": ["business"],
    "programs": ["AA"],
    "transfer_partners": [],
    "filters": {"airlines": [], "max_points": 40000, "max_taxes": None},
    "interval_hours": 6,
    "notify_pushover": False,
    "enabled": True,
    "created_at": "2025-11-30T09:00:00",
    "last_checked": "2026-01-02T08:00:00",
    "last_results": [{"route": "JFK-LHR", "price": 41000}],
    "notified_keys": ["k1", "k2"],
}


def case_edit_preserves_metadata():
    """Full edit: submitted fields applied, metadata preserved verbatim."""
    client = _app_with(BASE_RECORD)
    r = client.post("/api/scheduled/sched_1", json={
        "name": "new name",
        "origins": ["SFO"],
        "destinations": ["NRT"],
        "interval_hours": 12,
        "notify_pushover": True,
    })
    assert r.status_code == 200, (r.status_code, r.text)
    body = r.json()
    sched = body["schedule"]
    return {
        "status": r.status_code,
        "name": sched.get("name"),
        "origins": sched.get("origins"),
        "destinations": sched.get("destinations"),
        "interval_hours": sched.get("interval_hours"),
        "notify_pushover": sched.get("notify_pushover"),
        "created_at": target.SCHEDULES["sched_1"].get("created_at"),
        "last_checked": target.SCHEDULES["sched_1"].get("last_checked"),
        "last_results": target.SCHEDULES["sched_1"].get("last_results"),
        "notified_keys": target.SCHEDULES["sched_1"].get("notified_keys"),
    }


def case_partial_edit_keeps_unsubmitted_fields():
    """Edit with only `name`: every other field (incl. metadata) untouched."""
    client = _app_with(BASE_RECORD)
    r = client.post("/api/scheduled/sched_1", json={"name": "renamed"})
    assert r.status_code == 200, (r.status_code, r.text)
    stored = target.SCHEDULES["sched_1"]
    return {
        "status": r.status_code,
        "name": stored.get("name"),
        "origins": stored.get("origins"),
        "destinations": stored.get("destinations"),
        "filters": stored.get("filters"),
        "enabled": stored.get("enabled"),
        "created_at": stored.get("created_at"),
        "last_checked": stored.get("last_checked"),
        "last_results": stored.get("last_results"),
        "notified_keys": stored.get("notified_keys"),
    }


def case_edit_unknown_schedule_404():
    """Edit of a missing schedule -> 404 with the error shape, not a 500."""
    client = _app_with(BASE_RECORD)
    r = client.post("/api/scheduled/nope", json={"name": "x"})
    return {"status": r.status_code, "detail": r.json().get("detail")}


def case_empty_body_preserves_everything():
    """Empty edit body: record unchanged, metadata intact."""
    client = _app_with(BASE_RECORD)
    r = client.post("/api/scheduled/sched_1", json={})
    assert r.status_code == 200, (r.status_code, r.text)
    stored = target.SCHEDULES["sched_1"]
    return {
        "status": r.status_code,
        "name": stored.get("name"),
        "origins": stored.get("origins"),
        "created_at": stored.get("created_at"),
        "last_results": stored.get("last_results"),
        "notified_keys": stored.get("notified_keys"),
    }


def case_record_without_metadata():
    """Existing record lacking the metadata keys: edit still 200, no crash."""
    client = _app_with({"id": "sched_1", "name": "bare"})
    r = client.post("/api/scheduled/sched_1", json={"origins": ["LAX"]})
    assert r.status_code == 200, (r.status_code, r.text)
    stored = target.SCHEDULES["sched_1"]
    return {
        "status": r.status_code,
        "name": stored.get("name"),
        "origins": stored.get("origins"),
        "created_at": stored.get("created_at"),
        "notified_keys": stored.get("notified_keys"),
    }


def case_edit_normalizes_missing_metadata_keys():
    """Edit of a record LACKING the metadata keys: after saving, the stored
    record carries ALL FOUR metadata keys (created_at/last_checked/
    last_results/notified_keys), even if their values are None/[]. The runner
    relies on those keys being present on every stored record, so a save that
    drops or renames them leaves the store in a shape it cannot read."""
    client = _app_with({"id": "sched_1", "name": "bare"})
    r = client.post("/api/scheduled/sched_1", json={"origins": ["LAX"]})
    assert r.status_code == 200, (r.status_code, r.text)
    stored = target.SCHEDULES["sched_1"]
    return {
        "status": r.status_code,
        "has_created_at": "created_at" in stored,
        "has_last_checked": "last_checked" in stored,
        "has_last_results": "last_results" in stored,
        "has_notified_keys": "notified_keys" in stored,
        "created_at": stored.get("created_at"),
        "last_checked": stored.get("last_checked"),
        "last_results": stored.get("last_results"),
        "notified_keys": stored.get("notified_keys"),
    }


def case_invalid_body_422():
    """Wrong-typed field -> 422 validation error, not a 500."""
    client = _app_with(BASE_RECORD)
    r = client.post("/api/scheduled/sched_1", json={"interval_hours": "not-a-number"})
    return {"status": r.status_code}


CASES = [
    ("edit applies submitted fields and PRESERVES created_at/last_checked/"
     "last_results/notified_keys from the existing record",
     case_edit_preserves_metadata,
     {
         "status": 200,
         "name": "new name",
         "origins": ["SFO"],
         "destinations": ["NRT"],
         "interval_hours": 12,
         "notify_pushover": True,
         "created_at": "2025-11-30T09:00:00",
         "last_checked": "2026-01-02T08:00:00",
         "last_results": [{"route": "JFK-LHR", "price": 41000}],
         "notified_keys": ["k1", "k2"],
     }),
    ("partial edit (name only) keeps every unsubmitted field and all metadata",
     case_partial_edit_keeps_unsubmitted_fields,
     {
         "status": 200,
         "name": "renamed",
         "origins": ["JFK"],
         "destinations": ["LHR"],
         "filters": {"airlines": [], "max_points": 40000, "max_taxes": None},
         "enabled": True,
         "created_at": "2025-11-30T09:00:00",
         "last_checked": "2026-01-02T08:00:00",
         "last_results": [{"route": "JFK-LHR", "price": 41000}],
         "notified_keys": ["k1", "k2"],
     }),
    ("edit of an unknown schedule -> 404 with the error shape, not a 500",
     case_edit_unknown_schedule_404,
     {"status": 404, "detail": {"error": "schedule not found", "sched_id": "nope"}}),
    ("empty edit body leaves the record unchanged and metadata intact",
     case_empty_body_preserves_everything,
     {
         "status": 200,
         "name": "old name",
         "origins": ["JFK"],
         "created_at": "2025-11-30T09:00:00",
         "last_results": [{"route": "JFK-LHR", "price": 41000}],
         "notified_keys": ["k1", "k2"],
     }),
    ("existing record without metadata keys still edits cleanly (no crash)",
     case_record_without_metadata,
     {
         "status": 200,
         "name": "bare",
         "origins": ["LAX"],
         "created_at": None,
         "notified_keys": [],
     }),
    ("edit of a record lacking metadata keys still stores all four metadata "
     "keys (created_at/last_checked/last_results/notified_keys) after saving",
     case_edit_normalizes_missing_metadata_keys,
     {
         "status": 200,
         "has_created_at": True,
         "has_last_checked": True,
         "has_last_results": True,
         "has_notified_keys": True,
         "created_at": None,
         "last_checked": None,
         "last_results": None,
         "notified_keys": [],
     }),
    ("wrong-typed field in the edit body -> 422 validation error, not a 500",
     case_invalid_body_422,
     {"status": 422}),
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
