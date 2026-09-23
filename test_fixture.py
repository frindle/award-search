"""Adversarial fixture for: aw-sched-runner-s18-notify-hit

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

# The target uses relative imports (`from .pushover import ...`). Loaded as a
# bare module it has no parent package, so pre-register lightweight stubs under
# a fake package name and point the target's __package__ at it. pushover is the
# real dependency under test: instead of hitting Pushover we RECORD every call
# (bound to parameter names) so the fixture can assert exact values.
_PARAM_NAMES = ("origin", "destination", "date", "program",
                "miles", "cabin", "seats", "booking_url")
_records = []


def _record(*args, **kwargs):
    bound = dict(zip(_PARAM_NAMES, args))
    for k, v in kwargs.items():
        bound[k] = v
    _records.append(bound)
    return True


def _stub(name, **attrs):
    mod = types.ModuleType("stub." + name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules["stub." + name] = mod


_stub("pushover", send_award_notification=_record)
_stub("alert_filters", passes_filters=lambda *a, **k: True)
_stub("deeplinks", seats_aero_url=lambda *a, **k: "url")
_stub("seats_aero", SeatsAeroClient=object)
_stub("scheduled_searches", effective_programs=None, is_due=None,
      load_schedules=None, query_legs=None, upsert_schedule=None)

spec = importlib.util.spec_from_file_location("target", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["target"] = target
# Resolve the target's relative imports against the stub package above.
target.__package__ = "stub"
spec.loader.exec_module(target)


def _call(sched, r):
    del _records[:]
    target.notify_hit(sched, r)
    return list(_records)


SCHED = {"origin": "JFK", "destination": "LHR", "date": "2026-05-01"}

# Decoy keys a plausible-but-wrong impl would read instead: program/miles from
# the wrong field, origin/destination from r instead of sched.
R_DECOY = {
    "source": "AA", "cost": 45000, "cabin": "business", "seats": 3,
    "booking_url": "https://book.example/aa",
    "program": "DECOY", "miles": 999,
    "origin": "XXX", "destination": "YYY",
}

EXPECTED_DECOY = {
    "origin": "JFK", "destination": "LHR", "date": "2026-05-01",
    "program": "AA", "miles": 45000, "cabin": "business", "seats": 3,
    "booking_url": "https://book.example/aa",
}

EXPECTED_EMPTY = {k: None for k in _PARAM_NAMES}


CASES = [
    ("sends exactly one notification with sched origin/destination/date and "
     "r source/cost/cabin/seats/booking_url (ignoring decoy program/miles/"
     "origin/destination keys)",
     lambda: _call(SCHED, R_DECOY),
     [EXPECTED_DECOY]),

    ("program comes from r['source'] and miles from r['cost'], not the "
     "decoy fields",
     lambda: (lambda recs: (recs[0]["program"], recs[0]["miles"]))(
         _call({"origin": "SFO"}, {"source": "UA", "cost": 12000,
                                   "cabin": "economy", "seats": 1,
                                   "booking_url": None,
                                   "program": "WRONG", "miles": 777})),
     ("UA", 12000)),

    ("empty sched and r do not raise; one call with all-None values",
     lambda: _call({}, {}),
     [EXPECTED_EMPTY]),

    ("notify_hit returns None (it notifies, it does not report)",
     lambda: target.notify_hit(SCHED, R_DECOY) is None,
     True),
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
