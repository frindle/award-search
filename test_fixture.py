"""Adversarial fixture for: aw-sched-routes-s12-upserts-then-redirectres

INTEGRATION fixture: drives the real router through fastapi's TestClient and
asserts status codes, redirect Location headers, AND the SCHEDULES records the
route upserted. The target imports two sibling modules (scheduled_runner,
transfer_partners) that are not part of this slice, so they are stubbed in
sys.modules before the module is loaded -- the route under test does not touch
them.

Each case: (description, callable_returning_actual, expected)
"""
import importlib.util
import sys
import types

# --- load the target with its missing siblings stubbed ----------------------
# The target does relative imports of two sibling modules (scheduled_runner,
# transfer_partners) that are not part of this slice. Write minimal stub files
# next to it so the package resolves normally, then import through the real
# package machinery; clean the stubs up afterwards.
import os  # noqa: E402

sys.path.insert(0, os.getcwd())
_stub_runner = 'src/scheduled_runner.py'
_stub_partners = 'src/transfer_partners.py'
_created = []
try:
    if not os.path.exists(_stub_runner):
        with open(_stub_runner, "w") as f:
            f.write("def run_schedule(**kw):\n    return {'ran': kw}\n")
        _created.append(_stub_runner)
    if not os.path.exists(_stub_partners):
        with open(_stub_partners, "w") as f:
            f.write("def list_partners():\n    return []\n")
        _created.append(_stub_partners)

    import src.webui.scheduled_routes as target  # noqa: E402
except Exception:
    for path in _created:
        os.unlink(path)
    raise

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.router)
client = TestClient(app, follow_redirects=False)


def _reset():
    target.SCHEDULES.clear()


def _save(form):
    """POST the form to /scheduled/save; return (status, location)."""
    r = client.post("/api/scheduled/scheduled/save", data=form)
    return r.status_code, r.headers.get("location")


FULL_FORM = {
    "sched_id": "",
    "name": "Bay Area to Tokyo, spring",
    "origins": "QBA, LAX",
    "destinations": "TYO, ASA",
    "range_start": ["2026-04-01", "2026-05-01"],
    "range_end": ["2026-04-30", ""],
    "cabins": ["business", "first"],
    "programs": ["united"],
    "transfer_partners": ["partnerA"],
    "airlines": "NH, UA",
    "max_points": "100000",
    "max_taxes": "11.5",
    "interval_hours": "12",
    "notify_pushover": "true",
    "enabled": "true",
}


def case_new_schedule():
    _reset()
    status, location = _save(FULL_FORM)
    records = list(target.SCHEDULES.values())
    assert len(records) == 1, "expected exactly one upserted record"
    rec = records[0]
    return (
        status,
        location,
        isinstance(rec["id"], str) and len(rec["id"]) > 0,
        rec["name"],
        rec["origins"],
        rec["destinations"],
        rec["date_ranges"],
        rec["cabins"],
        rec["programs"],
        rec["transfer_partners"],
        rec["filters"],
        rec["interval_hours"],
        rec["notify_pushover"],
        rec["enabled"],
        (rec.get("created_at"), rec.get("last_checked"), rec.get("last_results")),
        rec.get("notified_keys"),
    )


def case_edit_preserves():
    _reset()
    target.SCHEDULES["s1"] = {
        "id": "s1",
        "name": "old name",
        "origins": ["QBA"],
        "destinations": [],
        "date_ranges": [],
        "cabins": [],
        "programs": [],
        "transfer_partners": [],
        "filters": {"airlines": [], "max_points": None, "max_taxes": None},
        "interval_hours": 6,
        "notify_pushover": False,
        "enabled": True,
        "created_at": "2026-01-01T00:00:00Z",
        "last_checked": "2026-02-02T00:00:00Z",
        "last_results": [{"program": "united"}],
        "notified_keys": ["k1"],
    }
    status, location = _save({
        "sched_id": "s1",
        "name": "renamed",
        "origins": "SFO",
        "destinations": "",
        "range_start": [],
        "range_end": [],
        "cabins": ["economy"],
        "programs": [],
        "transfer_partners": [],
        "airlines": "",
        "max_points": "",
        "max_taxes": "",
        "interval_hours": "24",
        "enabled": "true",
    })
    rec = target.SCHEDULES.get("s1")
    return (
        status,
        location,
        len(target.SCHEDULES),  # no new record created on edit
        rec["name"],
        rec["origins"],
        rec["cabins"],
        rec["interval_hours"],
        rec["notify_pushover"],
        rec["created_at"],
        rec["last_checked"],
        rec["last_results"],
        rec["notified_keys"],
    )


def case_create_run_state_keys_present():
    # Deleting the loop that seeds created_at/last_checked/last_results on a
    # CREATE leaves those keys ABSENT from the record. rec.get() would still
    # return None for absent keys, so assert key PRESENCE explicitly -- an
    # implementation that skips seeding must fail here.
    _reset()
    status, location = _save(FULL_FORM)
    rec = list(target.SCHEDULES.values())[0]
    return (
        status,
        location,
        tuple(k in rec for k in ("created_at", "last_checked", "last_results")),
        (rec["created_at"], rec["last_checked"], rec["last_results"]),
        "notified_keys" in rec and rec["notified_keys"] == [],
    )


def case_invalid_values():
    _reset()
    status, location = _save({
        "sched_id": "",
        "name": "bad caps",
        "origins": "",
        "destinations": "",
        "range_start": [],
        "range_end": [],
        "cabins": [],
        "programs": [],
        "transfer_partners": [],
        "airlines": "",
        "max_points": "abc",   # invalid cap -> None, NOT a 500
        "max_taxes": "xyz",   # invalid cap -> None, NOT a 500
        "interval_hours": "soon",  # invalid interval -> default 6
    })
    rec = list(target.SCHEDULES.values())[0]
    return (status, location, rec["filters"]["max_points"],
            rec["filters"]["max_taxes"], rec["interval_hours"])


def case_unchecked_and_empty():
    _reset()
    status, location = _save({
        "sched_id": "",
        "name": "minimal",
        # no origins/destinations/cabins/programs/partners fields at all,
        # and NO notify_pushover / enabled checkboxes (unchecked in the form)
    })
    rec = list(target.SCHEDULES.values())[0]
    return (
        status,
        location,
        rec["name"],
        rec["origins"],
        rec["destinations"],
        rec["cabins"],
        rec["programs"],
        rec["transfer_partners"],
        rec["filters"],
        rec["interval_hours"],
        rec["notify_pushover"],
        rec["enabled"],
    )



CASES = [
    ("new schedule: 303 to /scheduled?saved=1 and full record upserted",
     case_new_schedule,
     (303, "/scheduled?saved=1", True, "Bay Area to Tokyo, spring",
      ["QBA", "LAX"], ["TYO", "ASA"],
      [{"start": "2026-04-01", "end": "2026-04-30"}, {"start": "2026-05-01", "end": None}],
      ["business", "first"], ["united"], ["partnerA"],
      {"airlines": ["NH", "UA"], "max_points": 100000, "max_taxes": 11.5},
      12, True, True, (None, None, None), [])),
    ("edit existing: 303, record updated in place, run-state keys preserved",
     case_edit_preserves,
     (303, "/scheduled?saved=1", 1, "renamed", ["SFO"], ["economy"], 24, False,
      "2026-01-01T00:00:00Z", "2026-02-02T00:00:00Z", [{"program": "united"}], ["k1"])),
    ("create seeds created_at/last_checked/last_results keys as None (present, not absent)",
     case_create_run_state_keys_present,
     (303, "/scheduled?saved=1", (True, True, True), (None, None, None), True)),
    ("invalid caps/interval: still 303 (not a 5xx), bad values coerced to defaults",
     case_invalid_values,
     (303, "/scheduled?saved=1", None, None, 6)),
    ("unchecked checkboxes and empty fields: 303 with falsy/empty record fields",
     case_unchecked_and_empty,
     (303, "/scheduled?saved=1", "minimal", [], [], [], [], [],
      {"airlines": [], "max_points": None, "max_taxes": None}, 6, False, False)),
]


def main():
    if len(CASES) < 3:
        print("  SCAFFOLD_INCOMPLETE: {} adversarial case(s) authored, need >= 3."
              .format(len(CASES)))
        print("  A generated scaffold is not a verify. Author the cases in "
              "test_fixture.py.")
        return 1
    try:
        return _run_cases()
    finally:
        # remove any stub sibling modules we created for this run
        for path in _created:
            if os.path.exists(path):
                os.unlink(path)


def _run_cases():
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
