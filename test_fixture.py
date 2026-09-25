"""Adversarial fixture for: aw-sched-routes-s13-post-scheduled-sched-id

INTEGRATION fixture: drives the real FastAPI router from
src/webui/scheduled_routes.py through fastapi.testclient.TestClient and asserts
status codes AND response bodies/headers.

The target module does relative imports of sibling modules that are not part of
this slice (scheduled_runner, transfer_partners), so we register lightweight
stubs for those two in sys.modules before importing the package -- everything
else is the real code under test.

Each case: (description, callable_returning_actual, expected)
"""
import importlib
import pathlib
import sys
import types

# --- load the target module inside its real package context -----------------
ROOT = pathlib.Path(".")


def _make_pkg(name, path):
    m = types.ModuleType(name)
    m.__path__ = [str(path)]
    sys.modules[name] = m
    return m


_make_pkg("src", ROOT / "src")
_make_pkg("src.webui", ROOT / "src" / "webui")

# Stub ONLY the two sibling modules this slice does not own.
_runner = types.ModuleType("src.scheduled_runner")
_runner.run_schedule = lambda **kw: {"stub": True}
sys.modules["src.scheduled_runner"] = _runner

_partners = types.ModuleType("src.transfer_partners")
_partners.list_partners = lambda: []
sys.modules["src.transfer_partners"] = _partners

target = importlib.import_module("src.webui.scheduled_routes")


# --- build the real app around the real router ------------------------------
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()
app.include_router(target.router)
client = TestClient(app, follow_redirects=False)


def _seed(sched_id):
    target.SCHEDULES[sched_id] = {
        "id": sched_id,
        "name": "demo",
        "origins": ["JFK"],
        "destinations": ["LAX"],
        "date_ranges": [],
        "cabins": ["business"],
        "programs": [],
        "transfer_partners": [],
        "filters": {"airlines": [], "max_points": None, "max_taxes": None},
        "interval_hours": 6,
        "notify_pushover": False,
        "enabled": True,
    }


def _delete(sched_id):
    r = client.post("/api/scheduled/{}/delete".format(sched_id))
    return (r.status_code, r.headers.get("location"))



CASES = [
    ("deleting a known schedule 303-redirects to /scheduled",
     lambda: (_seed("sched-1"), _delete("sched-1"))[1],
     (303, "/scheduled")),

    ("after delete the schedule is actually gone from SCHEDULES",
     lambda: (_seed("sched-2"), _delete("sched-2"), "sched-2" not in target.SCHEDULES)[2],
     True),

    ("deleting an unknown sched_id is a 404 with the schedule-not-found body, not a 500",
     lambda: (lambda r: (r.status_code, r.json()["detail"]["error"], r.json()["detail"]["sched_id"]))(
         client.post("/api/scheduled/does-not-exist/delete")),
     (404, "schedule not found", "does-not-exist")),

    ("deleting twice: second delete of the same id is a 404 (idempotency boundary)",
     lambda: (_seed("sched-3"), _delete("sched-3"), _delete("sched-3"))[2],
     (404, None)),

    ("regression: GET /api/scheduled/templates still works after the new route lands",
     lambda: (lambda r: (r.status_code, r.json()))(client.get("/api/scheduled/templates")),
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
