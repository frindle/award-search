"""Adversarial fixture for: aw-sched-runner-s24-schedule-scheduler

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
import asyncio
import importlib.util
import inspect
import sys
import types

# The target module does relative imports of sibling modules that are not part
# of this slice's contract (and one, scheduled_searches, is not present in the
# worktree yet). Stub every sibling so the module loads hermetically; none of
# them affect what THIS slice asserts.
def _stub(name):
    mod = types.ModuleType("src." + name)
    sys.modules["src." + name] = mod
    return mod

pkg = types.ModuleType("src")
pkg.__path__ = []
sys.modules.setdefault("src", pkg)
_stub("alert_filters").passes_filters = lambda *a, **k: True
_stub("deeplinks").seats_aero_url = lambda *a, **k: ""
_pushover = _stub("pushover"); _pushover.send_award_notification = lambda *a, **k: None
_sa = _stub("seats_aero")
class _Client:  # placeholder; never instantiated by the cases below
    def __init__(self, *a, **k): raise AssertionError("client should not be built")
_sa.SeatsAeroClient = _Client
_ss = _stub("scheduled_searches")
for fn in ("effective_programs", "is_due", "load_schedules", "query_legs", "upsert_schedule"):
    setattr(_ss, fn, lambda *a, **k: None)

spec = importlib.util.spec_from_file_location("src.scheduled_runner", 'src/scheduled_runner.py')
target = importlib.util.module_from_spec(spec)
# REGISTER BEFORE EXEC. Not optional: a module loaded this way has no entry in
# sys.modules, so sys.modules[cls.__module__] is None -- and on Python 3.14 (the
# Studio worker) dataclasses resolves string annotations through exactly that
# lookup. A target with `from __future__ import annotations` + @dataclass then
# dies at IMPORT with AttributeError: 'NoneType' object has no attribute
# '__dict__', so the fixture fails for a reason that has nothing to do with
# the task and the dispatch reads as a model failure.
sys.modules["src.scheduled_runner"] = target
spec.loader.exec_module(target)


def _sig():
    return inspect.signature(getattr(target, "schedule_scheduler"))


def _last_hit_count(results):
    s = {"origin": "SFO", "destination": "LHR"}
    target.run_schedule(s, client=types.SimpleNamespace(search=lambda *a, **k: results), notify=False)
    return s["last_hit_count"]



CASES = [
    # --- the contract: a real coroutine function ---------------------------
    ("is an async def (inspect.iscoroutinefunction)",
     lambda: inspect.iscoroutinefunction(getattr(target, "schedule_scheduler")),
     True),

    ("single parameter named poll_minutes",
     lambda: list(_sig().parameters.keys()),
     ["poll_minutes"]),

    ("poll_minutes defaults to None",
     lambda: _sig().parameters["poll_minutes"].default,
     None),

    # --- awaitable without hanging (body must be minimal/non-blocking) -----
    ("awaiting with no args returns promptly and yields None",
     lambda: asyncio.run(asyncio.wait_for(target.schedule_scheduler(), timeout=5)),
     None),

    ("awaiting poll_minutes=0.25 explicitly returns promptly and yields None",
     lambda: asyncio.run(asyncio.wait_for(target.schedule_scheduler(poll_minutes=0.25), timeout=5)),
     None),

    # --- regression half: earlier slices' landed work must survive ---------
    ("run_schedule still runs a schedule with a fake client (notify off)",
     lambda: target.run_schedule(
         {"origin": "SFO", "destination": "LHR"},
         client=types.SimpleNamespace(search=lambda *a, **k: [{"availability_id": 1}]),
         notify=False),
     [{"availability_id": 1}]),

    ("run_schedule records last_hit_count == 1 on the schedule dict",
     lambda: _last_hit_count([{"program": "AA", "origin": "SFO", "destination": "LHR",
                               "date": "2026-01-01", "cabin": "Y"}]),
     1),

    ("run_schedule with an empty result set records last_hit_count == 0",
     lambda: _last_hit_count([]),
     0),
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
