"""Adversarial fixture for: aw-sched-routes-s14-post-scheduled-sched-id

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
"""
import sys
import types
import importlib.util

# The target uses relative imports (`from ..scheduled_runner import ...`) that
# resolve to src.webui.scheduled_runner / src.webui.transfer_partners, which are
# not part of this slice. Register stubs under those names so the module loads;
# none of them is exercised by the toggle route.
for _name in ("src", "src.webui"):
    if _name not in sys.modules:
        _mod = types.ModuleType(_name)
        _mod.__path__ = []
        sys.modules[_name] = _mod

def _stub(name, **attrs):
    """Register a stub module under its dotted name (real one wins if present)."""
    if name in sys.modules:
        return
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[name] = m

_stub("src.webui.scheduled_runner", run_schedule=lambda **kw: {"stub": True})
_stub("src.webui.transfer_partners", list_partners=lambda: [])

spec = importlib.util.spec_from_file_location(
    "src.webui.scheduled_routes", 'src/webui/scheduled_routes.py',
    submodule_search_locations=[])
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


def _make_client():
    app = FastAPI()
    app.include_router(target.router)
    return TestClient(app, raise_server_exceptions=False)


def _seed(schedule):
    target.SCHEDULES.clear()
    target.SCHEDULES.update({k: dict(v) for k, v in schedule.items()})


BASE = {
    "id": "s1",
    "name": "LHR->JFK saver",
    "origins": ["LHR"],
    "destinations": ["JFK"],
    "date_ranges": [{"start": "2026-05-01", "end": "2026-08-31"}],
    "cabins": ["business"],
    "programs": ["MR"],
    "transfer_partners": ["BA"],
    "filters": {"airlines": ["BA"], "max_points": 45000, "max_taxes": None},
    "interval_hours": 6,
    "notify_pushover": True,
    "created_at": "2026-01-02T03:04:05",
    "last_checked": None,
    "last_results": [{"k": "v"}],
    "notified_keys": ["a", "b"],
}


def _post(client, url):
    # Do NOT follow the 303: /scheduled is a page route outside this slice.
    return client.post(url, follow_redirects=False)


def _toggle_enabled_true():
    """Enabled schedule -> disabled; 303 to /scheduled; every other key intact."""
    _seed({"s1": dict(BASE, enabled=True)})
    c = _make_client()
    r = _post(c, "/api/scheduled/s1/toggle")
    rec = target.SCHEDULES.get("s1", {})
    return (r.status_code, r.headers.get("location"),
            rec.get("enabled"), {k: v for k, v in rec.items() if k != "enabled"})


def _toggle_enabled_false():
    """Disabled schedule -> enabled. A fix that hardcodes False fails here."""
    _seed({"s1": dict(BASE, enabled=False)})
    c = _make_client()
    r = _post(c, "api/scheduled/s1/toggle")
    rec = target.SCHEDULES.get("s1", {})
    return (r.status_code, rec.get("enabled"))


def _toggle_missing_enabled_key():
    """Record without an 'enabled' key: default is True, so toggle -> False."""
    _seed({"s1": dict(BASE)})  # BASE carries no 'enabled' key at all
    c = _make_client()
    r = _post(c, "api/scheduled/s1/toggle")
    return (r.status_code, target.SCHEDULES.get("s1", {}).get("enabled"))


def _toggle_unknown_id():
    """Unknown sched_id -> 404 with the exact delete/edit-save error shape."""
    _seed({})
    c = _make_client()
    r = _post(c, "api/scheduled/nope/toggle")
    return (r.status_code, r.json())


def _delete_still_works():
    """Regression: POST /{sched_id}/delete still 303s and removes the record."""
    _seed({"s1": dict(BASE, enabled=True)})
    c = _make_client()
    r = _post(c, "api/scheduled/s1/delete")
    return (r.status_code, r.headers.get("location"), "s1" in target.SCHEDULES)


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    ("enabled schedule toggles to disabled; 303 /scheduled; all other keys preserved",
     _toggle_enabled_true,
     (303, "/scheduled", False, {k: v for k, v in BASE.items() if k != "enabled"})),
    ("disabled schedule toggles back to enabled (no hardcoded False)",
     _toggle_enabled_false, (303, True)),
    ("record missing 'enabled' key defaults to True and flips to False",
     _toggle_missing_enabled_key, (303, False)),
    ("unknown sched_id -> 404 with the standard schedule-not-found shape",
     _toggle_unknown_id,
     (404, {"detail": {"error": "schedule not found", "sched_id": "nope"}})),
    ("regression: delete route still works and removes the record",
     _delete_still_works, (303, "/scheduled", False)),
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
