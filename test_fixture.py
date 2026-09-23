"""Adversarial fixture for: aw-sched-runner-s21-always-sets-sched-last-c

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
import importlib.util
import sys
import types
from datetime import datetime


# --- load src/scheduled_runner.py with its relative siblings stubbed --------
# The module does `from .alert_filters import ...` etc., so it must be loaded
# as a member of a package. Register a fake package plus inert stand-ins for
# every sibling symbol the target imports, then exec the real file under that
# name. run_schedule's own logic (search -> notify -> bookkeeping) is what we
# test; the stubs only exist so the import succeeds and so we can record
# notification calls.

def _stub(name, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


pkg = types.ModuleType("srcpkg")
pkg.__path__ = []
sys.modules["srcpkg"] = pkg

NOTIFY_CALLS = []


def _record_notify(*a, **k):
    NOTIFY_CALLS.append((a, k))


_stub("srcpkg.alert_filters", passes_filters=lambda c, f: True)
_stub("srcpkg.deeplinks", seats_aero_url=lambda *a, **k: "https://seats.aero/x")
_stub("srcpkg.pushover", send_award_notification=_record_notify)
_stub("srcpkg.seats_aero", SeatsAeroClient=type("SeatsAeroClient", (), {}))
_stub("srcpkg.scheduled_searches",
      effective_programs=lambda *a, **k: [],
      is_due=lambda *a, **k: True,
      load_schedules=lambda *a, **k: {},
      query_legs=lambda *a, **k: [],
      upsert_schedule=lambda *a, **k: None)

spec = importlib.util.spec_from_file_location("srcpkg.scheduled_runner", "src/scheduled_runner.py")
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC so the module has a sys.modules entry under its real name.
sys.modules["srcpkg.scheduled_runner"] = target
spec.loader.exec_module(target)


HITS = [
    {"availability_id": 1, "origin": "JFK", "destination": "LHR", "cost": 5000},
    {"availability_id": 2, "origin": "JFK", "destination": "LHR", "cost": 6000},
]


class FakeClient:
    def __init__(self, hits=None):
        self.hits = list(hits or [])

    def search(self, *a, **k):
        return list(self.hits)


def _fresh_sched():
    return {"origin": "JFK", "destination": "LHR"}


def _ts_ok(value):
    """last_checked must be a real ISO-8601 timestamp taken at run time."""
    if not isinstance(value, str):
        return False
    try:
        then = datetime.fromisoformat(value)
    except ValueError:
        return False
    return abs((datetime.now() - then).total_seconds()) < 300


def case_hits():
    """Two hits: bookkeeping set AND the hits are still returned."""
    sched = _fresh_sched()
    got = target.run_schedule(sched, client=FakeClient(HITS), notify=False)
    return (
        got == HITS,
        sched.get("last_results") == HITS,
        sched.get("last_hit_count") == 2,
        _ts_ok(sched.get("last_checked")),
    )


def case_zero_hits():
    """ALWAYS: with zero hits the keys are still set (empty list, count 0)."""
    sched = _fresh_sched()
    got = target.run_schedule(sched, client=FakeClient([]), notify=False)
    return (
        got == [],
        sched.get("last_results") == [],
        sched.get("last_hit_count") == 0,
        _ts_ok(sched.get("last_checked")),
    )


def case_notify_regression():
    """Regression half: notifications still fire per hit when notify=True,
    and stay silent when notify=False."""
    NOTIFY_CALLS.clear()
    sched = _fresh_sched()
    target.run_schedule(sched, client=FakeClient(HITS), notify=True)
    with_hits = len(NOTIFY_CALLS)

    NOTIFY_CALLS.clear()
    sched2 = _fresh_sched()
    target.run_schedule(sched2, client=FakeClient(HITS), notify=False)
    without_hits = len(NOTIFY_CALLS)

    return (with_hits == 2, without_hits == 0)


def case_last_checked_is_now():
    """last_checked must be a fresh timestamp, not a static/None value."""
    sched = _fresh_sched()
    target.run_schedule(sched, client=FakeClient(HITS), notify=False)
    return _ts_ok(sched.get("last_checked"))



CASES = [
    ("two hits: returned and recorded (results/count/timestamp)", case_hits,
     (True, True, True, True)),
    ("zero hits: keys still set with empty list and count 0", case_zero_hits,
     (True, True, True, True)),
    ("notify=True fires per hit; notify=False stays silent", case_notify_regression,
     (True, True)),
    ("last_checked is a fresh ISO timestamp", case_last_checked_is_now, True),
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
