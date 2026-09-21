"""Adversarial fixture for: aw-sched-runner-s16-against-the-full-filters

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


# --- load src/scheduled_runner.py as part of a synthetic package ------------
# The target uses relative imports (.alert_filters etc.), which cannot resolve
# when the file is loaded bare. Register stub sibling modules under a fake
# package so exec_module succeeds, then patch target.get_trip per case.

def _passes_filters(candidate, filters):
    """Deterministic stand-in: every non-None filter key must match; max_taxes
    bounds candidate['taxes'] (inclusive)."""
    for k, v in (filters or {}).items():
        if v is None:
            continue
        val = (candidate or {}).get(k)
        if val is None and k != "max_taxes":
            continue  # unset candidate fields are wildcards; max_taxes still bounds
        if k == "max_taxes":
            if val is None or val > v:
                return False
        elif val != v:
            return False
    return True


pkg = types.ModuleType("srcpkg")
pkg.__path__ = []
sys.modules["srcpkg"] = pkg

def _stub(name, **attrs):
    m = types.ModuleType("srcpkg." + name)
    for k, v in attrs.items():
        setattr(m, k, v)
    sys.modules[m.__name__] = m

_stub("alert_filters", passes_filters=_passes_filters)
_stub("deeplinks", seats_aero_url=lambda *a: None)
_stub("pushover", send_award_notification=lambda *a: None)
_stub("seats_aero", SeatsAeroClient=object)
_stub("scheduled_searches", effective_programs=None, is_due=None,
      load_schedules=None, query_legs=None, upsert_schedule=None)

spec = importlib.util.spec_from_file_location(
    "srcpkg.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["srcpkg.scheduled_runner"] = target
spec.loader.exec_module(target)


class _Trip:
    def __init__(self, total_taxes):
        self.total_taxes = total_taxes


def _case_kept_under_max():
    """Happy path: trip taxes under max_taxes -> kept, r['taxes'] set."""
    target.get_trip = lambda aid: _Trip(50.0)
    alert = {"filters": {"max_taxes": 100, "cabin": "business"}}
    r = {"availability_id": "a1", "cabin": "business"}
    got = target.select_results(alert, [r])
    return (got == [{"availability_id": "a1", "cabin": "business",
                     "taxes": 50.0}] and r.get("taxes") == 50.0)


def _case_boundary_equal_max():
    """Boundary: trip taxes EXACTLY max_taxes -> still kept (inclusive)."""
    target.get_trip = lambda aid: _Trip(100.0)
    alert = {"filters": {"max_taxes": 100, "cabin": "business"}}
    r = {"availability_id": "a2", "cabin": "business"}
    got = target.select_results(alert, [r])
    return (got == [{"availability_id": "a2", "cabin": "business",
                     "taxes": 100.0}] and r.get("taxes") == 100.0)


def _case_over_max_dropped():
    """Trip taxes over max_taxes -> NOT kept, taxes left None (fail closed)."""
    target.get_trip = lambda aid: _Trip(150.0)
    alert = {"filters": {"max_taxes": 100, "cabin": "business"}}
    r = {"availability_id": "a3", "cabin": "business"}
    got = target.select_results(alert, [r])
    return (got == [] and r.get("taxes") is None)


def _case_trip_none_dropped():
    """get_trip returns None -> NOT kept even though first pass passes."""
    target.get_trip = lambda aid: None
    alert = {"filters": {"max_taxes": 100, "cabin": "business"}}
    r = {"availability_id": "a4", "cabin": "business"}
    got = target.select_results(alert, [r])
    return (got == [] and r.get("taxes") is None)


def _case_trip_raises_dropped():
    """get_trip raises -> NOT kept, no exception escapes select_results."""
    def boom(aid):
        raise RuntimeError("upstream 500")
    target.get_trip = boom
    alert = {"filters": {"max_taxes": 100, "cabin": "business"}}
    r = {"availability_id": "a5", "cabin": "business"}
    got = target.select_results(alert, [r])
    return (got == [] and r.get("taxes") is None)


def _case_first_pass_fail_no_get_trip():
    """First-pass failure -> dropped WITHOUT calling get_trip at all."""
    calls = []
    def spy(aid):
        calls.append(aid)
        return _Trip(10.0)
    target.get_trip = spy
    alert = {"filters": {"max_taxes": 100, "cabin": "business"}}
    r = {"availability_id": "a6", "cabin": "economy"}  # fails first pass
    got = target.select_results(alert, [r])
    return (got == [] and calls == [])


def _case_no_max_taxes_still_fetches():
    """No max_taxes in filters -> trip still fetched, taxes set, kept."""
    target.get_trip = lambda aid: _Trip(42.0)
    alert = {"filters": {"cabin": "business"}}
    r = {"availability_id": "a7", "cabin": "business"}
    got = target.select_results(alert, [r])
    return (got == [{"availability_id": "a7", "cabin": "business",
                     "taxes": 42.0}] and r.get("taxes") == 42.0)


CASES = [
    ("trip taxes under max_taxes -> kept with r['taxes'] set", _case_kept_under_max, True),
    ("boundary: trip taxes exactly max_taxes -> kept (inclusive)", _case_boundary_equal_max, True),
    ("trip taxes over max_taxes -> dropped, taxes left None", _case_over_max_dropped, True),
    ("get_trip returns None -> dropped even if first pass passes", _case_trip_none_dropped, True),
    ("get_trip raises -> dropped, no exception escapes", _case_trip_raises_dropped, True),
    ("first-pass failure -> dropped without calling get_trip", _case_first_pass_fail_no_get_trip, True),
    ("no max_taxes in filters -> trip still fetched and taxes set", _case_no_max_taxes_still_fetches, True),
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
