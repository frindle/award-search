"""Adversarial fixture for: aw-sched-runner-s23-always-calls-upsert-sche

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


# --- stub the sibling modules BEFORE exec'ing the target -------------------
# The target does `from .alert_filters import ...` etc. Those siblings are not
# part of this slice; stub them so the module loads in isolation, and make
# scheduled_searches.upsert_schedule a RECORDER so each case can assert it was
# called (with what) before run_schedule returned its hits.

def _mod(name):
    # The target uses RELATIVE imports (`from .alert_filters import ...`), so
    # it must be loaded as a member of the `src` package: register a fake
    # parent package and every stub under the dotted name, or exec_module
    # raises "attempted relative import with no known parent package".
    m = types.ModuleType("src." + name)
    sys.modules["src." + name] = m
    return m


if "src" not in sys.modules:
    pkg = types.ModuleType("src")
    pkg.__path__ = ["src"]
    sys.modules["src"] = pkg

alert_filters = _mod("alert_filters")
alert_filters.passes_filters = lambda candidate, filters: True

deeplinks = _mod("deeplinks")
deeplinks.seats_aero_url = lambda o, d, date, cabin: "https://seats.example/book"

pushover = _mod("pushover")
_pushover_state = {"raise": False}
def send_award_notification(*a, **kw):
    if _pushover_state["raise"]:
        raise RuntimeError("pushover down")
pushover.send_award_notification = send_award_notification

seats_aero = _mod("seats_aero")
class SeatsAeroClient:  # pragma: no cover -- replaced per case via fake client
    def __init__(self, *a, **kw):
        raise AssertionError("real client must not be used in the fixture")
seats_aero.SeatsAeroClient = SeatsAeroClient

scheduled_searches = _mod("scheduled_searches")
_upsert_calls = []
def upsert_schedule(sched):
    _upsert_calls.append(dict(sched))
    return sched
scheduled_searches.upsert_schedule = upsert_schedule
scheduled_searches.effective_programs = lambda *a, **kw: None
scheduled_searches.is_due = lambda *a, **kw: True
scheduled_searches.load_schedules = lambda *a, **kw: {}
scheduled_searches.query_legs = lambda *a, **kw: []


spec = importlib.util.spec_from_file_location("src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure. The dotted name is also
# what makes the target's relative imports resolve against our stubs.
sys.modules["src.scheduled_runner"] = target
spec.loader.exec_module(target)


class FakeClient:
    def __init__(self, hits):
        self.hits = hits

    def search(self, origin, destination, start_date=None, end_date=None,
               cabins=None, programs=None):
        return list(self.hits)


def _reset():
    del _upsert_calls[:]
    _pushover_state["raise"] = False


HIT = {"program": "AA", "origin": "JFK", "destination": "LHR",
       "date": "2026-10-01", "cabin": "business"}


def case_hits_persisted():
    """Happy path: hits returned AND upsert_schedule(sched) called exactly once,
    with the same sched object (mutated state included)."""
    _reset()
    sched = {"origin": "JFK", "destination": "LHR", "notified_keys": []}
    client = FakeClient([dict(HIT)])
    out = target.run_schedule(sched, client=client)
    assert out == [HIT], "run_schedule must still return the hits"
    assert len(_upsert_calls) == 1, \
        "upsert_schedule not called exactly once (got {})".format(len(_upsert_calls))
    assert _upsert_calls[0] is sched or _upsert_calls[0] == sched, \
        "upsert_schedule must be called with the sched dict"
    return True


def case_zero_hits_still_persisted():
    """Boundary: an empty result set still counts as a checked cycle -- the
    schedule's last_checked/last_hit_count bookkeeping must be persisted too.
    A plausible wrong fix (only upsert when hits) fails this."""
    _reset()
    sched = {"origin": "JFK", "destination": "LHR"}
    out = target.run_schedule(sched, client=FakeClient([]))
    assert out == [], "empty search must return []"
    assert len(_upsert_calls) == 1, \
        "upsert_schedule must be called even with zero hits (got {})".format(len(_upsert_calls))
    assert _upsert_calls[0].get("last_hit_count") == 0, \
        "persisted sched must carry last_hit_count=0"
    return True


def case_notify_failure_still_persisted():
    """Failure path: a pushover outage must not skip the upsert -- the cycle's
    state (notified_keys, last_checked) is exactly what would be lost."""
    _reset()
    _pushover_state["raise"] = True
    sched = {"origin": "JFK", "destination": "LHR"}
    out = target.run_schedule(sched, client=FakeClient([dict(HIT)]))
    assert out == [HIT], "hits must still be returned when notify raises"
    assert len(_upsert_calls) == 1, \
        "upsert_schedule must run even if notification raised (got {})".format(len(_upsert_calls))
    return True


def case_persisted_state_shape():
    """Regression half: the bookkeeping fields that upsert persists keep their
    exact shape -- notified_keys capped/sorted, last_hit_count set."""
    _reset()
    sched = {"origin": "JFK", "destination": "LHR",
             "notified_keys": ["AA|JFK|LHR|2026-10-01|business"]}
    out = target.run_schedule(sched, client=FakeClient([dict(HIT)]))
    assert len(_upsert_calls) == 1
    persisted = _upsert_calls[0]
    key = "AA|JFK|LHR|2026-10-01|business"
    assert persisted.get("notified_keys") == [key], \
        "persisted notified_keys wrong: {!r}".format(persisted.get("notified_keys"))
    assert persisted.get("last_hit_count") == 1, \
        "persisted last_hit_count wrong: {!r}".format(persisted.get("last_hit_count"))
    assert isinstance(persisted.get("last_checked"), str) and persisted["last_checked"], \
        "persisted sched must carry a last_checked timestamp"
    return True


# Model-drafted; NOT yet read by a human.
DRAFT_UNCONFIRMED = True

CASES = [
    ("hits returned AND upsert_schedule(sched) called once", case_hits_persisted, True),
    ("zero hits still persist the schedule (boundary)", case_zero_hits_still_persisted, True),
    ("notify failure does not skip the upsert (failure path)", case_notify_failure_still_persisted, True),
    ("persisted state keeps its shape (regression)", case_persisted_state_shape, True),
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
